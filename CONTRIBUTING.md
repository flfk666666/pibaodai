# 一起往袋里放点好东西 · Contributing

[中文首页](README.md) · [English home](README.en.md)

屁宝袋是实用 Skills 与独立思考的开源百宝袋，由屁老师发起，欢迎一起完善。生活观察、实践感悟、工具经验，以及特定场景下摸索出来的办法，都欢迎进入这个袋子。一个反复踩坑后总结的小招数，也值得有自己的位置。

## 先选一种参与方式

- **提个脑洞：** 开 Issue，说明遇到了什么问题、现在怎么解决、希望 Skill 帮上哪一步。
- **报告一次翻车：** 附上去掉隐私的输入、实际输出、你期望的结果，以及所用模型或工具。
- **补一个案例：** 展示输入与输出；说清是实测记录，还是为解释方法编写的示例。
- **提交 Skill：** 用一个真实、可重复的问题起步，附完整案例，再登记到目录里。

这四种方式任选一种，不需要先完成前面的步骤。

## 现在就能参与，需要什么权限？

仓库是公开的。登录 GitHub 后，就可以通过 [Issue 入口](https://github.com/flfk666666/pibaodai/issues/new/choose) 提脑洞、报告翻车，也可以先贴出一个去掉隐私的案例。

想直接改文件、补案例或提交 Skill，可以 [Fork 仓库](https://github.com/flfk666666/pibaodai/fork)，在自己的副本里修改，再向本仓库发起 Pull Request。维护者审阅后决定是否合并。普通参与者无需申请仓库写入权限，也不用先成为协作者。

还没写成 Skill 也没关系；按 [从想法到 Skill 的固定流程](docs/skill-workflow.md) 一起打磨。

## 一个 Skill 的最小交付

放在 `skills/<skill-id>/`，目录名使用小写英文、数字和连字符。

```text
skills/your-skill/
├── SKILL.md              # 名称、触发条件、关键做法与边界
└── examples/
    ├── input.md          # 用户真正会给什么
    └── output.md         # 对应输出，附示例性质与检查点
```

需要时再加 `references/`、`scripts/` 或 `assets/`。读一个词不该顺手安装半个互联网。

1. 在 `SKILL.md` frontmatter 中填写 `name` 与 `description`。描述应能帮助 AI 判断何时使用。
2. 写清输入、输出、关键判断步骤和容易误用的地方。
3. 提供一个别人可以照着理解或复现的案例。涉及工具时写明依赖和实际验证范围。
4. 按 [目录说明](docs/catalog.md) 登记 `catalog.json`，并更新中英文首页与 `llms.txt`。
5. 运行 `npm test` 和 `npm run check`。在 PR 中说明修改内容、案例来源和检查结果。

新 Skill 默认标为 `experimental`。`stable` 需要记录覆盖过的场景和已知失败情况；不能只靠文案变成熟。

## 较大的独立项目

如果方法已经长成一个有独立代码、依赖或发布节奏的项目，可以保留自己的 GitHub 仓库，在屁宝袋登记入口。提供项目简介、适用场景、状态、`repository_url`、供 AI 继续读取的 `entry_url`，以及验证范围。

按 [目录说明](docs/catalog.md) 使用 `kind: project`、`source: external`，并同步中英文首页与 `llms.txt`。外部项目在自身仓库维护使用说明和案例；不要把链接包装成已经安装、已经运行过的本地 Skill。

## 经验、借鉴与公开范围

- 把读书所得变成自己的提问方式、检查流程或练习，标明书名、作者和可靠来源。
- 引用别人的 Skill 时保留作者和原链接；改编还要说明你改了什么，以及原材料的许可。
- 提交方法、案例或反馈时，可以说明希望使用的署名；合并时把作者与来源保留在对应内容中。首页的 Contributors 徽章只统计 GitHub 提交贡献者，不代表全部参与方式。
- 保持示例去标识化。不要提交真实账户、密钥、完整私人日记、私密对话或持仓资料。
- 对个人成长给观察维度与选择空间，不把自创分数包装成心理测评。
- 对研究给证据、假设和验证方法，不承诺收益或伪造回测。

---

## Contribute in English

Bring a useful method from life experience, reflection, independent thinking, tool use, or a specific task. Worked examples and clear reports of what failed are welcome too. Reading can inspire a method, alongside other forms of experience.

PiBaoDai was started by Pi Laoshi and welcomes contributions. Include your preferred credit and sources with a method, example, or feedback; retain them in the relevant content when merged. The homepage Contributors badge counts GitHub commit contributors, not every kind of participation.

Choose any one way to contribute: suggest an idea, report a failure, add a worked example, or submit a skill. These are alternatives, not a required sequence.

Sign in to GitHub and [open an Issue](https://github.com/flfk666666/pibaodai/issues/new/choose). To change files, [fork the repository](https://github.com/flfk666666/pibaodai/fork), edit your copy, and open a pull request for the maintainer to review. Contributors do not need write access or collaborator status. See [the idea-to-skill workflow](docs/skill-workflow.md).

Each runnable skill lives in `skills/<skill-id>/` and contains a `SKILL.md` with `name` and `description` frontmatter, plus a complete input/output example. Add references, scripts, and assets only when the workflow needs them.

Explain what the skill needs, what it produces, when it helps, and when it should not be used. Mark examples as either redacted real runs or authored illustrations. For tool workflows, name the dependencies and the extent of actual verification.

Register the skill in `catalog.json`, then update both READMEs and `llms.txt`. See [the catalog contract](docs/catalog.md). Run `npm test` and `npm run check`, and include the results in your pull request.

A larger project can stay in its own GitHub repository. Register it as `kind: project`, `source: external`, with a summary, use cases, status, `repository_url`, `entry_url`, and verification scope. Keep its full instructions and examples in its own repository. A directory link does not imply that a project has been installed or tested locally.

New skills start as `experimental`. Promote a skill to `stable` only with documented usage evidence and known limitations. Attribute books and upstream work, respect their permissions, and keep private material out of the repository.
