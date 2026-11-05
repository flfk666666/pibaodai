---
name: character-panel
description: Use for adult self-assessment character dashboards, 角色看板、个人六维档案、六轴评分/雷达、地区对照、人生方向、生活取向与行动轨迹、断点续测或局部复测. Save dated evidence privately; deliver six-axis scores and offline HTML/PNG plus an independently saved, unscored life-direction interview. Separate performance, evidence coverage, aspirations and actual actions; ask neutral follow-ups only when needed.
---

# 角色看板 / Character Panel

默认评分为`weighted-character-v0.6`、规则`character-rules-v0.6`；含人生方向的新报告采用`presentation_version: life-direction-v0.8`，仅六维联合报告仍支持`joint-profile-v0.7`。先读[v0.6评分方法](references/method-v06.md)、[rubric-v06.json](references/rubric-v06.json)对应项及[v0.7联合方法](references/joint-profile-v07.md)；人生方向读[独立方法](references/life-direction.md)，生成提升建议前读[现实提升与评测维护](references/improvement-actions.md)。保留明确六维评分、10字内短评、图形与每轴依据/动作；人生方向不评分、不设第七轴。材料不足和能力不足分开，不因简略回答或尚在探索判低。

## 输入与交付

- 本人、成年人；基础资料、实际经历、测量和经授权使用的照片。保留原观察日期，不把保存日期当新测量。
- 私人事实档案`current.md`、历史与材料；公开包只放通用方法/代码和明确标注的虚构案例。
- 人生方向另存`PRIVATE_ROOT/life-direction/current.md`，有独立修订和历史；L1—L5整理生活偏爱、形成轨迹、实际行动、障碍调整与反馈。亲密关系、生活方式和意义探索同样适用，不限职业或工作项目。
- 用户结果必须有精美离线HTML与PNG：首屏短评+六维数字/雷达；每轴给具体分析、可执行动作、36项账本；地区有完整六维参考分和身体/真实财务容量/资源及迁居适配坐标。
- 新报告采用`recommendation_protocol: real-life-improvement-v1`，六轴分别提供`improvement_plan`与`assessment_maintenance`。主要建议改变现实能力、状态或资源可调用性；补资料、续问、更新估值和留测量照片放评测维护，不充当自我提升。
- Python标准库处理存档、计算和HTML；截图由宿主浏览器完成。默认不需要API或账号。

## 先读取已有私人档案

1. 取得明确的本人私人存档路径；先核Git忽略/跟踪边界。不要把真人文件存在公共仓库或Skill安装目录，也不扫描整台电脑。
2. 用`python scripts/panel.py --state-dir PRIVATE_PATH status`读取。不存在才`init --profile-id ID`，格式损坏保留原件，不能初始化覆盖。
3. 展示已填/未决、上次位置，复核已有跨题材料，不重问已答或明确暂缺的内容。`PRIVATE_PATH`与`ID`须替换为真实参数。

## 先保存，再继续

每个有效回答或跳过用UTF-8 JSON负载执行：

```text
python scripts/panel.py --state-dir PRIVATE_PATH record --item ITEM_ID --payload-file PAYLOAD_FILE --expect-revision N
```

负载使用`inputs`内`value/unit/observed_at/source`、`input_status`、`next_item/next_prompt`；格式和已有命令见[CLI](references/cli.md)。`N`用刚读修订；写入失败不能声称已保存，冲突先重读。不把派生报告分值写入事实档案的正式校准`score`，这些字段继续null。真实回答可以自报，不要求账户截图或公司敏感原件换高分。

## 评分与追问

