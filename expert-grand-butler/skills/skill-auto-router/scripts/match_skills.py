#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""需求驱动的技能匹配打分引擎（零第三方依赖）。

输入「任务解析卡」，对全量技能索引逐条打分，输出分档决策表 + 建议调用链 + 缺口提示。
打分维度：成果形态吻合(45) + 领域语义重合(30) + 显式点名(20) + 层级优先(10) + 历史组合加成(15)。

用法：
  # 1) 直接传参
  python match_skills.py --task "写一份水务项目建议书" --forms word,pptx --domain 水务 \
                         --keywords 建议书,报价,方案 --task-type "正式方案类文档"

  # 2) 传任务解析卡
  python match_skills.py --card card.json

  # 3) 组合库快速通道（先查有无已晋级的典型组合）
  python match_skills.py --check-combo --task-type "正式方案类文档"

  # 4) 只要 JSON
  python match_skills.py --task "..." --forms pptx --json
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_skills import (  # noqa: E402
    DATA_DIR, INDEX_FILE, collect, tokenize,
)

USAGE_FILE = DATA_DIR / "usage_stats.json"

# 本技能自身名称：参与打分会让路由器把自己当候选，必须排除
SELF_NAME = "skill-auto-router"

# --------------------------------------------------------------------------- #
# 成果形态信号表：strong(区分度词,权重2) / weak(辅助词,权重1)
# 只有 strong 命中才可能拿满分；weak 单独命中不足为凭，避免"汇报/文档"这类泛词虚高。
# --------------------------------------------------------------------------- #
FORM_SIGNALS = {
    "word":  {"label": "Word 文档",
              "strong": ["docx", "python-docx", "建议书", "方案书", "计划书", "白皮书", "标书",
                         "投标方案", "公文", "备忘录", "说明书", "研究报告", "行业报告", "简历",
                         "合同", "协议", "word 文档", "docx 文件"],
              "weak": ["word", "文档", "报告", "手册", "纪要", "排版", "正式"]},
    "ppt":   {"label": "PPT 演示",
              "strong": ["pptx", "幻灯片", "演示文稿", "slide deck", "presentation", "路演", "课件",
                         "翻页", "16:9", "演讲"],
              "weak": ["ppt", "deck", "slide", "汇报", "演示", "页面"]},
    "excel": {"label": "Excel 表格",
              "strong": ["xlsx", "excel 表格", "工作簿", "透视表", "公式", "csv", "sheet", "台账",
                         "预算表", "统计表", "数据表"],
              "weak": ["excel", "表格", "统计", "清单"]},
    "html":  {"label": "网页/原型",
              "strong": ["html", "网页", "网站", "原型", "prototype", "dashboard", "landing page",
                         "前端页面", "单页应用", "交互式"],
              "weak": ["页面", "web", "看板", "可视化", "响应式"]},
    "pdf":   {"label": "PDF", "strong": ["pdf", "印刷", "画册", "版式"], "weak": ["导出", "打印"]},
    "chart": {"label": "图表可视化",
              "strong": ["echarts", "chart.js", "图表", "数据看板", "折线图", "柱状图", "饼图",
                         "趋势图", "可视化"],
              "weak": ["chart", "plot", "图形", "指标"]},
    "video": {"label": "视频",
              "strong": ["mp4", "视频", "短视频", "口播", "remotion", "配音", "分镜", "剪辑",
                         "video"],
              "weak": ["动画", "画面", "场景", "脚本"]},
    "image": {"label": "图片",
              "strong": ["配图", "海报", "封面", "插画", "生图", "抠图", "去水印", "白底图",
                         "image", "logo", "图标"],
              "weak": ["图片", "图像", "设计稿", "视觉"]},
    "code":  {"label": "代码/应用",
              "strong": ["代码", "脚本", "程序", "开发", "接口", "api", "部署", "重构", "调试",
                         "工程", "子代理", "pipeline"],
              "weak": ["应用", "工具", "运行", "命令行"]},
    "map":   {"label": "地图", "strong": ["地图", "gis", "地理信息", "选址", "路线规划", "map"],
              "weak": ["坐标", "区域"]},
    "3d":    {"label": "3D 模型", "strong": ["3d", "三维", "glb", "obj", "建模", "模型文件"],
              "weak": ["模型"]},
    "audio": {"label": "音频",
              "strong": ["音频", "配音", "语音合成", "tts", "转写", "播客", "响度"],
              "weak": ["声音", "audio", "录音"]},
    "research": {"label": "调研情报",
                 "strong": ["调研", "行业研究", "检索", "情报", "尽调", "竞品分析", "全网搜索",
                            "research", "search", "investigation", "web search"],
                 "weak": ["研究", "查询", "资料", "分析"]},
}

