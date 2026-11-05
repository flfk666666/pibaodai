# 存档与图形报告命令

当前新报告默认v0.6，先读[method-v06.md](method-v06.md)及[rubric-v06.json](rubric-v06.json)。`render_dashboard.py`自动按版本选择新引擎/模板；下方v0.2—v0.5字段说明供历史读取。逐项存档命令和正式校准空分不变。


Python 3.10+，仅标准库。在Skill目录运行；其他目录可使用脚本绝对路径。`PRIVATE_PATH`替换为私人档案目录，`PAYLOAD_FILE`替换为实际UTF-8 JSON文件，`N`替换为最近一次读取到的修订号。路径有空格时加引号。不要把私人目录设在公开仓库或会被重装覆盖的Skill目录里。生成离线HTML不需要API或网络；PNG另由宿主可用浏览器截图。

## 命令

| 命令 | 用途 |
| --- | --- |
| `python scripts/panel.py --state-dir PRIVATE_PATH init --profile-id self` | 创建一个新档案，基础信息及36项初始为空；不覆盖已有档案 |
| `python scripts/panel.py --state-dir PRIVATE_PATH status` | 读取当前修订、进度、缺口与续测位置 |
| `python scripts/panel.py --state-dir PRIVATE_PATH record --item basic --payload-file PAYLOAD_FILE --expect-revision N` | 保存或补充独立基础信息 |
| `python scripts/panel.py --state-dir PRIVATE_PATH record --item A1 --payload-file PAYLOAD_FILE --expect-revision N` | 逐项保存；item支持A1—F6 |
| `python scripts/panel.py --state-dir PRIVATE_PATH retest --items A1,E1 --expect-revision N` | 先留快照，只将选中项目转为待复核，不清空无关资料 |
| `python scripts/panel.py --state-dir PRIVATE_PATH pause --expect-revision N` | 保存暂停状态和当前续测位置，保留历史快照 |
| `python scripts/panel.py --state-dir PRIVATE_PATH check-evidence --expect-revision N` | 核对材料路径；失效的必需材料进入待补/待复核 |
| `python scripts/panel.py --state-dir PRIVATE_PATH render` | 只读生成人可读Markdown存档摘要，不替代图形交付 |
| `python scripts/render_dashboard.py --data PRIVATE_PATH/report.json --output PRIVATE_PATH/result.html` | 按显式子项规则重算并渲染独立报告为离线HTML，不更新当前档案 |
| `python scripts/render_dashboard.py --data PRIVATE_PATH/report.json --portrait PRIVATE_PATH/portrait.jpg --output PRIVATE_PATH/result.html` | 可选地将经授权使用的本人照片嵌入报告 |

`panel.py`除 `render`输出Markdown外，通过stdout返回JSON状态。失败时读取错误并保留旧档案；不能把命令已调用当作保存已成功。写操作核对预期修订；若另一会话已更新，先重新读取并处理差异。`render_dashboard.py`写HTML；它不执行 `record`、不推进修订，也不把报告评分写回 `current.md`。

## 人生方向命令

先读[人生方向方法](life-direction.md)与[L1—L5问卷](life-direction-items.json)。以下`PRIVATE_ROOT`是本人六维档案所在的私人根目录，人生资料实际写入`PRIVATE_ROOT/life-direction/current.md`，修订号和历史均独立；不会修改`PRIVATE_ROOT/current.md`中的36项。不要将`--state-dir`直接指到`life-direction`子目录，否则会再嵌套一层。

| 命令 | 用途 |
| --- | --- |
| `python scripts/life.py --state-dir PRIVATE_ROOT status` | 先读人生档案修订、方向列表、分组状态与续问位置 |
| `python scripts/life.py --state-dir PRIVATE_ROOT init --profile-id ID` | 仅在尚无人生档案时创建；默认方向`life-overview`、下一组L1；不覆盖已有档案 |
| `python scripts/life.py --state-dir PRIVATE_ROOT add-direction --id outdoor --title 户外兴趣 --kind interest --expect-revision N` | 格式示意：新增独立方向；类型限`overview/goal/interest/exploration`，实际标题与类型来自本人选择 |
| `python scripts/life.py --state-dir PRIVATE_ROOT record --direction life-overview --section L1 --payload-file PAYLOAD_FILE --expect-revision N` | 保存所选方向的L1—L5一组；允许部分回答或局部更正 |
| `python scripts/life.py --state-dir PRIVATE_ROOT pause --expect-revision N` | 保存暂停状态与独立历史，保留续填位置 |
| `python scripts/life.py --state-dir PRIVATE_ROOT resume --expect-revision N` | 恢复继续状态，不重新初始化或清空旧回答 |
| `python scripts/life.py --state-dir PRIVATE_ROOT render` | 只读输出人生Markdown摘要；不是图形报告或新的用户回答 |