1. 先看本项究竟评什么，再读取已有事实和图像。图像只能评可见呈现，不推智力、人格、财富、精确体脂或疾病。
2. 行为/形象依据内容选0/25/50/75/100；数值用原值重算。六轴和轴内六项都以1个权重单位等权归一，是默认产品选择，不是科学唯一比例。
3. 每项报告带`evaluation`与`coverage`：表现理由及实际材料独立于范围/来源/未测内容。覆盖不乘分、答题/照片数量不加分；没有材料不填默认50、60或75。
4. **已有积极高分线索＋一个关键条件未明＋答案可能改变判断时，问一个中立的区别问题。**允许反例、失败、未知或跳过。没有明显高分迹象就继续，保留“更高要求尚未观察”，不下能力上限结论。
5. 不因说得不全面支持低档；低档需要明确困难/失效事实。相邻档未决可带候选范围、`range_reason`和待问问题；不填区间中点，也不对所有人默认上界100。具体自报可以正常支持表现判断。
6. A3可按可见轮廓评分并注明未见部位，不能因没有完整站姿否定已有上身材料。B1不借卧推加分；B3是具体游泳任务，C2未测数量不压逻辑，C3按风险/领域核验，E6不强制副业或失业经历。F1不可调用不能靠额度补偿。

## 构建v0.6报告

报告使用`rating_type: weighted_character`、`version: weighted-character-v0.6`、`protocol_version: character-rules-v0.6`、`source_revision`和六轴A-F各六项。每项：

- 行为`selected_anchor`或null；数值`numeric_inputs`保存原值/区间。
- `evaluation`: `status`为rated/provisional/missing，`reason`和实际`evidence`（source_type/summary/observed_at，日期未知null）。
- `coverage`: level为limited/usable/broad、scope、gaps数组、higher_unassessed布尔；三档只解释材料，不是评分乘数。
- 可选`score_range`、具体`range_reason`、`followup`积极线索/问题/状态。局部未决可以没有代表分，但保留实际支持的范围；无材料不能缩窄范围。

