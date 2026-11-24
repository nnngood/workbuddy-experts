# skill-auto-router · 安装说明

> ## ⚠️ 本文件不是安装包，请勿单独上传
> 本文件只是**阅读用**的说明文档，自己**不含 `SKILL.md`**。
> 一旦把本文件（或「本文件 + `skill-auto-router.skill`」）压成 zip 去安装／上传，必报错：
> **「解析失败：压缩包缺少 SKILL.md 文件」**。
>
> ✅ **要安装／要上传，请直接用下面两个文件，二选一：**
> - `skill-auto-router.skill` —— **本地安装**（拖进对话说"安装这个技能"，或在技能管理里选文件）
> - `skill-auto-router_upload.zip` —— **开放平台上传**（包根目录直接是 SKILL.md）

## 一、这是什么

一个 WorkBuddy / CodeBuddy **技能包（Skill）**。装好后，你在对话里提到相关场景时，AI 会自动加载这套工作方法并按流程执行。

**技能简介**：技能自动调度中枢

## 二、安装（两种方式，选其一）

### 方式 A：让 AI 帮你装（最省事，推荐）

1. 打开 WorkBuddy，新建一个对话
2. 把本压缩包里的 **`skill-auto-router.skill`** 文件直接拖进输入框
3. 输入一句：**「安装这个技能」**
4. AI 会自动解压并放到正确目录，重启/新建会话后即可使用

> 如果 AI 提示找不到目录，改用方式 B。

### 方式 B：手动解压（10 秒搞定）

**Windows：**
1. 右键 `skill-auto-router.skill` →「重命名」→ 把后缀改成 `.zip`，回车（提示改扩展名选"是"）
2. 右键 →「全部解压缩」，得到文件夹 `skill-auto-router`
3. 把 `skill-auto-router` 文件夹整个复制到：
   ```
   %USERPROFILE%\.workbuddy\skills\
   ```
   > 小技巧：在文件地址栏或 Win+R 里输入 `%USERPROFILE%\.workbuddy\skills` 直接回车即可到达。
   > 若 `.workbuddy` 文件夹不存在，手动新建一个即可。

**macOS / Linux：**
```bash
mkdir -p ~/.workbuddy/skills
unzip skill-auto-router.skill -d ~/.workbuddy/skills/
```

### 方式 C：装到单个项目里（团队共享推荐）

把 `skill-auto-router` 文件夹放到**项目根目录**的 `.workbuddy/skills/` 下：

```
你的项目/
└── .workbuddy/
    └── skills/
        └── skill-auto-router/
```

这样它随项目走，凡是拿到这个项目的人都能用，不需要各自安装。适合团队协作。

## 三、验证是否装好

新建对话，输入：**「你有哪些技能」** 或 **「skill-auto-router 怎么用」**。
若 AI 能说出这套方法的流程，就说明装好了。

## 四、卸载

直接删掉对应的 `skill-auto-router` 文件夹即可，无残留。

---

打包时间：2026-09-15 09:33

## 五、授权与出处

- 版本：v1.1.1 ｜ 打包时间：2026-09-15 09:33
- 使用范围：经授权可用于相关交付；未经许可不得二次对外分发或商用转售。