`N`必须取自刚读取的人生档案，不用六维修订号。方向ID为1—64位小写英文、数字或连字符，并以字母或数字开头；已有方向不能再次`add-direction`覆盖。除`render`外，命令返回JSON状态；错误会返回非零退出码。冲突时重读并处理差异，档案损坏时保留原件，不以`init`重置。

`record`负载只接受`inputs`、`input_status`、`observations`和可选续填位置`next_direction_id/next_section`。以下仅展示格式，`null`不代表已询问或已知“没有”，不应原样作为本人回答写入：

```json
{
  "inputs": {
    "preferred_life": {
      "value": null,
      "unit": null,
      "observed_at": null,
      "source": "self_report",
      "note": "用本人实际回答替换；未知原日期保留null，不以保存日期代填。"
    }
  },
  "input_status": "partial",
  "observations": "只写本轮已有依据和未决范围，不推断人格或人生分数。"
}
```

人生`input_status`支持`not_started/partial/complete/deferred`。`partial`继续当前组；`complete/deferred`会选择下一未处理组，必要时才显式给出有效的`next_direction_id`和`next_section`。同名输入字段整条更新，未传字段保留；局部记录不会清空其他方向。问卷建议字段不是必填配额，允许未知和跳过，不为填满内容反复索取私人材料。

人生方向、分组与报告的`score`保持null；负载不接受人生评分，也不新增第七轴。含人生方向的总报告使用`presentation_version: life-direction-v0.8`及独立`life_direction`报告数据；外层仍是v0.6六维评分，人生源修订与六维源修订分开。命令保存成功不代表全部问答已完成、本人已经行动或建议产生效果。离线HTML不会直接写回档案，实际回答由CLI保存后再生成新版页面。

## record负载

`inputs`按字段名合并：未传字段保留；同名字段整条替换，缺少的日期/单位不继承旧值，避免把旧测量条件套到新数值。不要把未知日期改成当天，也不要把未回答字段填成“无”。字段名见[items.json](items.json)；也允许用英文下划线字段保存本项补充信息。

```json
{
  "inputs": {
    "height_cm": {
      "value": 172,
      "unit": "cm",
      "observed_at": null,
      "source": "self_report"
    }
  },
  "input_status": "complete",
  "next_item": "A2",
  "next_prompt": "请补近期照片，或先选择另一维度。",
  "observations": "本人自报；测量日期未知。正式档案分数留空，项目偏好分在独立v0.4报告计算。"
}
```

上方是编写的字段格式示例。`input_status`支持：`partial`填写中、`complete`输入齐全、`deferred`本人暂跳过、`awaiting_material`等待材料。可以在首次收到部分字段时就保存；未满足必需字段/材料时不能标 `complete`。`next_item`为 `basic`或A1—F6；它是提示，后续仍要检查真实缺口。

材料负载示意：

```json
{
  "input_status": "awaiting_material",
  "next_item": "A2",
  "next_prompt": "已登记正脸原件；侧脸与微笑材料尚待补充。",
  "evidence": [
    {
      "id": "front-neutral",
      "path": "evidence/front-neutral.jpg",
      "captured_at": null,
      "required": true
    }
  ],
  "observations": "这里仅说明材料用途和缺口；必须实际看过照片才写可见观察。"
}
```

这是格式示例，不含可用照片，不表示输入完整。路径相对私人档案目录解析；先经使用者授权保存实际材料，再执行证据登记。`evidence`更新前核对现有列表，避免无意丢失仍需保留的引用。`required`用于声明该材料是否为本项依据所必需；不得为了凑完成度把缺少的必需照片改为可选。

