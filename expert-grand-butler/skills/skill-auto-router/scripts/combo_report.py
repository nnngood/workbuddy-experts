#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把调用轨迹统计成「高频技能 + 典型组合」报告，并生成人读版组合库（零第三方依赖）。

用法：
  python combo_report.py            # 打印趋势报告
  python combo_report.py --write    # 打印并写入 data/combo_library.md
  python combo_report.py --top 15
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_skills import DATA_DIR  # noqa: E402

USAGE_FILE = DATA_DIR / "usage_stats.json"
MD_FILE = DATA_DIR / "combo_library.md"


def load() -> dict:
    if USAGE_FILE.is_file():
        try:
            return json.loads(USAGE_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    return {"records": [], "skill_counts": {}, "cooccurrence": {}, "combo_library": {}}


def render_markdown(data: dict, top: int = 10) -> str:
    records = data.get("records", [])
    skill_counts = data.get("skill_counts", {})
    cooc = data.get("cooccurrence", {})
    combos = data.get("combo_library", {})

    all_combos = []
    for key, lst in combos.items():
        for c in lst:
            all_combos.append((key, c))
    preset = [x for x in all_combos if x[1].get("promoted")]
    trial = [x for x in all_combos if not x[1].get("promoted")]
    preset.sort(key=lambda x: -x[1].get("count", 0))
    trial.sort(key=lambda x: -x[1].get("count", 0))

    L = []
    L.append("# 技能调用记忆库（自动生成）")
    L.append("")
    L.append(f"> 更新时间：{datetime.now():%Y-%m-%d %H:%M:%S}　|　"
             f"累计 {len(records)} 次任务记录　|　{len(skill_counts)} 个技能被调用过　|　"
             f"{len(combos)} 个任务类型")
    L.append("")

    L.append("## 一、预置组合（已晋级，同类任务可走快速通道）")
    L.append("")
    if preset:
        for key, c in preset[:top]:
            L.append(f"### {c.get('last_task_type', key)}　×{c['count']}")
            L.append("")
            L.append(f"- 调用链：{' → '.join('`' + s + '`' for s in c['chain'])}")
            if c.get("forms"):
                L.append(f"- 交付形态：{'、'.join(c['forms'])}")
            L.append(f"- 首次：{c.get('first_seen', '—')}　最近：{c.get('last_seen', '—')}")
            L.append("")
    else:
        L.append("_暂无。同一任务类型的调用链重复达到阈值后会自动出现在这里。_")
        L.append("")

    L.append("## 二、试用中的组合（次数未达晋级阈值）")
    L.append("")
    if trial:
        for key, c in trial[:top]:
            L.append(f"- [{c.get('last_task_type', key)} ×{c['count']}] "
                     f"{' → '.join(c['chain'])}")
    else:
        L.append("_暂无。_")
    L.append("")

    L.append(f"## 三、高频技能 Top {min(top, len(skill_counts))}")
    L.append("")
    if skill_counts:
        ranked = sorted(skill_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
        L.append("| 排名 | 技能 | 调用次数 |")
        L.append("|---|---|---|")
        for i, (name, n) in enumerate(ranked, 1):
            L.append(f"| {i} | `{name}` | {n} |")
    else:
        L.append("_暂无记录。_")
    L.append("")

    L.append(f"## 四、强关联技能对 Top {min(top, len(cooc))}")
    L.append("")
    if cooc:
        pairs = sorted(cooc.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
        L.append("| 技能 A | 技能 B | 共同出现次数 |")
        L.append("|---|---|---|")
        for k, n in pairs:
            a, b = k.split("|", 1)
            L.append(f"| `{a}` | `{b}` | {n} |")
    else:
        L.append("_暂无记录。_")
    L.append("")

    L.append("## 五、如何喂养这个记忆库")
    L.append("")
    L.append("每次任务收尾执行一次（`skills` 按实际调用顺序填写）：")
    L.append("")
    L.append("```bash")
    L.append('python scripts/record_usage.py --task-type "任务类型" \\')
    L.append('    --forms word,ppt --skills "技能A,技能B,技能C" --success true')
    L.append("```")
    L.append("")
    L.append("查看统计：`python scripts/record_usage.py --stats`　|　"
             "删除某类记忆：`python scripts/record_usage.py --forget \"任务类型\"`")
    return "\n".join(L)


def write_markdown(data: dict, top: int = 10) -> Path:
    MD_FILE.parent.mkdir(parents=True, exist_ok=True)
    MD_FILE.write_text(render_markdown(data, top=top), encoding="utf-8")
    return MD_FILE


def main() -> int:
    ap = argparse.ArgumentParser(description="生成技能调用记忆报告")
    ap.add_argument("--write", action="store_true", help="写入 data/combo_library.md")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    data = load()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    print(render_markdown(data, top=args.top))
    if args.write:
        p = write_markdown(data, top=args.top)
        print(f"\n已写入：{p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
