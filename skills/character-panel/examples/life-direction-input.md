# 人生方向案例输入：每月一份家庭照片册

**案例性质：编写的虚构成年人输入。**档案标识为 `fictional-album`，方向为“每月整理一份家庭照片册”，生活愿望是“与家人更有联系感”。人物、经历和回答均为演示而编写，不是用户访谈、产品背书或真实成效记录。

这个案例演示：总览与具体方向分别保存；L2 只填一半便暂停，恢复后接着填；完成 L1–L5 后发现 L3 说得不准确，只更正 L3，旧说法保留在历史。形成和首次行动的确切日期都不知道，保存为 `null`，不能拿 CLI 运行日期补上。

| 组 | 虚构回答要点 |
| --- | --- |
| L1 方向与偏爱 | 想与家人更有联系感，喜欢整理有故事的照片。先做每月10—15张的小册，不追求商业摄影或精致大作 |
| L2 形成与轨迹 | 形成时间记不清，第一次实际行动是建月份文件夹。曾想做一年总册而迟迟没开始，后来缩成每月一份；两个确切日期均未知 |
| L3 计划与实际 | 计划选片、写故事并做小册；实际整理8张、写2条自己的回忆，尚未请家人核实。先误记“8页草稿”，后来更正为“6页，尚未导出PDF” |
| L4 障碍与调整 | 选片追求完美导致拖延；改成只看一个月份、不反复改封面。一次家务打断后再接着做，但没有长期稳定记录 |
| L5 反馈与下一步 | 家人还没看过，效果未知；先用样张验证兴趣，再决定继续、缩小范围或暂停。不能由一份草稿认定自律已经很强 |

## 准备隔离的私人演示目录

以下命令从本 Skill 根目录运行。`PRIVATE_ROOT` 须替换为公开仓库和 Skill 安装目录之外的**新建私人演示子目录**；不要指向本人现有档案。此案例会同时建立一个空白六维父档，只用于核对它在后续人生方向操作中没有变化。

```powershell
$PRIVATE_ROOT = 'YOUR_PRIVATE_ROOT'
```

先运行下面这段 Python，写入完整虚构负载。`observed_at` 均保留未知；`source` 明确标为编写案例。建议字段无需填满，`complete` 只是本轮输入进度。

```python
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
payload_dir = root / 'payloads'
payload_dir.mkdir(parents=True, exist_ok=False)

def fact(value, note=None):
    data = {'value': value, 'observed_at': None,
            'source': 'authored_fictional_case'}
    if note is not None:
        data['note'] = note
    return data

payloads = {
    'overview-l1.json': {
        'input_status': 'complete',
        'inputs': {
            'preferred_life': fact('希望与家人更有联系感，不只在群里转发消息。'),
            'current_direction': fact('尝试每月整理一份家庭照片册。'),
            'priority_tradeoff': fact('先做小规模生活项目，暂不扩成商业摄影。')
        }
    },
    'album-l1.json': {
        'input_status': 'complete',
        'inputs': {
            'current_direction': fact('每月整理10—15张照片的小册，邀请家人补充故事。'),
            'preference': fact('喜欢有故事的照片，愿意先整理自己手头的材料。'),
            'reason': fact('想有一个具体方式了解家人的生活。'),
            'priority_tradeoff': fact('先做可看的小册，不先学复杂排版，不追求完美封面。')
        }
    },
    'album-l2-partial.json': {
        'input_status': 'partial',
        'inputs': {
            'formed_at': fact(None, '形成想法的具体日期记不清；不按本轮保存日期补写。')
        },
        'observations': '这一组暂时只答到这里，先暂停。'
    },
    'album-l2-complete.json': {
        'input_status': 'complete',
        'inputs': {
            'first_action_at': fact(None, '第一次行动的确切日期也记不清。'),
            'first_action': fact('建月份文件夹，把手机里的一批照片集中起来。'),
            'episodes': fact(['曾想做一年总册，范围太大而没有开始。',
                              '改成每月一份，先试一份小册。'])
        },
        'observations': '恢复后补完本组可回忆的内容；两个事件日期继续未知。'
    },
    'album-l3.json': {
        'input_status': 'complete',
        'inputs': {
            'period': fact('虚构的最近两周；起止日期未知。'),
            'planned_actions': fact('选10—15张，写简短故事，做一份可阅读的小册。'),
            'actual_actions': fact('整理8张照片，写2条自己记得的故事，建立草稿；尚未请家人核实。'),
            'outputs': fact('已完成8页草稿。', '这是稍后要局部更正的原说法。'),
            'results': fact('目前只有草稿，家人尚未看过，联系感是否改善未验证。')
        }
    },
    'album-l4.json': {
        'input_status': 'complete',
        'inputs': {
            'obstacle': fact('旧照片太多，挑选时想做到完美而拖延。'),
            'adjustment': fact('一次只看一个月份，先选10张，不反复返工封面。'),
            'interruption': fact('一次晚间安排被家务打断。'),
            'restart': fact('之后又接着补了草稿，但没有长期重复记录。'),
            'costs': fact('暂未记录明显额外代价；不是已经证明完全没有代价。')
        }
    },
    'album-l5.json': {
        'input_status': 'complete',
        'inputs': {
            'feedback': fact('尚无真实家人反馈；目前只能看草稿和本人意愿。'),
            'attribution': fact('缩小范围帮助开始；还不能断定能月月做，家人是否有空也会影响结果。'),
            'continue_condition': fact('本月能交付小册且家人愿意看，下月再试。'),
            'adjust_condition': fact('连续两次卡在选片，就把一份缩成5张。'),
            'stop_condition': fact('若持续影响休息，或本人不再觉得值得，就暂停复核。'),
            'next_experiment': fact('下一次先选5张发样张，询问家人是否愿意补故事。', '未来计划，不能冒充已经做过。')
        }
    },
    'album-l3-correction.json': {
        'input_status': 'complete',
        'inputs': {
            'outputs': fact('已整理8张照片，实际只完成6页草稿，尚未导出PDF。',
                            '更正先前“8页草稿”的说法；旧说法保留在历史中。')
        }
    }
}
for name, payload in payloads.items():
    (payload_dir / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
```

