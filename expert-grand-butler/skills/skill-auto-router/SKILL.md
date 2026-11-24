---
name: skill-auto-router
version: 1.1.1
display_name: 技能自动调度中枢
display_name_en: skill-auto-router
description: "需求驱动的技能自动调度中枢。把用户需求解析为结构化「任务解析卡」（含成果形态判断），在本地五层技能库、推荐市场与开放技能生态中全面检索并精准匹配，输出分档决策表与建议调用链；任务收尾自动沉淀高频技能与典型组合，下次同类任务直接走快速通道。当用户提出「自动匹配技能」「该用哪个技能」「帮我选技能」「技能编排」「多技能组合」「这个任务用什么技能」「任务复盘沉淀经验」，或启动一项需要多种能力协作的复杂交付任务时使用。适用于：正式文档/PPT交付、投标方案、行业研究、数据分析、短视频文案、企业站点建设等任意需要挑技能的场景。"
description_zh: "需求驱动的技能自动调度中枢。把用户需求解析为结构化「任务解析卡」（含成果形态判断），在本地五层技能库、推荐市场与开放技能生态中全面检索并精准匹配，输出分档决策表与建议调用链；任务收尾自动沉淀高频技能与典型组合，下次同类任务直接走快速通道。当用户提出「自动匹配技能」「该用哪个技能」「帮我选技能」「技能编排」「多技能组合」「这个任务用什么技能」「任务复盘沉淀经验」，或启动一项需要多种能力协作的复杂交付任务时使用。适用于：正式文档/PPT交付、投标方案、行业研究、数据分析、短视频文案、企业站点建设等任意需要挑技能的场景。"
description_en: "Requirement-driven skill auto-router for WorkBuddy. It converts a raw user request into a structured Task Card (with deliverable-form detection across 13 output types), then searches the local five-layer skill library, the recommended marketplace, and the open skill ecosystem to score and rank candidate skills. It outputs a tiered decision table plus a suggested invocation chain ordered by work stage (research, production, formatting, quality check), and flags coverage gaps needing external search. After delivery it records which skills were used and in what order, then promotes repeatedly used chains into preset combos so similar future tasks take a fast path. Use it when the user asks to auto-match skills, choose which skill to use, orchestrate multiple skills, or run a task retrospective. Best for multi-step delivery work such as formal proposals, bid packages, industry research, data analysis, short-video scripts, and website builds."
agent_created: true
---

# 技能自动调度中枢

把一个"要交付什么"的需求，变成一条"调哪几个技能、按什么顺序调"的可执行生产线；
任务做完再把这次的选择记下来，用得越多越准。

**核心信念：技能不该靠猜，该靠解析 + 检索 + 打分 + 记忆。**

---

## 三步流水线总览

| 步 | 名称 | 干什么 | 产出 |
|---|---|---|---|
| **第 0 步** | 组合库快速通道 | 先查这个任务类型有没有历史验证过的路径 | 命中就直接复用，跳过打分 |
| **第 1 步** | 需求与成果形态解析 | 六问拆解需求，判定交付物形态与质量线 | **任务解析卡**（JSON） |
| **第 2 步** | 开放空间检索与精准匹配 | 四级检索通道 + 六维打分 + 链条排序 | **技能匹配决策表** |
| **第 3 步** | 记忆与组合沉淀 | 记录本次调用轨迹，自动晋级预置组合 | 更新记忆库 |

---

## 前置准备

脚本目录用绝对路径调用，先设好变量（本技能脚本零第三方依赖，任何 Python 3.9+ 均可；
下面优先用本机托管解释器，不可用时改用 `python`）：

```bash
SKILL_DIR="$HOME/.workbuddy/skills/skill-auto-router"
# 本机托管 Python（Windows 为 %USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe）
PY="$HOME/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
[ -x "$PY" ] || PY="$HOME/.workbuddy/binaries/python/versions/3.13.12/python.exe"
[ -x "$PY" ] || PY=python
```

