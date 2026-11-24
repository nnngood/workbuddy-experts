# WorkBuddy 专家包分享

本仓库分享 WorkBuddy 专家「专家大掌柜」（技能调度大掌柜，标识 `expert-grand-butler`）。

## 专家能做什么

你派活，掌柜派技能。它读懂需求，从免费且验证好用的技能中挑出最佳组合，排成流水线执行并验收。内置技能 `skill-auto-router`，无需额外安装。

两条铁律：只用免费技能；优先用被验证好用的技能。

## 如何安装

1. 下载 `expert-grand-butler.zip.base64`，执行还原命令：

   ```bash
   base64 -d expert-grand-butler.zip.base64 > expert-grand-butler.zip
   ```

   Windows PowerShell 可用：

   ```powershell
   [IO.File]::WriteAllBytes('expert-grand-butler.zip', [Convert]::FromBase64String((Get-Content 'expert-grand-butler.zip.base64' -Raw)))
   ```

2. 把生成的 `expert-grand-butler.zip` 拖入 WorkBuddy 对话框，说「安装这个专家」。
3. 在「专家中心 → 我的专家」中召唤「专家大掌柜」。

## 目录说明

- `expert-grand-butler/`：专家源码（plugin.json、Agent 人设、内置技能与脚本）
- `expert-grand-butler/avatars/expert.png.base64`：头像（512×512 PNG）的 base64 文本，解码方式同上
- `expert-grand-butler.zip.base64`：完整专家包（含头像）的 base64 文本，用于一键还原安装

## 注意

- 专家标识 `expert-grand-butler` 创建后不可修改。
- `plugin.json` 中的作者信息为占位值，正式上架前请替换为实际署名与邮箱。