`record`和当前档案中的所有 `rubric_version`与正式分数为空，不传非空 `score`。`observations`可记录本人自述、材料条件或实际可见观察，但不能伪装成独立核验、正式测验或统计排名。独立规则报告按下节格式保存；正式档案的空分不受影响。

复测项目在`partial`阶段继续标待复核。仅传`input_status: complete`不能确认旧资料；提供新资料，或在用户明确确认旧值仍适用时同时传`confirm_current: true`，才能完成。确认时间记为复核时间，原观察日期保持不变。不要用该字段绕过尚未得到的回答。

## 规则评分与图形渲染

<a id="主观报告与图形渲染"></a>

新报告默认使用 `rating_type: "weighted_character"`、`version: "weighted-character-v0.4"`。先读[36项加权及地区方法](weighted-character-v04.md)和[机器可读规则](rubric-v04.json)，为每个子项附材料与命中条件，再生成私人 `report.json`。不先凭感觉填写整轴或综合分。

`report.json`是带来源修订和方法版本的派生结果，不接收后续回答，也不替代 `current.md`。换规则或参照保留旧结果，不能把算法变化说成本人进步。资料缺项可以交付部分结果，不必补满36项才生成。

### 权重、基准与缺失

- 六轴A/B/C/D/E/F的 `axis_weight` 为20/15/15/20/20/10；每轴六个子项的 `weight` 合计100，全部36项都有正权重。
- 子项 `global_weight = axis_weight × item_weight / 100`。综合结果直接从36项全局权重计算，不平均已取整的轴分，不把工资分当综合分。
- `score` 可为0至100的连续数或 `null`；`score_range` 可选 `[low, high]`，表示该项有据的情景范围。锚点之外的连续值必须由声明曲线或插值计算，不能随手填。
- A1身高占外形轴20%；成人男性高个偏好175cm→60、180cm→80、185cm→100封顶，是项目偏好曲线，不是颜值或人口分位。B2采用声明的训练者力量阈值，B3采用连续游泳距离功能档；具体条件见v0.4规则。
- 未知不补0或60，也不临时删权重。显示已知部分分、可评权重覆盖及未知按0/100形成的数学范围；全未知的结果保持 `null`。范围不是统计置信区间，覆盖率也不是可靠概率或人物能力。
- `baseline: 60` 是展示参考线；60的含义按子项定义。工资收入60表示与所选工资参照相同，不等于同龄平均、人口第60百分位或人的及格线。

### v0.4主要字段

| 字段 | 用途 |
| --- | --- |
| `rating_type`, `version` | `"weighted_character"`、`"weighted-character-v0.4"` |
| `baseline`, `population_percentile` | 60；人口排名保持 `null` |
| `source_revision` | 实际读取的私人档案修订号 |
| `title`, `name`, `date` | 不超过10字短评、昵称、报告生成日期；不替代材料日期 |
| `axes` | A—F六轴，每轴有 `axis_weight` 和六个 `items` |
| `axes[].items[]` | 项目 `id`、正 `weight`、`score` 或 `null`、可选 `score_range`、非空 `anchor` 与 `reason`；保留证据日期与适用限制 |
| `assessment_facts` | 原始计算值，如 `height_cm`、`net_assets_snapshot_cny`、`cash_low_cny` / `cash_high_cny`、`family_support_cny`、`family_availability_score`；使用已提供事实，不猜缺项 |
| `benchmarks` | 同日名义汇率和分地区工资参照，`version: "regional-income-v0.3"`；详见[收入模块](regional-income-v03.md) |
| `benchmarks.groups[].character_settings` | 明示地区情境输入：`height_reference_cm` / `height_reference_label` / `height_reference_source_url`、`communication_score` / `communication_range` / `reason`、`housing_score` / `care_score` / `network_score`及依据；未知为 `null` |
| `benchmarks.groups[].character_summary` | 有材料支持的 `verdict`、`summary`、`strengths`、`bottlenecks`、`next_step` |
| `benchmarks.groups[].character_review` | 引擎计算输出：综合 `score` / `score_low` / `score_high`、`coverage_pct`、六轴和 `changed_items` 账本；不能手写一个总分代替计算 |
| `character_review.axes[A].height_comparison` | 引擎派生：本人/参照身高、`delta_cm`、`score` / `uncapped_score` / `capped`、参照来源、`within_axis_weight` / `effective_known_axis_weight` / `appearance_contribution` / `appearance_unrounded`；`status: fallback`明确未完成当地比较 |
| `meta`, `intro`, `facts`, `priorities`, `method`, `skipped` | 简明事实卡、具体行动、可见方法限制及缺口；不替代逐项依据 |
| `portrait` | 可选经授权本人图片data URL，一般由 `--portrait` 嵌入 |