可以把这段保存为演示目录之外的临时 `prepare-album.py`，再运行 `python prepare-album.py "$PRIVATE_ROOT"`；也可以用支持标准输入的宿主执行，传入同一个目录。它不创建或改写六维档案。

## 按修订执行 CLI

每条写命令都用刚读到的修订；下面的编号只适用于这一份全新演示档。已有档案应先 `status`，不能照抄修订号覆盖。

```powershell
# 先建立结构完整的空白六维父档，记下原文件哈希。
python scripts/panel.py --state-dir "$PRIVATE_ROOT" init --profile-id fictional-album
$before = (Get-FileHash -Algorithm SHA256 -LiteralPath "$PRIVATE_ROOT/current.md").Hash

# 人生方向独立修订，从1开始。
python scripts/life.py --state-dir "$PRIVATE_ROOT" init --profile-id fictional-album
python scripts/life.py --state-dir "$PRIVATE_ROOT" record --direction life-overview --section L1 --payload-file "$PRIVATE_ROOT/payloads/overview-l1.json" --expect-revision 1
python scripts/life.py --state-dir "$PRIVATE_ROOT" add-direction --id family-album --title "每月家庭照片册" --kind goal --expect-revision 2
python scripts/life.py --state-dir "$PRIVATE_ROOT" record --direction family-album --section L1 --payload-file "$PRIVATE_ROOT/payloads/album-l1.json" --expect-revision 3
python scripts/life.py --state-dir "$PRIVATE_ROOT" record --direction family-album --section L2 --payload-file "$PRIVATE_ROOT/payloads/album-l2-partial.json" --expect-revision 4
python scripts/life.py --state-dir "$PRIVATE_ROOT" pause --expect-revision 5
python scripts/life.py --state-dir "$PRIVATE_ROOT" status
python scripts/life.py --state-dir "$PRIVATE_ROOT" resume --expect-revision 6
python scripts/life.py --state-dir "$PRIVATE_ROOT" record --direction family-album --section L2 --payload-file "$PRIVATE_ROOT/payloads/album-l2-complete.json" --expect-revision 7
python scripts/life.py --state-dir "$PRIVATE_ROOT" record --direction family-album --section L3 --payload-file "$PRIVATE_ROOT/payloads/album-l3.json" --expect-revision 8
python scripts/life.py --state-dir "$PRIVATE_ROOT" record --direction family-album --section L4 --payload-file "$PRIVATE_ROOT/payloads/album-l4.json" --expect-revision 9
python scripts/life.py --state-dir "$PRIVATE_ROOT" record --direction family-album --section L5 --payload-file "$PRIVATE_ROOT/payloads/album-l5.json" --expect-revision 10

# 只更正L3的outputs；其他字段与其他组保持原值。
python scripts/life.py --state-dir "$PRIVATE_ROOT" record --direction family-album --section L3 --payload-file "$PRIVATE_ROOT/payloads/album-l3-correction.json" --expect-revision 11
python scripts/life.py --state-dir "$PRIVATE_ROOT" status
python scripts/life.py --state-dir "$PRIVATE_ROOT" render

# 应为True：人生方向没有改动父级六维current.md。
((Get-FileHash -Algorithm SHA256 -LiteralPath "$PRIVATE_ROOT/current.md").Hash -eq $before)
```

人生方向写入 `PRIVATE_ROOT/life-direction/current.md`；过去修订位于其 `history` 子目录。`pause/resume` 只保存状态与修订，不刷新事实的 `observed_at`。`render` 输出当前 Markdown，不代表生成了新事实或改变了修订。

本轮实际运行结果与验证边界见 [案例输出](life-direction-output.md)。
