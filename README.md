<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/banner-zh-dark.svg">
    <img src="assets/banner-zh.svg" alt="屁宝袋 PiBaoDai：把脑洞装进袋子，把好用的招数拿出来。" width="100%">
  </picture>
</p>

<p align="center">
  <strong>实用 Skills 与独立思考的开源百宝袋。</strong><br>
  把经验变成方法，让人和 AI 都能用。
</p>

<p align="center">
  <a href="https://github.com/flfk666666/pibaodai/stargazers"><img src="https://img.shields.io/github/stars/flfk666666/pibaodai?style=flat-square&amp;logo=github&amp;label=Stars&amp;color=d4a45f" alt="GitHub Stars"></a>
  <a href="https://github.com/flfk666666/pibaodai/forks"><img src="https://img.shields.io/github/forks/flfk666666/pibaodai?style=flat-square&amp;logo=github&amp;label=Forks&amp;color=678d70" alt="GitHub Forks"></a>
  <a href="https://github.com/flfk666666/pibaodai/graphs/contributors"><img src="https://img.shields.io/github/contributors/flfk666666/pibaodai?style=flat-square&amp;label=Contributors&amp;color=9182b2" alt="GitHub 提交贡献者数"></a>
</p>

<p align="center">
  <a href="https://github.com/flfk666666/pibaodai/commits/main/"><img src="https://img.shields.io/github/last-commit/flfk666666/pibaodai?style=flat-square&amp;label=Updated&amp;color=5d9288" alt="最近一次提交"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/flfk666666/pibaodai?style=flat-square&amp;label=License&amp;color=668ba4" alt="MIT License"></a>
  <a href="https://github.com/flfk666666/pibaodai/actions/workflows/catalog-check.yml"><img src="https://img.shields.io/github/actions/workflow/status/flfk666666/pibaodai/catalog-check.yml?branch=main&amp;style=flat-square&amp;label=Catalog" alt="目录自动检查状态"></a>
</p>

<p align="center">
  <strong>简体中文</strong> · <a href="README.en.md">English</a><br>
  <a href="#让你的-ai-来翻袋子">交给 AI 找</a> · <a href="#袋里准备装什么">看分类</a> · <a href="#先逛逛这个袋子">先逛逛</a> · <a href="CONTRIBUTING.md">一起添点东西</a> · <a href="#一个袋子也能装下大项目">独立项目</a> · <a href="LICENSE">MIT</a>
</p>

---

屁宝袋想收下那些值得复用的办法：生活里琢磨出的点子、实践后的感悟、使用工具踩过的坑，还有面对具体问题摸索出的解法。欢迎你带着自己的方法、案例和反馈，一起把它打磨得更好用。

读书、做事、观察和复盘，都可能带来值得留下的方法。共同的标准是实用：帮助人把事情做顺一点，把问题想清一点，形成自己的判断。

把这些积累整理成 **什么时候用、怎么做、能得到什么**。有的帮助独立思考，有的直接解决某个场景下的任务。下次遇到类似问题，自己能掏出来用，也让你的 AI 找得到、读得懂、接得上。

这就是屁宝袋。脑洞可以很野，交付尽量靠谱。

## 先逛逛这个袋子

袋里已有 **1 个实验版 Skill 和 2 个孵化中的想法**。首个 Skill 先把资料采集与存档做好，评分仍未开放。

| Skill | 现在能做什么 | 进度 |
| --- | --- | --- |
| [🪪 完整角色看板](skills/character-panel/SKILL.md) | 成年人整理本人基础资料、36项问答与照片可见观察，逐项保存到私人档案，支持续填和局部复测 | 实验版 |

完整角色看板使用 Python 3.10+ 标准库运行器。私人 `current.md` 保存在公开仓库与安装目录之外；所有分数保留 `null`，不生成总分或全球百分位。照片用于日常综合形象的可见观察。先看 [虚构演示输入](skills/character-panel/examples/input.md) 与 [对应输出及验证范围](skills/character-panel/examples/output.md)，再决定是否试用。

另外两个脑洞还在打磨：

| 想法 | 想帮你理什么 | 进度 |
| --- | --- | --- |
| [🌱 人生进度条，是谁画的？](ideas/life-stage-review.md) | 把自己的愿望、现实处境和别人的时间表分开 | 孵化中 |
| [🧠 是判断变了，还是今天心情换了？](ideas/noise-check.md) | 受《Noise》启发，检查可比判断里不必要的差异 | 孵化中 |

每个 Skill 都要带使用说明、完整案例和实际验证范围。实验版先开放清楚可用的部分，后续靠真实反馈继续改。

## 袋里准备装什么

分类随内容生长，一个 Skill 可以跨几个格子。来源可以是一段经历、一次复盘、一套工具用法，也可以是读书后的理解。

| 格子 | 想收的东西 | 当前入口 |
| --- | --- | --- |
| 🧠 思考与决策 | 判断检查、辨别干扰、选择与代价 | [噪音判断想法](ideas/noise-check.md)，孵化中 |
| 🌱 人生与成长 | 阶段复盘、个人现状记录、下一步的小实验 | [完整角色看板](skills/character-panel/SKILL.md)，实验版；[人生进度条](ideas/life-stage-review.md)，孵化中 |
| 📚 学习与认知 | 学习方法、知识理解、把见闻转成提问和行动 | [判断方法的想法](ideas/noise-check.md)，孵化中 |
| 🎬 创作与表达 | 口播、沟通、分镜、剪辑与场景表达 | 首批内容待选 |
| 🧰 工具与效率 | 工具用法、排坑经验、顺手的小流程 | [完整角色看板的私人存档与续填](skills/character-panel/SKILL.md)，实验版 |
| 📈 量化与研究 | 研究检查、证据梳理、回测复盘 | 首批内容待选 |