调用`from review_v06 import calculate_report`重算；六维联合报告使用`presentation_version: joint-profile-v0.7`，包含人生方向时使用`life-direction-v0.8`并按[人生方法](references/life-direction.md#页面协议)附加`life_direction`，然后执行：

```text
python scripts/render_dashboard.py --data REPORT_JSON --output REPORT_HTML
```

需要本人授权肖像时添加`--portrait LOCAL_IMAGE`；不嵌图则省略。v0.7呈现自动选`assets/dashboard-v07.html`，renderer依次重算v0.6、附加`joint_assessment`，有`financial_facts`时再算`financial_context`；不改36项数值、权重或轴分。页面先呈现短评、六维图形和联合判断，再展开条件、瓶颈、未决与账本。地区A1突出/E1工资坐标在`contextual_references`另列，不能替换本人形象偏好或实际财务联合口径。资金分所有权/可用性/用途去重；3/6/12月为诊断窗口，住房为明确假设演算。完整规则、字段与可运行虚构演示见[v0.7方法](references/joint-profile-v07.md)。未设该呈现版本的v0.6继续选原模板。所有真人JSON、HTML、图片和中间文件留私人目录。既有虚构输入见[review-v06.json](examples/review-v06.json)与[结果](examples/review-v06-output.md)。

## 人生方向：先读，再逐组保存

1. 用`python scripts/life.py --state-dir PRIVATE_ROOT status`读取独立人生档案；确实不存在才用`init --profile-id ID`。`PRIVATE_ROOT`与本人六维目录一致，实际写入其`life-direction/`子目录，不修改原36项。修订冲突或格式损坏时保留原件，不能初始化覆盖。
2. 先复用已有材料及原日期。按[问卷](references/life-direction-items.json)每次推进一组：L1生活取向/偏爱与理由，L2形成与轨迹，L3计划/实际行动，L4障碍/调整，L5反馈/归因与继续、调整、停止条件。历史目标不能自动确认成今天优先；形成日期、首次行动日和保存日分别记录。
3. 允许`overview / goal / interest / exploration`四类方向。初始化自带`life-overview`；新增方向用`add-direction`，每次回答用`record --direction ID --section L1 --payload-file PAYLOAD_FILE --expect-revision N`。`N`是刚读取的人生修订号，不是六维修订号。局部补充只重写所选方向和分组；暂停/继续用`pause`、`resume`。
4. 方向、组与报告的`score`均为null；不用忙碌、坚持久、结果好或字段齐全代替目标感/自律。未知、合理休息、停止或转向不判低。需要时依据已有六维条件提出目标建议，但不改原权重、分数，也不把兴趣自动升级为行动承诺。
5. `life-direction-v0.8`使用`assets/dashboard-v08.html`，保留六维图形，增加人生方向文字观察和下一问。顶层`source_revision`仍引用六维档案；`life_direction.source_revision`引用独立人生档案。HTML不直接保存回答，实际聊天回答由CLI逐组保存，重新生成时核对源修订。完整命令和负载见[CLI人生方向段](references/cli.md#人生方向命令)。

## 把自我提升与评测维护分开

新报告在顶层声明`recommendation_protocol: real-life-improvement-v1`，每个A–F轴填写：

- `improvement_plan`: `title / target_items / current_gap / target / standard_basis / steps / success / sources`；`target_items`仅引用本轴六项，`sources`中的URL仅用HTTPS。
- `assessment_maintenance`: 字符串数组，可为空。只保存影响评阅准确性的资料、日期、口径或复测提示，尊重用户已跳过的项目。

先用已有事实找真实制约，再给“目标行为→具体动作→生活中的验收”。高分维度可以巩固或迁移优势；未测范围不能写成短板。不为填齐六轴虚构问题，也不强制增高、额外社交、学外语、开副业或购买服务。根据本人已选目标给最小有用动作。

验收看现实任务、状态或资源是否改变，不看是否多答题、补照片、更新档案或得到更高分。练习周期与次数只是可调整建议，不是评分或医学门槛；完成建议不保证升分。健康、财务等建议按风险核验一手来源，来源支持具体建议，不为本项目分数背书。

旧`actions`保留为历史兼容字段；声明新协议的报告不得以`actions`替代六轴的结构化提升计划，也不把旧动作原样复制后改名。完整字段、坏例与改写、边界及[虚构F3片段](examples/improvement-actions-fictional.json)见[improvement-actions.md](references/improvement-actions.md)。

## 地区比较

读取现有[身高参照](references/regional-height-v051.json)与[韩国工资](references/regional-income-kr-v051.json)，新增或更新参照查一手来源。年龄±3优先，近出生队列/宽年龄/年份/统计人群分别明示，不以一国代替全欧。

地区完整六维参考分只变有明示依据/曲线的项；A1身高突出坐标，E1名义收入坐标。E2/E3/F1按真实开支容量和调用条件，不再除当地工资重复变分。另列身高厘米差/真实可用分布、现金实际月数、资产日期、住房照护协作，以及迁居工作语言/岗位资格/报价的未决条件。无当地常模的任务分保持，不凭国名改思考、身体或面貌；同分不表示人口位置相同。

同日换币只统一货币单位，不是PPP。均值/均值置信区间不能当个体分布或标准差；有真实分位表只显示可核的区间，不编精确排名。地区情境合成不是完整当地竞争排名或就业概率。

## 核对与续测

- 实际核对36项内容、数值、权重、候选范围、追问和地区变更；在浏览器检查桌面/手机、短评/六轴/账本/切换和图片，至少导出首屏PNG。
- 说明分数与材料范围、已知归一与完整范围的不同分母；软件测试不等于人群校准或用户体验已验收。旧版审计见[model-audit-v053](references/model-audit-v053.md)，新修订不删除旧报告。
- 用户继续、暂停或局部复测时先读最新事实修订；命令`retest --items A1,E1 --expect-revision N`只重测所选项；`pause`保存位置。没有用户调度要求不创建后台定时任务。
- 方法改变另存新报告，原观察日期、历史资产估值和用户明确暂缓项不自动更新；新回答只重评依赖项。

适用于成年人本人的角色整理，不用于秘密评估他人、招聘/信贷资格、医疗心理诊断、智商或人生价值排名。可选均衡合成不能让关键资格缺口被身高或资产抵消。
