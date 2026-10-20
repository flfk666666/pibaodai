"""Run the authored example in an explicitly chosen PRIVATE output directory."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from panel_store import Store, summary  # noqa: E402


def fact(value, unit=None, observed_at=None):
    return {"value": value, "unit": unit, "observed_at": observed_at, "source": "authored_example"}


def main():
    parser = argparse.ArgumentParser(description="虚构资料演示；输出目录必须在公开仓库之外。")
    parser.add_argument("--state-dir", required=True)
    args = parser.parse_args()
    store = Store(args.state_dir)
    trace = []

    def capture(action, state):
        trace.append({"action": action, "revision": state["revision"], "status": state["assessment_status"],
                      "next_item": state["next_item"], "summary": summary(state)})
        return state

    state = capture("init", store.init("authored-example"))
    state = capture("basic", store.record("basic", {"inputs": {
        "is_self_assessment": fact(True), "adult_confirmation": fact(True),
        "birth_year": fact(1994, "year"), "current_city": fact("苏州"),
        "occupation": fact("工业产品设计"), "display_name": fact("小禾")},
        "input_status": "complete", "next_item": "A1"}, state["revision"]))
    state = capture("A1 initial", store.record("A1", {"inputs": {"height_cm": fact(172, "cm")},
        "input_status": "complete", "next_item": "D1"}, state["revision"]))
    state = capture("D1 draft", store.record("D1", {"inputs": {
        "domain": fact("家用产品结构设计"), "work_case": fact("最近做过一个便携收纳盒，贡献与验证待补。")},
        "input_status": "partial", "next_item": "D1", "next_prompt": "请补本人贡献、他人贡献和实际验证。"}, state["revision"]))
    state = capture("pause", store.pause(state["revision"]))
    # New Store instance reads the on-disk state, rather than a conversation variable.
    store = Store(args.state_dir)
    state = capture("resume read", store.read())
    assert state["assessment_status"] == "paused" and state["next_item"] == "D1"
    state = capture("D1 completed", store.record("D1", {"inputs": {
        "work_case": fact("本人设计扣合结构，用3D打印样件迭代两次；同事负责外观。开合记录200次，未完成量产验证。")},
        "input_status": "complete", "next_item": "A2"}, state["revision"]))
    d1_before = state["items"]["D1"]
    state = capture("retest A1", store.retest(["A1"], state["revision"]))
    state = capture("A1 new measurement", store.record("A1", {"inputs": {
        "height_cm": fact(171.5, "cm", "2026-10-18"),
        "measurement_conditions": fact("早上脱鞋靠墙测量两次，数值相同。", observed_at="2026-10-18")},
        "input_status": "complete", "next_item": "A2"}, state["revision"]))
    saved = store.read()
    assert saved == state and saved["items"]["D1"] == d1_before
    assert all(item["score"] is None for item in saved["items"].values())
    older = [path.read_text(encoding="utf-8") for path in (store.root / "history").glob("*.md")]
    assert any('"value": 172' in text for text in older)
    print(json.dumps({"case": "authored fictional inputs; commands actually executed",
                      "trace": trace, "verified": {"readback": True, "old_height_in_history": True,
                      "unselected_D1_unchanged": True, "all_scores_null": True},
                      "history_revisions": sorted(path.stem for path in (store.root / "history").glob("*.md"))},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
