# 存档运行器命令

Python 3.10+，仅标准库。在Skill目录运行；其他目录可使用脚本绝对路径。`PRIVATE_PATH`替换为私人档案目录，`PAYLOAD_FILE`替换为实际UTF-8 JSON文件，`N`替换为最近一次读取到的修订号。路径有空格时加引号。不要把私人目录设在公开仓库或会被重装覆盖的Skill目录里。

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
| `python scripts/panel.py --state-dir PRIVATE_PATH render` | 只读生成人可读Markdown报告 |

除 `render`输出Markdown外，命令通过stdout返回JSON状态。失败时读取错误并保留旧档案；不能把命令已调用当作保存已成功。写操作核对预期修订；若另一会话已更新，先重新读取并处理差异。

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
  "observations": "本人自报；测量日期未知，尚无审美评分规则。"
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

首版所有 `rubric_version`和分数为空，不传非空 `score`。`observations`可记录本人自述、材料条件或实际可见观察，但不能伪装成独立核验、正式测验或统计排名。

复测项目在`partial`阶段继续标待复核。仅传`input_status: complete`不能确认旧资料；提供新资料，或在用户明确确认旧值仍适用时同时传`confirm_current: true`，才能完成。确认时间记为复核时间，原观察日期保持不变。不要用该字段绕过尚未得到的回答。

## 成功与恢复

当前数据位于 `current.md`的 `character-panel-state` JSON块；人可读摘要由它生成。只通过运行器修改，只有一个当前来源。`.last-good.md`是上一次成功版本，`history/`保存重要历史快照；它们仍是私人资料。

精确状态标记是`<!-- character-panel-state:v1 -->`，后接唯一的JSON代码块。未知格式、非法复测队列或材料字段会拒绝读取，原文件保留。写锁`.write.lock`阻止同时写入；程序异常退出留下锁时，先核对锁内PID对应的写入进程确已结束，再处理遗留锁，不能直接抢锁。

每次保存先使用最新revision，收到成功返回后核对项目与新revision。读取失败、校验失败、修订冲突或写入失败时，不覆盖为空档案；先报告实际错误。需要恢复时保留损坏文件与备份，核验具体修订后再处理，不静默回滚、丢弃回答或声称自动恢复。