# 语义重合计算时过滤的通用词，避免"一份/正式/需要"这类词虚增分数
STOPWORDS = {
    "一份", "一个", "这个", "那个", "我们", "你们", "他们", "需要", "可以", "同时", "以及",
    "并且", "进行", "通过", "根据", "相关", "内容", "要求", "形成", "生成", "输出", "提供",
    "支持", "帮助", "使用", "主要", "包括", "部分", "一般", "常见", "如果", "因为", "所以",
    "但是", "而且", "已经", "正在", "就是", "什么", "怎么", "如何", "哪些", "一些", "这些",
    "那些", "之后", "之前", "目前", "现在", "应该", "必须", "能够", "是否", "对于", "关于",
    "由于", "为了", "提高", "提升", "优化", "完成", "获取", "查看", "时候", "问题", "情况",
    "方法", "方式", "过程", "结果", "目标", "基础", "重要", "不同", "各种", "全部", "直接",
    "然后", "最后", "第一", "第二", "第三", "正式", "客户", "领导", "版本",
    "帮我", "帮我写", "写一", "一条", "一款", "我要", "我想", "请帮", "麻烦", "谢谢",
    "能不能", "怎么样", "如何写", "需要写", "给我", "生成一", "做一份", "来一份",
    "做一", "出一", "拿一", "看一", "要一", "一点", "一起", "一下", "一份",
    "the", "and", "for", "with", "that", "this", "from", "your", "you", "can", "will",
    "are", "has", "have", "not", "use", "used", "using", "via", "its", "per", "etc",
    "into", "more", "most", "all", "any", "some", "each", "other", "such", "than",
    "then", "when", "what", "which", "who", "how", "our", "their", "them", "they",
    "there", "these", "those", "also", "but", "was", "were", "been", "being", "does",
    "should", "would", "could", "may", "might", "must", "about", "after", "before",
    "file", "files", "task", "tasks", "user", "users",
}

# 形态别名 -> 标准形态
FORM_ALIAS = {
    "doc": "word", "docx": "word", "文档": "word", "word": "word",
    "ppt": "ppt", "pptx": "ppt", "演示": "ppt", "幻灯片": "ppt", "slide": "ppt",
    "xls": "excel", "xlsx": "excel", "excel": "excel", "表格": "excel", "csv": "excel",
    "网页": "html", "网站": "html", "web": "html", "html": "html", "原型": "html",
    "pdf": "pdf", "图表": "chart", "chart": "chart", "可视化": "chart",
    "视频": "video", "video": "video", "mp4": "video",
    "图片": "image", "image": "image", "海报": "image",
    "代码": "code", "code": "code", "app": "code", "应用": "code",
    "地图": "map", "map": "map", "3d": "3d",
    "音频": "audio", "audio": "audio",
    "调研": "research", "research": "research", "研究报告": "research",
}

# 调用链阶段识别（用于排出建议执行顺序）；strong 计 2 分 / weak 计 1 分，
# 技能名与分类字段的命中额外 ×3 加权（名字最能说明它属于哪个环节）。
PHASE_PATTERNS = {
    1: {"name": "需求澄清与调研",
        "strong": ["调研", "行业研究", "需求澄清", "澄清", "访谈", "诊断", "定位", "尽调",
                   "竞品分析", "现状", "research", "explore", "requirement"],
        "weak": ["研究", "检索", "搜索", "search", "梳理", "资料", "分析"]},
    2: {"name": "内容与方案生产",
        "strong": ["撰写", "写作", "writer", "writing", "文案", "copywriting", "纪要", "minutes",
                   "memo", "备忘录", "教案", "课程开发", "脚本", "方案设计", "报告生成",
                   "商业计划", "建议书", "白皮书"],
        "weak": ["内容", "生成", "输出", "方案", "报告", "文档", "规划", "拆解"]},
    3: {"name": "视觉与格式加工",
        "strong": ["pptx", "幻灯片", "演示文稿", "排版", "美化", "design", "视觉设计", "图表",
                   "chart", "海报", "封面", "视频", "video", "渲染", "模板", "原型", "html",
                   "frontend", "deploy"],
        "weak": ["ppt", "格式", "设计", "页面", "画面", "样式", "版式"]},
    4: {"name": "质检与交付",
        "strong": ["质检", "qc", "预渲染", "目视", "校验", "转换", "convert", "部署", "发布",
                   "上线", "打包", "present", "压缩", "verify", "validate"],
        "weak": ["交付", "检查", "预览", "验证", "导出"]},
}