首次使用或技能库有变动时，刷新一次索引（约 200 个技能，秒级完成）：

```bash
"$PY" "$SKILL_DIR/scripts/scan_skills.py"
```

---

## 第 0 步：组合库快速通道（先查记忆，别重复思考）

```bash
"$PY" "$SKILL_DIR/scripts/match_skills.py" --check-combo --task-type "任务类型"
```

- **命中「已晋级」组合** → 直接按该链条执行，同时看一眼有没有明显不适用的环节，然后跳到"执行"。
- **只有「试用中」组合** → 作为参考，仍走第 1、2 步完整匹配。
- **无命中** → 正常走第 1、2 步。

> 任务类型必须用固定词汇，见 `references/intent-analysis-framework.md` 第四节的命名表——
> **名字不统一，记忆就是碎的。**

---

## 第 1 步：需求与成果形态解析

**完整方法论见 `references/intent-analysis-framework.md`（执行前必读一次）。**

按"任务六问"过一遍：要什么 / 给谁看 / 什么形态 / 什么领域 / 什么约束 / 什么标准算合格。
把答案落成任务解析卡：

```json
{
  "task": "用户原话，原样保留",
  "task_type": "正式方案类文档",
  "deliverable_forms": ["word", "ppt"],
  "domain": "水务/智慧城市",
  "audience": "客户方决策层",
  "keywords": ["建议书", "报价", "水质监测"],
  "constraints": ["正式可呈报", "含数据表格"],
  "quality_bar": "领导呈报级"
}
```

**三个必须守住的点：**

1. `deliverable_forms` 只能填 13 个标准形态键（`word/ppt/excel/html/pdf/chart/video/image/code/map/3d/audio/research`），**不许自造词**，否则匹配引擎识别不了。
2. **主动补隐含形态**——"报给领导"意味着 Word+PPT；"发抖音"意味着视频+封面图；"投标"意味着正文+讲标+报价三件套。用户没说，不等于不需要。
3. 把卡存成文件（如 `card.json`），第 2 步直接喂给脚本，避免参数散落。

**需求信息明显不足时**（连给谁看、要什么形态都判断不出来），先向用户确认关键项，不要硬猜后一路错到底。

---

## 第 2 步：开放空间检索与精准匹配

**完整规则见 `references/matching-rules.md`（执行前必读一次）。**

### 2.1 通道① 本地技能索引（必走）

```bash
# 直接找：拿形态词 + 领域词做检索
"$PY" "$SKILL_DIR/scripts/scan_skills.py" --query "建议书 汇报 方案" --top 10

# 或直接跑完整匹配打分
"$PY" "$SKILL_DIR/scripts/match_skills.py" --card card.json --top 8
```

也可以内联传参（不想建卡的时候）：

```bash
"$PY" "$SKILL_DIR/scripts/match_skills.py" \
  --task "写一份水务水质监测机器人项目建议书，正式可呈报，配汇报PPT" \
  --task-type "正式方案类文档" --forms word,ppt --domain 水务 \
  --keywords 建议书,报价,方案 --top 8
```

脚本会输出**技能匹配决策表**：分档结果 + 建议调用链 + 缺口提示。

### 2.2 通道② 推荐市场（本地不达标时才走）

当脚本提示 **最高分 < 55**（未达"主选"线），或某个目标形态**零覆盖**时，用市场检索工具（action=`search`）
按"形态 + 领域"组合词检索，例如：`PPT 生成`、`行业研究报告`、`视频剪辑`。
找到合适技能后安装，然后**重新跑 2.1**，让新技能进入索引参与打分。

### 2.3 通道③ 开放技能生态（②仍然不达标时才走）

调用 `find-skills` 技能进行社区检索，关键词同上。

### 2.4 通道④ 连接器能力（任务需要外部系统时）

任务涉及邮箱、会议、在线表格、云文档等外部系统时，看会话连接器状态；
缺能力则用 `recommend-connectors` 推荐，不要硬用本地技能硬扛。

### 2.5 定案依据（三者取一）