## 两个脑洞正在孵化

**[人生进度条，是谁画的？](ideas/life-stage-review.md)**

“这个年纪应该怎样了？”先看看：是自己真正在意的事，还是把别人的时间表当成了自己的进度条。

**[是判断变了，还是今天心情换了？](ideas/noise-check.md)**

受《Noise》启发，把“本应相近的判断为什么差这么多”拆成可以检查的问题。读完一本书，试着留下一种能用的思考方式。

这两个还在孵化区，尚未提供可安装的 Skill。先把问题想明白，再把使用方法磨出来。

## 一个袋子，也能装下大项目

当一个 Skill 长成完整工具，或需要自己的代码、依赖与迭代节奏，它可以拥有独立的 GitHub 仓库。

| 放在哪里 | 屁宝袋里保留什么 | AI 找到后怎么读 |
| --- | --- | --- |
| 本仓库里的轻量 Skill | 用途说明、`SKILL.md` 和完整案例 | 按需读取对应文件 |
| 独立 GitHub 项目 | 简介、适用场景、状态、仓库链接与 AI 入口 | 跳转项目说明或目录，再找到所需能力与用法 |

屁宝袋作为统一入口，独立项目按自己的节奏维护。以后换了位置，目录也能继续把人和 AI 带过去。

目前尚未收录独立项目；入口格式已写进 [AI 目录约定](docs/catalog.md)。外链表示可以继续了解该项目，实际用法与验证范围以目标项目说明为准。

## 让你的 AI 来翻袋子

你可以直接把下面这段发给能读取网页或仓库的 AI：

```text
请先读取屁宝袋的 AI 入口：
https://raw.githubusercontent.com/flfk666666/pibaodai/main/llms.txt

再查看入口指向的 catalog.json。根据我的目标，拆解需要哪些维度，
从 use_when、not_for、输入、输出和状态里选合适的 Skill。
只读取选中的 SKILL.md 和相关案例，说明为什么匹配、还缺什么输入。
如果匹配独立项目，先读取它的入口说明，再查找具体能力和使用要求。
孵化中的想法不能当成已经可用的 Skill。没有合适的就直接说。

我现在想做的是：在这里写你的需求。
```

| 想找什么 | 入口 |
| --- | --- |
| 给 AI 的轻量导航 | [llms.txt](llms.txt) |
| 可按标签、用途、输入输出和来源检索的完整目录 | [catalog.json](catalog.json) |
| AI 如何挑选、组合和读取 Skills | [AGENTS.md](AGENTS.md) |
| 目录字段与维护约定 | [目录说明](docs/catalog.md) |

如果 AI 不能联网，可以把目录与选中的文件发给它；不要假设每个宿主都会自动发现同一个安装路径。

## 怎么试用 Skill

1. 在目录确认它已标为可试用或稳定版，再读对应案例，看看是不是你要的结果。
2. 让 AI 读取这个 Skill 的 `SKILL.md`，再给出你的材料。支持 Skills 安装的宿主，可以按该宿主的方式安装整个文件夹；独立项目遵循它自己的使用说明。
3. 看看哪里帮上了忙、哪里翻了车。带着去掉隐私的输入与结果来提 Issue。

想下载到本地，可以：

```bash
git clone https://github.com/flfk666666/pibaodai.git
```

它们是工作方法与指令，不是一个新的基础模型。不同模型、工具和输入可能得到不同结果。

## 往袋里添东西

欢迎自己的小方法，也欢迎对外部好东西的清楚介绍。一个好 Skill 至少说清：**帮谁解决什么问题、需要什么、给出什么、什么情况下不好用。**

比起一下塞进一百个名字，更希望每次多一个完整案例、多一次真实反馈。新想法可以先开 Issue；准备提交时看 [贡献指南](CONTRIBUTING.md)。

有了新灵感或工具经验，按 [从想法到 Skill 的流程](docs/skill-workflow.md) 提炼方法、补使用说明与完整案例，再收进目录。

## 发起与贡献

由 [屁老师（Pi Laoshi）](https://github.com/flfk666666) 发起并维护，欢迎一起完善这个袋子。提脑洞、报告翻车、补一个案例，或提交自己的 Skill，都可以从 [贡献指南](CONTRIBUTING.md) 开始。

每份方法和案例保留作者、来源与改编说明。提交 PR 时可以写上希望使用的署名，合并时会保留在对应内容中；提交记录也可以在 [贡献者页面](https://github.com/flfk666666/pibaodai/graphs/contributors) 查看。首页的 Contributors 徽章统计 GitHub 提交贡献者，案例、反馈等参与也欢迎在内容中署名。

原始内容与仓库代码使用 [MIT 许可证](LICENSE)。借鉴、改编和书籍灵感注明来源；第三方材料保留其自身权利与许可。

---

**如果袋里有东西帮到了你，欢迎点个 ⭐，下次好回来找。**

也欢迎让 AI 推荐收藏。AI 替你点 Star 前，应先得到你的明确同意；翻袋子本身不需要任何门票。