TIER_RULES = [("主选", 55), ("辅选", 38), ("备选", 22)]
LAYER_BONUS = {"project": 10, "user": 8, "connector": 7, "plugin": 6, "builtin": 5}

# 收尾环节识别标记（用于"阶段补位"时挑出真正的质检/转换技能）
QC_MARKERS = ["质检", "qc", "预渲染", "目视", "校验", "转换", "convert", "审查", "验证", "压缩"]


# --------------------------------------------------------------------------- #
def norm_forms(forms) -> list:
    out = []
    for f in forms or []:
        f = str(f).strip().lower()
        if not f:
            continue
        key = FORM_ALIAS.get(f, f if f in FORM_SIGNALS else None)
        if key and key not in out:
            out.append(key)
    return out


def load_index(cwd: Path) -> dict:
    if INDEX_FILE.is_file():
        try:
            idx = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
            if idx.get("skills"):
                return idx
        except Exception:  # noqa: BLE001
            pass
    return collect(cwd)


def load_usage() -> dict:
    if USAGE_FILE.is_file():
        try:
            return json.loads(USAGE_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    return {"records": [], "skill_counts": {}, "combo_library": {}}


def combo_lookup(usage: dict, task_type: str, promoted_only: bool = True) -> list:
    if not task_type:
        return []
    key = re.sub(r"\s+", "", task_type).lower()
    hits = []
    for k, combos in (usage.get("combo_library") or {}).items():
        if key and (key in re.sub(r"\s+", "", k).lower() or re.sub(r"\s+", "", k).lower() in key):
            for c in combos:
                if (not promoted_only) or c.get("promoted"):
                    hits.append(c)
    hits.sort(key=lambda c: -c.get("count", 0))
    return hits


def build_df(index: dict) -> dict:
    """统计每个词在技能库中的出现频次（document frequency），用于 IDF 加权。"""
    df: dict = {}
    for s in index["skills"]:
        for t in set(s.get("tokens") or []):
            df[t] = df.get(t, 0) + 1
    return df


def token_weight(t: str, df: dict, n_docs: int) -> float:
    """IDF 权重：越罕见的词越有区分度。通用词（如"研究报告"）会被压到接近 0.1。"""
    return math.log((n_docs + 1) / (df.get(t, 0) + 1)) + 0.1


def dedup_terms(terms: list) -> list:
    """去掉被更长命中词包含的短词/子串，让"命中关键词"一栏可读。"""
    terms = sorted(set(terms), key=len, reverse=True)
    kept = []
    for t in terms:
        if not any(t != k and t in k for k in kept):
            kept.append(t)
    return kept


def build_signature(task_tokens: set, df: dict, n_docs: int, k: int = 8):
    """从任务词里挑出最有区分度的 k 个当"任务签名"。
    只有命中签名词的技能才算真·领域相关；命中"智能/方案/报告"这类泛词不计分。

    关键：**必须过滤 df=0 的词**——技能库里根本没人提过的 n-gram（如"水质监"）
    按 IDF 公式会拿到最高权重，却永远匹配不上，会把签名整体拉成 0 分。"""
    candidates = [t for t in task_tokens if df.get(t, 0) >= 1]
    if not candidates:
        candidates = list(task_tokens)
    sig = sorted(candidates, key=lambda t: (-token_weight(t, df, n_docs), -len(t)))[:k]
    anchor = sum(token_weight(t, df, n_docs) for t in sig) or 1.0
    return sig, anchor


def score_skill(skill: dict, card: dict, task_tokens: set, usage: dict,
                df: dict = None, n_docs: int = 1,
                signature: list = None, sig_anchor: float = 0.0) -> dict:
    df = df or {}
    signature = signature or []
    text = " ".join(filter(None, [
        skill.get("name", ""), skill.get("display_name", ""),
        skill.get("category", ""), skill.get("description", ""),
    ])).lower()
    text_tokens = (set(skill.get("tokens") or []) - STOPWORDS)

    # --- 1) 成果形态吻合度 (45)：strong 计 2 分 / weak 计 1 分，满 4 分封顶 ---
    form_detail = {}
    for form in card["deliverable_forms"]:
        sig = FORM_SIGNALS[form]
        pts = 2 * sum(1 for kw in sig["strong"] if kw in text)
        pts += sum(1 for kw in sig["weak"] if kw in text)
        form_detail[form] = round(min(1.0, pts / 4.0), 2)
    if form_detail:
        depth = max(form_detail.values())
        coverage = sum(1 for v in form_detail.values() if v >= 0.5) / len(form_detail)
        form_score = 45.0 * (0.5 * depth + 0.5 * coverage)
    else:
        form_score = 20.0  # 未指定形态，给中性偏低分，避免无差别拉平

    # --- 2) 领域语义重合度 (30)：只看"任务签名词"命中比例 ---
    if signature and sig_anchor > 0:
        sig_hit = sum(token_weight(t, df, n_docs) for t in signature if t in text_tokens)
        domain_score = 30.0 * min(1.0, (sig_hit / sig_anchor) ** 0.5)
        overlap = task_tokens & text_tokens
        ordered = sorted(overlap, key=lambda t: (-token_weight(t, df, n_docs), -len(t)))
        matched_terms = dedup_terms(ordered)[:8]
    else:
        domain_score, matched_terms = 8.0, []

    # --- 3) 显式点名 (20) ---
    raw_task = card["task"].lower()
    name = skill.get("name", "").lower()
    dirname = skill.get("dir", "").lower()
    explicit = 0.0
    if name and len(name) > 2 and name in raw_task:
        explicit = 20.0
    elif dirname and len(dirname) > 2 and dirname in raw_task:
        explicit = 16.0
    else:
        at = skill.get("display_name", "").lower()
        if at and len(at) > 1 and at in raw_task:
            explicit = 13.0

    # --- 4) 层级优先 (10) ---
    layer_score = float(LAYER_BONUS.get(skill.get("layer"), 5))

    # --- 5) 任务类型吻合 (10) ---
    #    程序型技能（如"长文档双版本交付流水线"）天生不含行业词汇，
    #    但它明确服务于某一类任务——任务类型词命中正好补上这块。
    type_score = 0.0
    type_tokens = set(card.get("_type_tokens") or [])
    if type_tokens:
        to = type_tokens & text_tokens
        if to:
            type_score = 10.0 * min(1.0, len(to) / 2.0)

    # --- 6) 历史组合加成 (15) ---
    combo_score = 0.0
    for c in combo_lookup(usage, card.get("task_type", ""), promoted_only=False):
        if skill["name"] in c.get("chain", []):
            combo_score = 15.0 if c.get("promoted") else 8.0
            break

    # --- 相关性闸门：形态分必须由领域匹配"解锁"，避免"形态沾边但领域无关"的技能虚高 ---
    rel = (domain_score / 30.0) if signature else 0.6
    form_eff = round(form_score * (0.40 + 0.60 * rel), 1)
    total = min(100.0, form_eff + domain_score + explicit + layer_score
                + type_score + combo_score)

    return {
        "name": skill["name"],
        "layer": skill.get("layer_label", skill.get("layer")),
        "category": skill.get("category", ""),
        "path": skill.get("path", ""),
        "description": (skill.get("description") or "")[:220],
        "score": round(total, 1),
        "breakdown": {
            "形态吻合": form_eff,
            "语义重合": round(domain_score, 1),
            "显式点名": round(explicit, 1),
            "层级优先": round(layer_score, 1),
            "类型吻合": round(type_score, 1),
            "组合加成": round(combo_score, 1),
        },
        "form_coverage": form_detail,
        "matched_terms": matched_terms,
    }


def classify_phase(res: dict) -> int:
    """判定技能属于调用链的哪个阶段。技能名/分类命中权重 ×3。"""
    head = (res["name"] + " " + res.get("category", "")).lower()
    body = (res.get("description") or "").lower()
    tally = {}
    for ph, spec in PHASE_PATTERNS.items():
        pts = 2 * sum(1 for kw in spec["strong"] if kw in body)
        pts += sum(1 for kw in spec["weak"] if kw in body)
        pts += 3 * (2 * sum(1 for kw in spec["strong"] if kw in head)
                    + sum(1 for kw in spec["weak"] if kw in head))
        tally[ph] = pts
    best = max(tally.items(), key=lambda kv: (kv[1], -kv[0]))
    return best[0] if best[1] > 0 else 2


def tier_of(score: float) -> str:
    for label, thr in TIER_RULES:
        if score >= thr:
            return label
    return "参考"


def build_chain(selected: list, pool: list, limit: int = 6) -> list:
    """最高分技能领衔（主力），其余按 调研 -> 生产 -> 加工 -> 质检 阶段排序。
    并做"阶段补位"：若链条缺质检/交付环节，从候选中补一个，且保证不被长度截断掉。"""
    for r in pool:
        r.setdefault("phase", classify_phase(r))
    if not selected:
        return []
    head = selected[0]
    rest = sorted(selected[1:], key=lambda r: (r["phase"], -r["score"]))

    chain = [head["name"]]
    for r in rest:
        if r["name"] not in chain:
            chain.append(r["name"])

    qc = None
    phases = {next(r["phase"] for r in pool if r["name"] == nm) for nm in chain}
    if 4 not in phases:
        # 补位只认真正的收尾环节（质检/渲染校验/格式转换），避免把无关工具塞进链条
        cand = sorted([r for r in pool
                       if r["phase"] == 4 and r["score"] >= 18
                       and any(m in (r["name"] + r["description"]).lower() for m in QC_MARKERS)],
                      key=lambda r: -r["score"])
        qc = cand[0]["name"] if cand and cand[0]["name"] not in chain else None

    final = chain[:limit]
    if qc and qc not in final:
        final = chain[:limit - 1] + [qc]
    return final


def render(card: dict, results: list, chain: list, combos: list, forms: list, top: int) -> str:
    lines = []
    lines.append("# 技能匹配决策表")
    lines.append("")
    lines.append(f"- 任务：{card['task'][:120]}")
    lines.append(f"- 任务类型：{card.get('task_type') or '（未指定）'}")
    if forms:
        lines.append("- 目标成果形态：" + "、".join(FORM_SIGNALS[f]["label"] for f in forms))
    if card.get("domain"):
        lines.append(f"- 领域：{card['domain']}")
    lines.append(f"- 生成时间：{datetime.now():%Y-%m-%d %H:%M:%S}")
    lines.append("")

    if combos:
        lines.append("## 组合库命中（历史验证过的路径，优先复用）")
        for c in combos[:3]:
            mark = "★已晋级" if c.get("promoted") else "试用中"
            lines.append(f"- [{mark} ×{c.get('count')}] {' → '.join(c.get('chain', []))}")
        lines.append("")

    lines.append(f"## 匹配结果（Top {min(top, len(results))}）")
    lines.append("")
    lines.append("| 档位 | 技能 | 层级 | 得分 | 形态 | 语义 | 类型 | 命中关键词 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in results[:top]:
        lines.append("| {} | `{}` | {} | {} | {} | {} | {} | {} |".format(
            tier_of(r["score"]), r["name"], r["layer"], r["score"],
            r["breakdown"]["形态吻合"], r["breakdown"]["语义重合"],
            r["breakdown"]["类型吻合"],
            "、".join(r["matched_terms"][:4]) or "—"))
    lines.append("")

    if chain:
        lines.append("## 建议调用链（按执行顺序）")
        lines.append("")
        for i, nm in enumerate(chain, 1):
            ph = next((r["phase"] for r in results if r["name"] == nm), 2)
            tag = "【主力・最高匹配】" if i == 1 else ""
            lines.append(f"{i}. `{nm}`  {tag} —— 阶段{ph}·{PHASE_PATTERNS[ph]['name']}")
        lines.append("")

    # 缺口提示
    gaps = [FORM_SIGNALS[f]["label"] for f in forms
            if not any(r["form_coverage"].get(f, 0) >= 0.5 for r in results[:top])]
    best = results[0]["score"] if results else 0
    notes = []
    if gaps:
        notes.append(f"⚠️ 本地技能库对「{'、'.join(gaps)}」覆盖较弱，建议补充检索：推荐市场（workbuddy_marketplace_skill search）+ 开放技能生态（find-skills）。")
    if best < TIER_RULES[0][1]:
        notes.append(f"⚠️ 最高分未达「主选」线（{TIER_RULES[0][1]} 分），说明本地匹配不充分，务必执行开放空间检索后再定方案。")
    if not notes:
        notes.append("✅ 本地技能库已能覆盖主要交付形态，可直接进入执行。")
    lines.append("## 风险与补充检索提示")
    lines.append("")
    for n in notes:
        lines.append(f"- {n}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="需求驱动的技能匹配打分引擎")
    ap.add_argument("--card", help="任务解析卡 JSON 文件路径")
    ap.add_argument("--task", help="任务原始描述")
    ap.add_argument("--task-type", dest="task_type", default="", help="任务类型（用于组合库检索与沉淀）")
    ap.add_argument("--forms", default="", help="目标成果形态，逗号分隔（word,ppt,excel,html,video...）")
    ap.add_argument("--domain", default="", help="领域/行业")
    ap.add_argument("--keywords", default="", help="补充关键词，逗号分隔")
    ap.add_argument("--top", type=int, default=8, help="输出条数")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--check-combo", action="store_true", help="仅查组合库快速通道")
    ap.add_argument("--cwd", help="工作目录")
    args = ap.parse_args()

    cwd = Path(args.cwd).resolve() if args.cwd else Path.cwd()

    if args.card:
        card = json.loads(Path(args.card).read_text(encoding="utf-8"))
    else:
        card = {}
    card.setdefault("task", args.task or "")
    card.setdefault("task_type", args.task_type)
    card.setdefault("domain", args.domain)
    card.setdefault("deliverable_forms", [])
    card.setdefault("keywords", [])
    if args.forms:
        card["deliverable_forms"] = [x for x in re.split(r"[,\s、]+", args.forms) if x]
    if args.keywords:
        card["keywords"] = [x for x in re.split(r"[,\s、]+", args.keywords) if x]
    if args.task_type:
        card["task_type"] = args.task_type

    usage = load_usage()

    if args.check_combo:
        combos = combo_lookup(usage, card["task_type"], promoted_only=False)
        if args.json:
            print(json.dumps(combos, ensure_ascii=False, indent=2))
        elif not combos:
            print(f"组合库中暂无「{card['task_type'] or '(未指定类型)'}」的历史组合，走常规匹配流程。")
        else:
            print(f"组合库命中 {len(combos)} 条：")
            for c in combos:
                print(f"  [{'已晋级' if c.get('promoted') else '试用中'} ×{c.get('count')}] {' → '.join(c.get('chain', []))}")
        return 0

    forms = norm_forms(card["deliverable_forms"])
    card["deliverable_forms"] = forms

    task_text = " ".join([card["task"], card.get("domain", ""), " ".join(card.get("keywords") or [])])
    task_tokens = set(tokenize(task_text)) - STOPWORDS
    for extra in card.get("constraints") or []:
        task_tokens |= (set(tokenize(str(extra))) - STOPWORDS)
    # 任务类型词：用于"类型吻合"维度（程序型技能靠它补分）
    card["_type_tokens"] = sorted(set(tokenize(card.get("task_type", ""))) - STOPWORDS)

    index = load_index(cwd)
    df = build_df(index)
    n_docs = max(1, index["count"])
    # 排除本技能自身，避免路由器把自己当成候选技能推荐
    pool = [s for s in index["skills"] if s["name"] != SELF_NAME]

    # 任务签名：只拿最有区分度的词当领域相关性的判据
    signature, sig_anchor = build_signature(task_tokens, df, n_docs)

    results = [score_skill(s, card, task_tokens, usage, df, n_docs, signature, sig_anchor)
               for s in pool]
    results = [r for r in results if r["score"] >= 15]
    results.sort(key=lambda r: (-r["score"], r["name"]))

    combos = combo_lookup(usage, card.get("task_type", ""), promoted_only=False)
    chain = build_chain(results[:args.top], results)

    if args.json:
        print(json.dumps({
            "card": card,
            "index_size": index["count"],
            "combo_hits": combos,
            "chain": chain,
            "results": results[:args.top],
        }, ensure_ascii=False, indent=2))
        return 0

    print(render(card, results, chain, combos, forms, args.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
