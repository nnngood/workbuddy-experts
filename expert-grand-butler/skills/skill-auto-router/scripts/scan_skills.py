#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描本机全量技能库，建立可检索的技能索引（零第三方依赖）。

覆盖五个层级：
  L2 项目级   <cwd>/.workbuddy/skills/*/SKILL.md          （优先级最高）
  L1 用户级   ~/.workbuddy/skills/*/SKILL.md
  L4 连接器级 ~/.workbuddy/connectors/skills/*/SKILL.md
  L3 插件级   ~/.workbuddy/plugins/cache/**/skills/*/SKILL.md
  L5 内置级   <LocalAppData>/Programs/WorkBuddy/.../plugins/**/skills/*/SKILL.md

用法：
  python scan_skills.py                      # 刷新索引并打印统计
  python scan_skills.py --query 表格 --top 8  # 关键字检索
  python scan_skills.py --layer user          # 只统计某一层
  python scan_skills.py --json                # 输出完整 JSON
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
INDEX_FILE = DATA_DIR / "skill_index.json"

LAYER_LABEL = {
    "project": "项目级",
    "user": "用户级",
    "connector": "连接器级",
    "plugin": "插件级",
    "builtin": "内置级",
}
LAYER_PRIORITY = {"project": 5, "user": 4, "connector": 3, "plugin": 2, "builtin": 1}

# 明显不是可用技能目录的路径片段，直接跳过
SKIP_PARTS = ("__pycache__", ".bak", ".backup", "node_modules", "/dist/", "\\.bak")

CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")
WORD = re.compile(r"[a-zA-Z][a-zA-Z0-9\-_.]{1,}")


# --------------------------------------------------------------------------- #
# frontmatter 解析（容错，无需 pyyaml）
# --------------------------------------------------------------------------- #
def parse_frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            end = i
            break
    if end is None:
        return {}

    fm = lines[1:end]
    data: dict = {}
    i = 0
    while i < len(fm):
        raw = fm[i]
        if not raw.strip() or raw.strip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*:\s*(.*)$", raw)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()

        # YAML 块标量  >  |  >-  |-
        if val in (">", "|", ">-", "|-", ">+", "|+"):
            style = val[0]
            i += 1
            block = []
            while i < len(fm) and (not fm[i].strip() or fm[i][:1] in (" ", "\t")):
                block.append(fm[i].strip())
                i += 1
            sep = " " if style == ">" else "\n"
            data[key] = sep.join(x for x in block if x).strip()
            continue

        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("\"", "'"):
            val = val[1:-1]
        data[key] = val
        i += 1
    return data


def first_heading(text: str) -> str:
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return ""


def core_purpose(text: str) -> str:
    """抓取正文里最有信息量的一段（Core Purpose / 核心目的 之后的首段）。"""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if re.match(r"^#{1,3}\s*(Core Purpose|核心目的|核心用途|Overview|概述)\s*$", ln.strip(), re.I):
            buf = []
            for nxt in lines[i + 1: i + 8]:
                if nxt.strip().startswith("#"):
                    break
                if nxt.strip():
                    buf.append(nxt.strip())
            if buf:
                return " ".join(buf)[:400]
    return ""


# --------------------------------------------------------------------------- #
# 分词（中英混合，用于后续匹配打分）
# --------------------------------------------------------------------------- #
def tokenize(text: str) -> list:
    text = (text or "").lower()
    toks = set(WORD.findall(text))
    for run in CJK_RUN.findall(text):
        for n in (2, 3):
            if len(run) >= n:
                for i in range(len(run) - n + 1):
                    toks.add(run[i:i + n])
        if len(run) <= 4:
            toks.add(run)
    return sorted(toks)


# --------------------------------------------------------------------------- #
# 目录扫描
# --------------------------------------------------------------------------- #
def skill_roots(cwd: Path):
    local_app = Path(os.environ.get("LOCALAPPDATA", str(HOME / "AppData" / "Local")))
    return [
        (cwd / ".workbuddy" / "skills", "project", 3),
        (HOME / ".workbuddy" / "skills", "user", 3),
        (HOME / ".workbuddy" / "connectors" / "skills", "connector", 3),
        (HOME / ".workbuddy" / "plugins" / "skills", "plugin", 3),
        (HOME / ".workbuddy" / "plugins" / "cache", "plugin", 8),
        (local_app / "Programs" / "WorkBuddy" / "resources" / "app.asar.unpacked"
         / "resources" / "plugins", "builtin", 8),
    ]


def _skipped(p: Path) -> bool:
    s = str(p).replace("\\", "/")
    return any(part.replace("\\", "/") in s for part in SKIP_PARTS)


def walk_skills(root: Path, layer: str, max_depth: int, seen_dirs: set):
    """在 root 下按深度上限寻找 SKILL.md。"""
    if not root.is_dir():
        return
    root = root.resolve()
    base_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        if _skipped(d):
            dirnames[:] = []
            continue
        if len(d.parts) - base_depth > max_depth:
            dirnames[:] = []
            continue
        # 剪枝：跳过明显无关目录
        dirnames[:] = [x for x in dirnames
                       if x not in ("__pycache__", "node_modules", ".git")
                       and not x.startswith(".bak")]
        if "SKILL.md" in filenames:
            rp = d.resolve()
            if rp in seen_dirs:
                continue
            seen_dirs.add(rp)
            yield rp / "SKILL.md", layer


def load_one(skill_md: Path, layer: str) -> dict:
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return {"error": f"读取失败: {exc}", "path": str(skill_md), "layer": layer}

    fm = parse_frontmatter(text)
    raw_name = fm.get("name") or skill_md.parent.name
    name = raw_name.strip().strip("\"'")
    desc = (fm.get("description") or fm.get("description_zh")
            or fm.get("description_en") or "").strip()
    if not desc:
        desc = core_purpose(text)

    search_text = " ".join(filter(None, [
        name,
        fm.get("display_name", ""),
        fm.get("display_name_en", ""),
        fm.get("category", ""),
        fm.get("tags", ""),
        fm.get("description", ""),
        fm.get("description_zh", ""),
        fm.get("description_en", ""),
        first_heading(text),
        core_purpose(text),
    ]))

    return {
        "name": name,
        "dir": skill_md.parent.name,
        "layer": layer,
        "layer_label": LAYER_LABEL.get(layer, layer),
        "path": str(skill_md),
        "category": str(fm.get("category", "") or "").strip(),
        "display_name": str(fm.get("display_name", "") or "").strip(),
        "description": re.sub(r"\s+", " ", desc)[:900],
        "agent_created": str(fm.get("agent_created", "")).lower() in ("true", "yes", "1"),
        "version": str(fm.get("version", "") or "").strip(),
        "tokens": tokenize(search_text)[:400],
    }


def collect(cwd: Path) -> dict:
    seen_dirs: set = set()
    raw = []
    for root, layer, depth in skill_roots(cwd):
        for skill_md, lyr in walk_skills(root, layer, depth, seen_dirs):
            raw.append(load_one(skill_md, lyr))

    # 按 name 去重，保留优先级最高的层，合并路径
    merged: dict = {}
    errors = [r for r in raw if "error" in r]
    for r in raw:
        if "error" in r:
            continue
        key = r["name"].lower()
        if key not in merged:
            r["alt_paths"] = []
            merged[key] = r
        else:
            cur = merged[key]
            if LAYER_PRIORITY.get(r["layer"], 0) > LAYER_PRIORITY.get(cur["layer"], 0):
                r["alt_paths"] = cur.get("alt_paths", []) + [cur["path"]] + cur.get("alt_paths", [])
                merged[key] = r
            else:
                cur.setdefault("alt_paths", []).append(r["path"])

    skills = sorted(merged.values(), key=lambda x: (-LAYER_PRIORITY.get(x["layer"], 0), x["name"].lower()))

    by_layer: dict = {}
    for s in skills:
        by_layer[s["layer_label"]] = by_layer.get(s["layer_label"], 0) + 1

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "roots": [str(r[0]) for r in skill_roots(cwd)],
        "count": len(skills),
        "by_layer": by_layer,
        "errors": errors,
        "skills": skills,
    }


def search(index: dict, query: str, top: int = 10) -> list:
    q = set(tokenize(query))
    if not q:
        return []
    scored = []
    for s in index["skills"]:
        st = set(s.get("tokens") or [])
        if not st:
            continue
        overlap = q & st
        if not overlap:
            continue
        score = len(overlap) / max(1, len(q)) * 100
        # 名称直接命中加成
        if s["name"].lower() in query.lower():
            score += 40
        scored.append((round(score, 1), len(overlap), s))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]["name"]))
    return scored[:top]


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="扫描全量技能库并建立索引")
    ap.add_argument("--query", "-q", help="关键字检索")
    ap.add_argument("--layer", help="仅统计/检索某一层（project/user/connector/plugin/builtin）")
    ap.add_argument("--top", type=int, default=10, help="检索返回条数")
    ap.add_argument("--json", action="store_true", help="输出完整 JSON")
    ap.add_argument("--no-write", action="store_true", help="不写入索引文件")
    ap.add_argument("--cwd", help="工作目录（用于定位项目级技能）")
    args = ap.parse_args()

    cwd = Path(args.cwd).resolve() if args.cwd else Path.cwd()
    index = collect(cwd)

    if args.layer:
        index["skills"] = [s for s in index["skills"] if s["layer"] == args.layer]
        index["count"] = len(index["skills"])

    if not args.no_write and not args.query:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.query:
        hits = search(index, args.query, args.top)
        if args.json:
            print(json.dumps([{"score": h[0], "name": h[2]["name"], "layer": h[2]["layer_label"],
                               "desc": h[2]["description"][:160], "path": h[2]["path"]}
                              for h in hits], ensure_ascii=False, indent=2))
            return 0
        print(f"检索「{args.query}」命中 {len(hits)} 条（共扫描 {index['count']} 个技能）\n")
        for sc, ov, s in hits:
            print(f"[{sc:>5.1f}] {s['name']}  ({s['layer_label']})")
            print(f"        {s['description'][:150]}")
            print(f"        {s['path']}")
        return 0

    if args.json:
        print(json.dumps(index, ensure_ascii=False, indent=2))
        return 0

    print(f"技能索引已刷新：{index['count']} 个技能")
    for k, v in sorted(index["by_layer"].items()):
        print(f"  - {k}: {v}")
    print(f"索引文件：{INDEX_FILE}")
    if index["errors"]:
        print(f"  ! 解析异常 {len(index['errors'])} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