当 2.1 的候选与 `references/known-combos.md` 的预置组合不一致时，按下列优先级定案：

1. 预置组合里有、且匹配表里也主选命中的 → **直接采信**
2. 仅匹配表主选命中 → **采信匹配表**（打分是有数据支撑的）
3. 仅预置组合里有 → 只有当匹配表结果**明显离散/无主选**时才采信，并在心里标记为"待实测"

### 2.6 呈现纪律

**只把最终选定的技能和调用链告诉用户**，不要把 20 个候选全倒出来。
用户要的是"用哪个"，不是"有哪些"。展示建议链条 + 一句话理由即可。

### 2.7 执行

按链条顺序调用技能。链条第 1 位是**主力技能**，先跟它走；后续环节按阶段推进：
**调研 → 生产 → 加工 → 质检**。质检环节不许跳——交付前必须过一遍。

---

## 第 3 步：任务收尾——记忆与组合沉淀

**任务交付完成后的标准动作，不许省。**

```bash
"$PY" "$SKILL_DIR/scripts/record_usage.py" \
  --task-type "正式方案类文档" \
  --forms word,ppt \
  --skills "formal-doc-dual-delivery,project-requirement-plan-design,office-preview-qc" \
  --success true \
  --notes "水务建议书，客户领导呈报版"
```

- `--skills` **必须按实际调用顺序填**，顺序是组合记忆的一部分。
- 同一任务类型的相同调用链**重复达到阈值（默认 2 次）自动晋级为"预置组合"**，
  下次第 0 步就能直接命中。
- 多一个成员会自动并入同一组合（成员重合度 ≥ 0.6 视为同一链条），不会碎成一堆。

查看沉淀效果：

```bash
"$PY" "$SKILL_DIR/scripts/record_usage.py" --stats
```

会输出：预置组合 / 试用中组合 / 高频技能 Top N / 强关联技能对 Top N。
同时自动生成人读版 `data/combo_library.md`。

删掉某类错误记忆：

```bash
"$PY" "$SKILL_DIR/scripts/record_usage.py" --forget "任务类型"
```

---

## 脚本清单

| 脚本 | 作用 |
|---|---|
| `scripts/scan_skills.py` | 扫描五层技能库建索引；`--query` 关键字检索 |
| `scripts/match_skills.py` | 匹配打分引擎；`--check-combo` 组合快速通道；`--json` 机器可读 |
| `scripts/record_usage.py` | 记录调用轨迹、晋级组合；`--stats` 看报告；`--forget` 删记忆 |
| `scripts/combo_report.py` | 生成记忆统计报告与人读版组合库 |

## 数据文件

| 文件 | 说明 |
|---|---|
| `data/skill_index.json` | 技能索引（自动刷新，可删，会重建） |
| `data/usage_stats.json` | **记忆库本体**，请勿手工破坏结构 |
| `data/combo_library.md` | 人读版组合库（自动生成） |

## 参考文档

| 文件 | 什么时候读 |
|---|---|
| `references/intent-analysis-framework.md` | 第 1 步前读。内含形态识别陷阱与任务类型命名表 |
| `references/matching-rules.md` | 第 2 步前读。内含打分模型、去重规则、新建技能的判断条件 |
| `references/known-combos.md` | 匹配结果离散拿不准时读。人工预置的高置信组合 |

---

## 红线纪律

1. **不许跳过第 1 步直接检索。** 形态没判对，检索再准也是错的。
2. **不许跳过第 2 步直接凭印象挑技能。** 索引里有 200 个技能，印象一定不全。
3. **不许跳过第 3 步。** 不沉淀，这个技能就退化成一个普通的手动选择器，失去全部价值。
4. **本地能覆盖就不要外检。** 本地主选已命中还去搜市场，是浪费用户时间。
5. **发现能力缺口时，不要用不匹配的技能硬凑。** 走 `skill-creator` 新建。
6. **不要为了"看起来专业"而堆砌技能。** 链条默认 6 个以内；少而准远胜多而杂。