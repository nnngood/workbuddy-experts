# 预置推荐组合（人工整理，非统计产物）

> 这是**人工筛选的高置信组合**，覆盖已知的高频任务类型，用于冷启动阶段"第一次就能走对路"。
> 与 `data/combo_library.md`（脚本统计生成、靠真实使用自动晋级）是两套东西：
> **本文件的组合在匹配时会作为候选参考；一旦被真实调用并记录，就会自动进入统计组合库。**
>
> 组合内的技能名均已在本机技能索引中核实存在。标 `(?)` 的表示**该环节待实测确认是否需要**。

---

## 1. 正式方案类文档（Word + PPT 双版本）· 最高频

```
formal-doc-dual-delivery
  → project-requirement-plan-design (?)   需求澄清，项目方信息不全时必上
  → consulting-doc-kit (?)                需要标准十章节结构时替代/补充上一条
  → office-preview-qc                     交付前目视排版质检（必过）
```
适用：项目建议书、可研报告、商业计划书、申报方案、白皮书。
要点：先 HTML 预览、再出 Word；正式方案默认配 PPT 汇报版。

## 2. 投标 / 竞标方案

```
bid-tech-penetration-proposal             招标文件穿透解读 → 合作/投标方案
  → bid-proposal-writer (?)               培训类标书改用这一支
  → formal-doc-dual-delivery (?)          需要 Word+PPT 双版本时叠加
  → office-preview-qc
```

## 3. 战略规划咨询

```
blm-strategy-leading-model                BLM 四维十面五步工作流
  → office-preview-qc
```
产出：《BLM 模型战略分析与任务分解报告》Word + PPT。

## 4. 培训课程开发

```
wangshaopeng-course-dev                   五份成稿（学员分析/框架/大纲/课件/讲师手册）
  → teaching-ppt-generator (?)            高职院校授课课件场景改用这一支
  → ppt-generator (?)                     需要通用演示文稿时
  → office-preview-qc
```

## 5. 行业 / 企业研究

```
haiawake-industry-research (或 industry-research-framework)
  → company-research (?)                  需要企业实体、竞品名录时
  → quantitative-analysis (?)             有定量数据需做交叉分析与显著性检验时
  → smart-charts (?)                      需要把数据变成交互图表时
  → formal-doc-dual-delivery              汇总为正式报告
```
另：`summarize-all` / `summarize` 用于长材料速读；`markitdown` 用于批量摄取多格式资料。

## 6. 定量数据分析

```
quantitative-analysis                     两阶段：交叉分析表 → HTML 图表报告
  → smart-charts (?)                      需要独立交互图表时
  → project-analysis-report (?)           多份 Excel 汇总为综合 HTML 报告时
```

## 7. 简历筛选与评价

```
resume-screening-evaluation               四步法：解析 → 对标 → 评分 → 报告(Word+PPT)
  → office-preview-qc
```

## 8. 短视频口播文案（抖音 / 视频号）

```
deai-promax                               去 AI 味，保真改写（必过）
  → video-prompt-expert (?)               需要转成 AI 视频提示词时
  → infimind-video-generation (?)         需要直接出片时
  → 视频号爆款短视频拆解（付费版：全能）【零一数科·出品】  (?)  需要拆解对标爆款时
```
另有：`douyin-copy-extract__skillhub` 用于从分享链接提取原文（素材获取环节）。

## 9. 公众号内容生产

```
wechat-topic-outline-planner (或 wechat-write)
  → wechat-draft-writer (或 微信公众号写作工具)
  → deai-promax (?)                       去 AI 味
  → wechat-cover                          封面图方案
  → wechat-article-publisher              排版并存入草稿箱
```
辅助：`wechat-title-generator`（标题）、`wechat-style-profiler`（风格定位）、`wechat-article-search`（找对标）。

## 10. 企业站点 / 小程序定制（瑞哈希线）

```
ruihashi-web-miniapp                      六步法：品牌分析 → AI 信源报告 → 原型 → 提案PPT → 汇报视频 → 话术
  → ruihashi-ops-audit (?)                上线后的 SEO 合规与内容优化诊断
  → office-preview-qc
```

## 11. 研讨会 / 会议方案

```
formal-doc-dual-delivery
  → ppt-generator (?)                     需要演示版
  → office-preview-qc
```
另：`meeting-minutes-generator`（会议纪要）、`tencent-meeting-skill`（会议管理）、
`emmx-mindmap-parser`（.emmx 脑图转方案）。

## 12. 内部共创与行动落地

```
super-team-co-creation                    七步法：现状 → 影响因素 → 行动计划Excel → 风险 → 过程地图
（客户咨询交付场景改用 wsp-seven-step-method）
```

## 13. 产品介绍视频 / 演示视频

```
infimind-video-analysis (?)               先拆解参考片
  → video-prompt-expert                   写分镜提示词
  → infimind-video-generation             出片
```

---

## 使用纪律

1. **本文件是参考，不是圣经。** 优先用第二步的匹配引擎实测打分；本文件的组合用于
   "匹配结果离散、拿不准"时提供兜底判断。
2. **带 `(?)` 的环节必须有明确触发条件才纳入链条**，不要无脑全上。
3. **不同时调用同能力技能**（详见 `matching-rules.md` 第四节）。
4. 新沉淀出的高频组合请写回 `data/`（由 `record_usage.py` 自动管理），
   若某种组合反复验证有效且稳定，再考虑晋升到本文件。
