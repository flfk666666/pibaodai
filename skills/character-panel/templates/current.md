# 当前角色档案：格式说明

这是空白格式说明，不是实际测算结果。请用运行器 `init` 创建含基础信息和全部36项的私人 `current.md`；不要把此文件当成已有存档，不要把私人档案放进公开 Skill 目录。

运行器生成的文件包含人可读摘要和一个标识为 `character-panel-state` 的JSON代码块。该代码块是唯一当前数据；摘要由它生成，不能另建一份手工维护的JSON来竞争。具体字段以运行器生成的档案为准。

空值含义示意：

```json
{
  "profile_id": "example-format-only",
  "revision": 0,
  "items": {
    "A1": {
      "inputs": {},
      "input_status": "not_started",
      "score": null,
      "rubric_version": null
    }
  }
}
```

上方只是字段片段，不是可直接导入的完整状态；实际档案必须由当前版本运行器创建。`null`表示未知或尚无规则，不是0、50，也不是已完成评价。观察日期与保存时间各自保留。存档续测前先运行 `status`，再使用其当前修订号记录下一份回答。
