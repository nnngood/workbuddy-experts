#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""记录单次任务的技能调用轨迹，沉淀为"高频技能 + 典型组合"记忆（零第三方依赖）。

每次任务收尾调用一次；同一任务类型的同一调用链重复出现达到阈值后自动"晋级"为
预置组合，下次同类任务可直接走快速通道。

用法：
  python record_usage.py --task-type "正式方案类文档" --forms word,ppt \
      --skills "formal-doc-dual-delivery,office-preview-qc" --success true \
      --notes "水务项目建议书，客户领导呈报版" --threshold 2

  python record_usage.py --stats          # 只看统计，不记录
  python record_usage.py --forget "正式方案类文档"   # 删除某任务类型的组合记忆
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_skills import DATA_DIR  # noqa: E402

USAGE_FILE = DATA_DIR / "usage_stats.json"
DEFAULT_THRESHOLD = 2


def norm_key(task_type: str) -> str:
    return re.sub(r"\s+", "", (task_type or "未分类")).lower()


def load() -> dict:
    if USAGE_FILE.is_file():
        try:
            data = json.loads(USAGE_FILE.read_text(encoding="utf-8"))
            data.setdefault("records", [])
            data.setdefault("skill_counts", {})
            data.setdefault("cooccurrence", {})
            data.setdefault("combo_library", {})
            return data
        except Exception:  # noqa: BLE001
            pass
    return {"records": [], "skill_counts": {}, "cooccurrence": {}, "combo_library": {}}


def save(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def dedupe(seq) -> list:
    out = []
    for x in seq:
        x = x.strip()
        if x and x not in out:
            out.append(x)
    return out


def similar(a: list, b: list) -> bool:
    """两条调用链是否算同一条：主力技能相同，且成员重合度 >= 0.6。"""
    if not a or not b:
        return False
    if a[0] != b[0]:
        return False
    sa, sb = set(a), set(b)
    return len(sa & sb) / max(1, len(sa | sb)) >= 0.6


def merge_chain(old: list, new: list) -> list:
    """合并两条相似链：保留旧链顺序，把新链里的新成员追加进去。"""
    return dedupe(old + [x for x in new if x not in old])


# --------------------------------------------------------------------------- #
def do_record(args) -> int:
    data = load()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    skills = dedupe(re.split(r"[,\n;，、]+", args.skills or ""))
    forms = dedupe(re.split(r"[,\s、]+", args.forms or ""))
    key = norm_key(args.task_type)
    threshold = args.threshold if args.threshold else DEFAULT_THRESHOLD

    if not skills:
        print("未提供 --skills，无法记录。", file=sys.stderr)
        return 2

    data["records"].append({
        "ts": now, "task_type": args.task_type or "未分类",
        "forms": forms, "skills": skills,
        "success": str(args.success).lower() in ("true", "1", "yes"),
        "notes": args.notes or "",
    })
    data["records"] = data["records"][-500:]  # 只保留最近 500 条，防止无限膨胀

    for s in skills:
        data["skill_counts"][s] = data["skill_counts"].get(s, 0) + 1
    for i, a in enumerate(skills):
        for b in skills[i + 1:]:
            k = "|".join(sorted([a, b]))
            data["cooccurrence"][k] = data["cooccurrence"].get(k, 0) + 1

    # --- 组合库更新 ---
    combos = data["combo_library"].setdefault(key, [])
    hit = next((c for c in combos if similar(c["chain"], skills)), None)
    became_preset = False

    if hit is None:
        combos.append({
            "chain": skills, "count": 1,
            "forms": forms, "first_seen": now, "last_seen": now,
            "promoted": 1 >= threshold,
            "last_task_type": args.task_type or "未分类",
        })
        hit = combos[-1]
        action = "新建组合"
    else:
        hit["chain"] = merge_chain(hit["chain"], skills)
        hit["count"] += 1
        hit["last_seen"] = now
        hit["forms"] = dedupe(hit.get("forms", []) + forms)
        was = hit.get("promoted", False)
        hit["promoted"] = hit["count"] >= threshold
        became_preset = hit["promoted"] and not was
        action = "累加已有组合"

    combos.sort(key=lambda c: (-c.get("count", 0), c.get("first_seen", "")))
    save(data)

    # 同步刷新人读版组合库
    try:
        from combo_report import render_markdown, write_markdown
        write_markdown(data)
    except Exception:  # noqa: BLE001
        pass

    print(f"✅ 已记录：{args.task_type or '未分类'}")
    print(f"   {action} ×{hit['count']}（阈值 {threshold}）")
    print(f"   调用链：{' → '.join(hit['chain'])}")
    if became_preset:
        print(f"   ★ 该组合已晋级为「预置组合」，下次同类任务可走快速通道！")
    print(f"   记忆文件：{USAGE_FILE}")
    return 0


def do_stats(args) -> int:
    data = load()
    try:
        from combo_report import render_markdown
        print(render_markdown(data, top=args.top))
    except Exception:  # noqa: BLE001
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def do_forget(args) -> int:
    data = load()
    key = norm_key(args.forget)
    if key in data["combo_library"]:
        removed = data["combo_library"].pop(key)
        save(data)
        try:
            from combo_report import write_markdown
            write_markdown(data)
        except Exception:  # noqa: BLE001
            pass
        print(f"已删除「{args.forget}」下的 {len(removed)} 条组合记忆。")
    else:
        print(f"组合库中未找到「{args.forget}」。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="记录技能调用轨迹并沉淀典型组合")
    ap.add_argument("--task-type", dest="task_type", default="", help="任务类型（组合库分类键）")
    ap.add_argument("--forms", default="", help="本次交付形态，逗号分隔")
    ap.add_argument("--skills", default="", help="按调用顺序排列的技能名，逗号分隔")
    ap.add_argument("--success", default="true", help="本次是否顺利（true/false）")
    ap.add_argument("--notes", default="", help="备注")
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                    help=f"晋级为预置组合所需重复次数（默认 {DEFAULT_THRESHOLD}）")
    ap.add_argument("--stats", action="store_true", help="打印统计报告，不记录")
    ap.add_argument("--forget", help="删除某任务类型的组合记忆")
    ap.add_argument("--top", type=int, default=10, help="统计报告条数")
    args = ap.parse_args()

    if args.forget:
        return do_forget(args)
    if args.stats:
        return do_stats(args)
    if not args.skills:
        # 无参数时直接给统计，避免误操作
        return do_stats(args)
    return do_record(args)


if __name__ == "__main__":
    sys.exit(main())
