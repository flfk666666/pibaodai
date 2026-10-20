# 从一个想法，到一个能用的 Skill

[中文首页](../README.md) · [English home](../README.en.md) · [贡献指南](../CONTRIBUTING.md)

生活里的灵感、实践后的感悟、工具经验和具体问题的解法，都可以从这里起步。先把有用的部分找出来，再给它一个别人和 AI 都能接着用的形式。

## 你可以这样开头

把材料交给维护者或 AI 助手时，直接说：

```text
帮我把这个经验收进屁宝袋。
我遇到的问题是：……
我现在的做法或想法是：……
我希望它能帮别人：……
已有的输入、结果和工具版本：……（没有就直说）
这次材料属于：实际用过 / 还只是想法。
```

不需要一次填齐。先说你最在意的问题，缺少的关键材料再补。

## 固定流程

1. **提炼问题。** 说清帮谁、在什么场景下解决什么问题，需要哪些输入，预期交付什么。先查现有目录，有相近方法就完善它。
2. **选择形态。** 只有灵感、缺少操作方法的，放进 `ideas/`，标为 `incubating`。已有明确步骤、边界与完整案例的，整理为 `skills/<skill-id>/`，默认 `experimental`。已有独立仓库的大工具，按 [目录约定](catalog.md) 登记外部项目入口。
3. **写使用说明。** 在 `SKILL.md` 写明什么时候用、不适合什么、需要准备什么、关键步骤、预期输出、工具依赖和失败后的处理。安装方法以宿主和工具的实际要求为准。
4. **补一个完整案例。** 提供对应的 `examples/input.md` 与 `examples/output.md`，标明案例性质、背景、操作过程、结果和检查点，让读者能看懂方法如何起作用。
5. **整理公开版本。** 把私人经历提炼为可复用的方法，去掉身份、账户、密钥和第三方隐私；保留借鉴来源。使用编写的示例可以解释方法，实际效果还需要实践检验。
6. **登记与检查。** 更新 `catalog.json`、中英文首页和 `llms.txt`。运行 `npm test` 与 `npm run check`，检查链接、案例一致性和实际工具验证范围。
7. **发布与迭代。** 贡献者通过 PR 提交，由维护者审阅合并。维护者委托 AI 发布时，AI 在已授权的范围内提交、推送，并核对远端结果。记录后续反馈，再决定如何改进或升级状态。

## 完整案例要交代什么？

| 部分 | 应该写清 |
| --- | --- |
| 案例性质 | 去隐私的实测记录，或为解释方法编写的示例 |
| 背景与输入 | 原问题、目标、约束，以及对应的完整输入 |
| 操作过程 | 如何使用该方法；有工具时写版本、命令或关键操作 |
| 对应输出 | 一份与输入配套的完整结果；大文件可在案例中链接 |
| 检查点 | 怎样判断结果是否满足目标，哪里仍需人判断 |
| 验证范围 | 实际执行过什么、哪些步骤只是演示、已知失败情况 |

没有实测材料时，可以制作明确标注的演示案例；不能写成“亲测有效”。`stable` 需要有记录的实际使用证据和已知边界。首批公开 Skills 仍由维护者后续选择，这份流程说明本身不算一个已上架的 Skill。

## Idea-to-skill workflow

Bring an idea, reflection, tool experience, or a solution to a concrete problem. Explain the problem, your current approach, the intended result, and any real inputs or outputs you have. Missing evidence is fine; label it clearly.

1. Define the user, situation, inputs, outputs, and boundaries. Check the existing catalog before adding a duplicate.
2. Keep an early idea as `incubating` in `ideas/`. Package an actionable method with a complete example under `skills/<skill-id>/`, initially `experimental`. Link larger independent repositories using the [catalog contract](catalog.md).
3. Write usage instructions in `SKILL.md`: when it helps, when it does not, prerequisites, steps, expected output, dependencies, and failure handling.
4. Include paired `examples/input.md` and `examples/output.md`. State the context, steps, result, checkpoints, and verification scope. Label the case as a redacted real run or an authored illustration.
5. Remove private details, retain attribution, update the catalog and bilingual entry points, then run `npm test` and `npm run check`.
6. Submit a pull request for review. An AI acting for the maintainer may publish within the user's authorization and must verify the remote result. Improve the method with actual feedback; reserve `stable` for documented use evidence and known limitations.

This document describes the maintenance process. It is not a published runnable skill and does not select the first three skills.