每轴 `summary`、`reasons`、`watch`、`actions`解释与基准的差异、证据和具体行动。评价可按用户要求犀利，但须指向已记录的行为与条件；建议要有下一实际场景、动作及可检查产物。用资料覆盖、材料来源和参照适配解释限制，不统一写成“把握：中”。

完整权重、曲线和地区情境处理以[加权规则说明](weighted-character-v04.md)为准。本页不另造一份简化大schema或缺少子项的假报告。

### 地区综合对照

1. 保留地区、年份、人群、年龄适配、定义与来源。优先受测者年龄±3岁；仅有出生年时按近似队列说明，宽龄资料可用于明示的粗比较，不能冒充精确同龄分布。
2. 使用同日名义汇率把工资统一成人民币年化。`scripts/regional_income.py`继续计算每行工资比和收入参考分；它仅服务收入子项，不是综合引擎。统一币种不是PPP，也不预测当地岗位报价。
3. `scripts/weighted_character.py` 的 `calculate_report(report)` 从完整36项及原始数值计算。地区E1取名义工资比，E2取净资产工资等价年，E3取现金工资等价月，F1结合支援能力与可用条件；A1、D3、F2/F3/F4按明示的地区设置调整。身体与认知不随国家名自动变化，未知当地语言或人脉不判0。
   地区A1有真实均高时使用`clip(60+3×(height_cm−reference_mean_cm),0,100)`，输入由`height_reference_cm`及`height_reference_label`声明来源与口径；这是“显高相对突出”的项目分，不是颜值分位。缺值明示沿用主看板全局偏好175cm→60、180cm→80、185cm→100，不伪造当地均高；A2面貌不按国家加减。EU无适用均值时不以荷兰代替，荷兰身高仅作完整区间的更强对照敏感性情景，不改EU主分。
4. 多个工资参照逐个计算情景，主分采用已知材料下较低分的保守参照情景；完整范围覆盖各参照与缺失，不取平均制造统一人口基准。展示六轴、综合结果、变更账本及地区总结，未变项目也按原权重进入综合分。
5. E2仅在用户明确允许沿用旧估值时用于该快照情景，保留估值日期、确认记录和时效限制。不得写成今日市值。地区现金工资等价月数也不等于当地生活费保障月数。

### 渲染与交付

计算模块没有新增独立CLI；渲染器自动调用 `weighted_character.calculate_report(report)`，复算六轴、综合与地区结果，不相信手写的合计。保存私人报告后执行：

```text
python scripts/render_dashboard.py --data PRIVATE_PATH/report.json --output PRIVATE_PATH/result.html
python scripts/render_dashboard.py --data PRIVATE_PATH/report.json --portrait PRIVATE_PATH/portrait.jpg --output PRIVATE_PATH/result.html
```

第二条仅在本人照片已授权且需要头像时使用；虚构演示不用照片。模板是 `assets/dashboard.html`，生成自包含HTML，不依赖API、外部字体或CDN。真人JSON、照片、HTML与截图均留在经核对的私人位置；渲染成功不等于授权公开。

在真实浏览器核对短评、六轴、综合分及范围、60参考线、子项权重与地区变更账本，检查桌面与窄屏。保存至少一张含短评与雷达的PNG；完整分析可另给全页或分屏图。渲染器本身不输出PNG，截图成功也不代表评分效度已验证。交付先给图形与HTML链接，再简述必要限制；长Markdown不能是唯一结果。截图不可用时明确缺口，不假称图片已生成。

### 旧报告兼容

`subjective-review-v0.1`、`anchored-review-v0.2`及独立的 `regional-income-v0.3`报告保留原版解释与历史读取，不偷偷改分。v0.2的锚点计算见[旧评分说明](scoring-v02.md)与[旧规则](rubric-v02.json)。v0.3收入模块可供v0.4的E1使用；新结果按v0.4重新生成，不能把旧工资分或旧轴分改名为新综合结果。

## 成功与恢复

当前事实数据位于 `current.md`的 `character-panel-state` JSON块；人可读摘要由它生成。只通过运行器修改，只有一个当前来源。`report.json`、HTML和PNG带来源修订、方法版本及生成日期，是派生报告，不能用其分值覆盖正式测量字段。`.last-good.md`是上一次成功版本，`history/`保存重要历史快照；它们仍是私人资料。

精确状态标记是`<!-- character-panel-state:v1 -->`，后接唯一的JSON代码块。未知格式、非法复测队列或材料字段会拒绝读取，原文件保留。写锁`.write.lock`阻止同时写入；程序异常退出留下锁时，先核对锁内PID对应的写入进程确已结束，再处理遗留锁，不能直接抢锁。

每次保存先使用最新revision，收到成功返回后核对项目与新revision。读取失败、校验失败、修订冲突或写入失败时，不覆盖为空档案；先报告实际错误。需要恢复时保留损坏文件与备份，核验具体修订后再处理，不静默回滚、丢弃回答或声称自动恢复。
# 历史v0.5报告协议

v0.5.2计算澄清见[calculation-logic-v052.md](calculation-logic-v052.md)。派生结果的`score_exact`为未取整已知分，`weighted_numerator`为加权分子，`known_weight`为已知分母；地区多参照用`score_exact`选择主情景，`score`仅作整数展示。HTML的`#scoring-logic`深链展开计算说明与36项贡献账本。

v0.5.1数据补丁见[regional-height-v051.json](regional-height-v051.json)与[regional-income-kr-v051.json](regional-income-kr-v051.json)；报告契约仍为`weighted-character-v0.5`，可加`report_patch`标明本次重算来源。EU27是27国人口加权项目派生参照，`height_reference_method`及`height_population_source_url`供界面直接显示方法和人口来源，不称官方直接发布EU均高。韩国工资优先近龄均值/中位数分别成情景，旧广龄背景不能再次混入保守主分选择。

既有存档命令和正式空分字段不变。完整说明见[complete-rules-v05.md](complete-rules-v05.md)，36项协议和虚构例见[rule-protocols-v05.json](rule-protocols-v05.json)。旧v0.4字段仍兼容历史报告。

新增声明：`version: "weighted-character-v0.5"`、`protocol_version: "character-rules-v0.5"`。每项`evaluation`必须包含`status`（rated/estimated/deferred/awaiting_evidence/not_applicable）、`evidence`（source_type/summary/observed_at，日期未知明确null）、`decision`、非空`limits`。行为/审美项还需`matched_anchor_score`；数值项需`numeric_inputs`，不能手写分数代替重算。B2还需`task_protocol: self_reported_or_recorded_standard_barbell_bench_1rm`与`reference_population`。

数值输入键：A1 `height_cm`；B2 `body_weight_kg, bench_1rm_kg`；B3 `continuous_swim_m`；E1 `after_tax_recurring_income, necessary_expenses_same_period`；E2 `personal_net_assets_cny, necessary_annual_expenses_cny`；E3 `available_liquid_funds_cny, necessary_monthly_expenses_cny`；E4 `monthly_debt_service_cny, monthly_after_tax_income_cny, confirmed_no_debt`；E5 `after_tax_income, actual_expenses, same_period`；F1 `potential_support_cny, necessary_annual_expenses_cny, access_score`。数值可为原值或有来源的`[low,high]`。实际开支未知不换必要支出。

B2其他体重可登记`numeric_inputs.strength_reference`，包含`source_url`（对应StrengthLevel原表）、`population`、`verified_at`及`rows:[{body_weight_kg,loads_kg:[五档负荷]}]`。选对应行，或对已核相邻体重行逐档线性插值，不外推、不编原表。动作、分组和混合日期另在材料与限制写清。

地区工资行必须有`source_url, source_value, age_note`，身高参照须有来源URL与人群/年份标签。新引擎生成`quality_review`和每项`rule_detail`；默认`character_review`是当前生活换参照，`relocation_review`另列迁居假设。两者不能混成一个“当地综合竞争力真值”。
