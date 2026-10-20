"""Regression tests for private character-panel checkpoints.

All records are authored fixtures in temporary directories.  CLI tests use a
fresh Python process for every action so they also exercise restart recovery.
"""

from __future__ import annotations

import copy
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
CLI = SCRIPTS / "panel.py"
MARKER = "<!-- character-panel-state:v1 -->"
STATE_BLOCK = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)
ITEM_IDS = {f"{axis}{number}" for axis in "ABCDEF" for number in range(1, 7)}


def embedded_state(markdown: str) -> dict:
    blocks = STATE_BLOCK.findall(markdown)
    if markdown.count(MARKER) != 1 or len(blocks) != 1:
        raise AssertionError("current.md must contain one marked canonical JSON block")
    return json.loads(blocks[0])


def fact(value, observed_at=None, unit=None):
    result = {"value": value, "observed_at": observed_at, "source": "self_report"}
    if unit is not None:
        result["unit"] = unit
    return result


class PanelCLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="character-panel-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.state_dir = self.root / "private-state"
        self.current = self.state_dir / "current.md"
        self.payload_number = 0

    def run_cli(self, *arguments, expected_code=0):
        result = subprocess.run(
            [sys.executable, str(CLI), "--state-dir", str(self.state_dir), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
            timeout=20,
        )
        self.assertEqual(
            expected_code,
            result.returncode,
            f"command: {arguments}\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )
        if expected_code:
            failure = json.loads(result.stderr)
            self.assertIs(failure["ok"], False)
            self.assertTrue(failure.get("error"))
            return failure
        self.assertEqual("", result.stderr)
        if arguments[0] == "render":
            return result.stdout
        response = json.loads(result.stdout)
        self.assertIs(response["ok"], True)
        self.assertEqual(response["revision"], response["state"]["revision"])
        return response

    def initialize(self):
        return self.run_cli("init", "--profile-id", "self")

    def write_payload(self, payload):
        self.payload_number += 1
        path = self.root / f"payload-{self.payload_number}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def record(self, item, payload, revision, expected_code=0):
        path = self.write_payload(payload)
        return self.run_cli(
            "record", "--item", item, "--payload-file", str(path),
            "--expect-revision", str(revision), expected_code=expected_code,
        )

    def disk_state(self):
        return embedded_state(self.current.read_text(encoding="utf-8"))

    def history_states(self):
        return [
            embedded_state(path.read_text(encoding="utf-8"))
            for path in (self.state_dir / "history").glob("*.md")
        ]

    def assert_no_scores(self, state):
        self.assertEqual(ITEM_IDS, set(state["items"]))
        for item in state["items"].values():
            self.assertIsNone(item["score"], item["id"])
            self.assertIsNone(item["rubric_version"], item["id"])

    def test_init_has_36_unknown_items_and_a_readable_canonical_archive(self):
        response = self.initialize()
        state = response["state"]
        self.assertEqual(1, state["schema_version"])
        self.assertEqual(1, state["revision"])
        self.assertEqual("self", state["profile_id"])
        self.assertEqual("in_progress", state["assessment_status"])
        self.assertEqual("basic", state["next_item"])
        self.assertEqual({}, state["basic_profile"]["inputs"])
        self.assert_no_scores(state)
        for item in state["items"].values():
            self.assertEqual("not_started", item["input_status"])
            self.assertEqual("blocked", item["scoring_status"])
            self.assertEqual({}, item["inputs"])
        self.assertEqual(36, response["summary"]["total_items"])
        self.assertEqual(0, response["summary"]["filled_items"])
        self.assertEqual(0, response["summary"]["scored_items"])
        markdown = self.current.read_text(encoding="utf-8")
        self.assertEqual(state, embedded_state(markdown))
        self.assertIn("A1", markdown)
        self.assertIn("F6", markdown)

    def test_init_cannot_reset_an_existing_archive(self):
        self.initialize()
        original = self.current.read_bytes()
        self.run_cli("init", "--profile-id", "someone-else", expected_code=2)
        self.assertEqual(original, self.current.read_bytes())

    def test_partial_answers_merge_across_processes_without_refreshing_dates(self):
        self.initialize()
        first = self.record("A1", {
            "inputs": {"height_cm": fact(174, None, "cm")},
            "input_status": "partial", "next_item": "A1",
            "next_prompt": "请补充测量方式。",
        }, 1)
        second = self.record("A1", {
            "inputs": {"measurement_method": fact("barefoot", "2026-10-01")},
            "input_status": "partial", "next_item": "A1",
            "next_prompt": "继续确认资料。",
        }, first["revision"])
        saved_bytes = self.current.read_bytes()
        resumed = self.run_cli("status")
        item = resumed["state"]["items"]["A1"]
        self.assertEqual(174, item["inputs"]["height_cm"]["value"])
        self.assertIsNone(item["inputs"]["height_cm"]["observed_at"])
        self.assertEqual("2026-10-01", item["inputs"]["measurement_method"]["observed_at"])
        self.assertEqual("继续确认资料。", resumed["state"]["next_prompt"])
        self.assertEqual(second["revision"], resumed["revision"])
        self.assertEqual(saved_bytes, self.current.read_bytes())
        self.assertEqual(second["state"]["saved_at"], resumed["state"]["saved_at"])
        self.assertEqual(1, resumed["summary"]["partial_items"])
        self.assert_no_scores(resumed["state"])

    def test_completed_input_remains_unscored_while_rubric_is_undefined(self):
        self.initialize()
        response = self.record("A1", {
            "inputs": {"height_cm": fact(174, "2026-10-01", "cm")},
            "input_status": "complete", "next_item": "A2",
        }, 1)
        item = response["state"]["items"]["A1"]
        self.assertEqual("complete", item["input_status"])
        self.assertEqual("blocked", item["scoring_status"])
        self.assertIsNone(item["score"])
        self.assertTrue(item["reason"])
        self.assertEqual(1, response["summary"]["filled_items"])
        self.assertEqual(0, response["summary"]["scored_items"])

    def test_basic_profile_is_checkpointed_without_counting_as_a_scored_item(self):
        self.initialize()
        first = self.record("basic", {
            "inputs": {"city": fact("Example City", "2026-10-01")},
            "input_status": "partial", "next_item": "basic",
            "next_prompt": "请补充你希望使用的比较地区。",
        }, 1)
        second = self.record("basic", {
            "inputs": {"age": fact(30, "2026-10-01", "years")},
            "input_status": "partial",
        }, first["revision"])
        profile = self.run_cli("status")["state"]["basic_profile"]
        self.assertEqual("Example City", profile["inputs"]["city"]["value"])
        self.assertEqual(30, profile["inputs"]["age"]["value"])
        self.assertEqual(0, second["summary"]["filled_items"])
        self.assertEqual(36, second["summary"]["total_items"])

    def test_replacing_a_fact_does_not_carry_forward_an_old_date_or_unit(self):
        self.initialize()
        first = self.record("A1", {
            "inputs": {"height_cm": fact(174, "2026-09-01", "cm")},
            "input_status": "partial",
        }, 1)
        second = self.record("A1", {
            "inputs": {"height_cm": {"value": 175}},
            "input_status": "partial",
        }, first["revision"])
        replaced = second["state"]["items"]["A1"]["inputs"]["height_cm"]
        self.assertEqual(175, replaced["value"])
        self.assertIsNone(replaced["observed_at"])
        self.assertIsNone(replaced["unit"])

    def test_pause_preserves_resume_cursor_and_archives_prior_revision(self):
        self.initialize()
        written = self.record("A1", {
            "inputs": {"height_cm": fact(174, unit="cm")},
            "input_status": "partial", "next_item": "A1",
            "next_prompt": "请确认测量日期；不知道可以留空。",
        }, 1)
        paused = self.run_cli("pause", "--expect-revision", str(written["revision"]))
        self.assertEqual("paused", paused["state"]["assessment_status"])
        self.assertEqual("A1", paused["state"]["next_item"])
        self.assertEqual(written["state"]["next_prompt"], paused["state"]["next_prompt"])
        self.assertIn(written["state"], self.history_states())
        self.assertEqual(paused["state"], self.run_cli("status")["state"])

    def test_local_retest_preserves_unselected_items_and_old_observation_dates(self):
        self.initialize()
        one = self.record("A1", {
            "inputs": {"height_cm": fact(174, "2026-09-01", "cm")},
            "input_status": "partial",
        }, 1)
        two = self.record("E1", {
            "inputs": {"monthly_income": fact(8000, "2026-09-30", "CNY")},
            "input_status": "partial",
        }, one["revision"])
        before = two["state"]
        response = self.run_cli(
            "retest", "--items", "A1,E1", "--expect-revision", str(two["revision"]),
        )
        after = response["state"]
        self.assertNotEqual(before["assessment_id"], after["assessment_id"])
        self.assertEqual("A1", after["next_item"])
        for item_id in ITEM_IDS - {"A1", "E1"}:
            self.assertEqual(before["items"][item_id], after["items"][item_id], item_id)
        for item_id in {"A1", "E1"}:
            self.assertEqual(before["items"][item_id]["inputs"], after["items"][item_id]["inputs"])
            self.assertEqual("partial", after["items"][item_id]["input_status"])
            self.assertEqual("review_due", after["items"][item_id]["freshness"])
        self.assertIn(before, self.history_states())
        self.assert_no_scores(after)

    def test_retest_queue_resumes_partial_items_then_advances_only_within_selection(self):
        self.initialize()
        retest = self.run_cli("retest", "--items", "A1,E1", "--expect-revision", "1")
        self.assertEqual(["A1", "E1"], retest["state"]["retest_queue"])
        partial = self.record("A1", {
            "inputs": {"height_cm": fact(174, "2026-10-01", "cm")},
            "input_status": "partial",
        }, retest["revision"])
        self.assertEqual("A1", partial["state"]["next_item"])
        self.assertEqual(["A1", "E1"], partial["state"]["retest_queue"])
        complete = self.record("A1", {
            "input_status": "complete", "confirm_current": True,
        }, partial["revision"])
        self.assertEqual("E1", complete["state"]["next_item"])
        self.assertEqual(["E1"], complete["state"]["retest_queue"])
        skipped = self.record("E1", {
            "input_status": "deferred", "observations": "User explicitly defers this item.",
        }, complete["revision"])
        self.assertEqual([], skipped["state"]["retest_queue"])
        self.assertNotIn(skipped["state"]["next_item"], ["A1", "E1"])
        self.assertEqual("deferred", skipped["state"]["items"]["E1"]["input_status"])
        self.assertIsNone(skipped["state"]["items"]["E1"]["score"])

    def test_saving_an_answer_resumes_a_paused_assessment(self):
        self.initialize()
        paused = self.run_cli("pause", "--expect-revision", "1")
        self.assertEqual("paused", paused["state"]["assessment_status"])
        resumed = self.record("A1", {
            "inputs": {"height_cm": fact(174, unit="cm")},
            "input_status": "partial", "next_item": "A1",
        }, paused["revision"])
        self.assertEqual("in_progress", resumed["state"]["assessment_status"])
        self.assertEqual("A1", self.run_cli("status")["state"]["next_item"])

    def test_overwriting_a_nonempty_fact_preserves_its_previous_revision(self):
        self.initialize()
        before = self.record("A1", {
            "inputs": {"height_cm": fact(174, "2026-09-01", "cm")},
            "input_status": "partial",
        }, 1)
        after = self.record("A1", {
            "inputs": {"height_cm": fact(175, "2026-10-01", "cm")},
            "input_status": "partial",
        }, before["revision"])
        self.assertIn(before["state"], self.history_states())
        self.assertEqual(175, after["state"]["items"]["A1"]["inputs"]["height_cm"]["value"])
        self.assertEqual(before["state"], embedded_state(
            (self.state_dir / ".last-good.md").read_text(encoding="utf-8")
        ))

    def test_stale_revision_refuses_to_overwrite_a_newer_answer(self):
        self.initialize()
        self.record("A1", {"inputs": {"height_cm": fact(174, unit="cm")}}, 1)
        original = self.current.read_bytes()
        self.record("A1", {"inputs": {"height_cm": fact(190, unit="cm")}}, 1, expected_code=2)
        self.assertEqual(original, self.current.read_bytes())

    def test_existing_writer_lock_refuses_a_second_writer(self):
        self.initialize()
        original = self.current.read_bytes()
        lock = self.state_dir / ".write.lock"
        lock.write_text("another-session", encoding="utf-8")
        self.record("A1", {"inputs": {"height_cm": fact(174, unit="cm")}}, 1, expected_code=2)
        self.assertEqual(original, self.current.read_bytes())
        self.assertEqual("another-session", lock.read_text(encoding="utf-8"))

    def test_unknown_schema_is_not_reset_or_silently_migrated(self):
        response = self.initialize()
        state = copy.deepcopy(response["state"])
        state["schema_version"] = 999
        markdown = self.current.read_text(encoding="utf-8")
        replacement = "```json\n" + json.dumps(state, ensure_ascii=False, indent=2) + "\n```"
        self.current.write_text(STATE_BLOCK.sub(lambda _: replacement, markdown), encoding="utf-8")
        original = self.current.read_bytes()
        self.run_cli("status", expected_code=2)
        self.assertEqual(original, self.current.read_bytes())

    def test_required_photo_disappearing_marks_awaiting_material_not_zero(self):
        self.initialize()
        evidence_dir = self.state_dir / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        photo = evidence_dir / "front.jpg"
        photo.write_bytes(b"authored-fixture-no-personal-photo")
        response = self.record("A2", {
            "inputs": {}, "input_status": "partial",
            "evidence": [{"id": "front", "path": "evidence/front.jpg", "captured_at": None, "required": True}],
            "observations": "Only a path-access fixture; no appearance judgment.",
        }, 1)
        photo.unlink()
        checked = self.run_cli("check-evidence", "--expect-revision", str(response["revision"]))
        item = checked["state"]["items"]["A2"]
        self.assertEqual("awaiting_material", item["input_status"])
        self.assertEqual("review_due", item["freshness"])
        self.assertIsNone(item["score"])
        self.assertGreaterEqual(checked["summary"]["awaiting_material_items"], 1)
        self.assertEqual(0, checked["summary"]["scored_items"])

    def test_record_rechecks_a_previously_available_required_photo_before_completion(self):
        self.initialize()
        photo = self.state_dir / "photo.jpg"
        photo.write_bytes(b"authored-fixture-no-personal-photo")
        saved = self.record("A2", {
            "evidence": [{"id": "front", "path": "photo.jpg", "captured_at": None, "required": True}],
            "input_status": "complete",
        }, 1)
        self.assertEqual("complete", saved["state"]["items"]["A2"]["input_status"])
        photo.unlink()
        attempted = self.record("A2", {"input_status": "complete"}, saved["revision"])
        item = attempted["state"]["items"]["A2"]
        self.assertEqual("awaiting_material", item["input_status"])
        self.assertEqual("review_due", item["freshness"])
        self.assertEqual("missing", item["evidence"][0]["availability"])
        self.assertIsNone(item["score"])

    def test_retest_cannot_complete_old_values_or_clear_review_with_only_notes(self):
        self.initialize()
        filled = self.record("A1", {
            "inputs": {"height_cm": fact(174, "2026-09-01", "cm")},
            "input_status": "complete",
        }, 1)
        retest = self.run_cli("retest", "--items", "A1,E1", "--expect-revision", str(filled["revision"]))
        original = self.current.read_bytes()
        self.record("A1", {"input_status": "complete"}, retest["revision"], expected_code=2)
        self.assertEqual(original, self.current.read_bytes())
        noted = self.record("A1", {
            "input_status": "partial", "observations": "An explanatory note, no new measurement or confirmation.",
            "next_prompt": "Please confirm whether the saved height is still current.",
        }, retest["revision"])
        self.assertEqual("review_due", noted["state"]["items"]["A1"]["freshness"])
        self.assertEqual(["A1", "E1"], noted["state"]["retest_queue"])
        self.assertEqual("A1", noted["state"]["next_item"])

    def test_retest_partial_facts_remain_due_until_explicit_completion_confirmation(self):
        self.initialize()
        filled = self.record("A1", {
            "inputs": {"height_cm": fact(174, "2026-09-01", "cm")},
            "input_status": "complete",
        }, 1)
        retest = self.run_cli("retest", "--items", "A1,E1", "--expect-revision", str(filled["revision"]))
        partial = self.record("A1", {
            "inputs": {"measurement_method": fact("barefoot", "2026-10-01")},
            "input_status": "partial",
        }, retest["revision"])
        self.assertEqual("review_due", partial["state"]["items"]["A1"]["freshness"])
        self.assertEqual(["A1", "E1"], partial["state"]["retest_queue"])
        confirmed = self.record("A1", {
            "input_status": "complete", "confirm_current": True,
        }, partial["revision"])
        item = confirmed["state"]["items"]["A1"]
        self.assertEqual("complete", item["input_status"])
        self.assertEqual("current", item["freshness"])
        self.assertEqual("2026-09-01", item["inputs"]["height_cm"]["observed_at"])
        self.assertEqual(["E1"], confirmed["state"]["retest_queue"])
        self.assertEqual("E1", confirmed["state"]["next_item"])

    def test_explicit_null_is_preserved_and_not_imputed_as_zero(self):
        self.initialize()
        response = self.record("A1", {
            "inputs": {"height_cm": fact(None, None, "cm")},
            "input_status": "partial",
        }, 1)
        self.assertIsNone(response["state"]["items"]["A1"]["inputs"]["height_cm"]["value"])
        self.assertIsNone(self.disk_state()["items"]["A1"]["score"])
        self.assertEqual(0, response["summary"]["scored_items"])

    def test_invalid_payloads_cannot_write_scores_or_corrupt_the_archive(self):
        self.initialize()
        invalid_payloads = [
            {"score": 80},
            {"scoring_status": "scored"},
            {"inputs": []},
            {"input_status": "invented-status"},
            {"inputs": {}, "input_status": "complete"},
            {"inputs": {"height_cm": fact(None)}, "input_status": "complete"},
            {"inputs": {"height_cm": fact(174, "not-a-date", "cm")}},
            {"inputs": {"height_cm": fact(float("nan"), unit="cm")}},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                original = self.current.read_bytes()
                self.record("A1", payload, 1, expected_code=2)
                self.assertEqual(original, self.current.read_bytes())
        self.record("Z9", {"inputs": {}}, 1, expected_code=2)

    def test_render_is_read_only_and_contains_the_same_canonical_state(self):
        response = self.initialize()
        original = self.current.read_bytes()
        rendered = self.run_cli("render")
        self.assertEqual(response["state"], embedded_state(rendered))
        self.assertEqual(original, self.current.read_bytes())

    def test_empty_or_unrelated_new_fields_cannot_finish_a_retest(self):
        self.initialize()
        saved = self.record("A1", {"inputs": {"height_cm": fact(174, "2026-09-01", "cm")},
            "input_status": "complete"}, 1)
        retest = self.run_cli("retest", "--items", "A1", "--expect-revision", str(saved["revision"]))
        original = self.current.read_bytes()
        for value in [None, "", "   ", [], {}, "optional description without a new height"]:
            with self.subTest(value=value):
                self.record("A1", {"inputs": {"measurement_method": fact(value)},
                    "input_status": "complete"}, retest["revision"], expected_code=2)
                self.assertEqual(original, self.current.read_bytes())

    def test_invalid_state_metadata_and_evidence_are_rejected_without_reset(self):
        response = self.initialize()
        original = self.current.read_bytes()
        for field, value in [("retest_queue", ["Z9"]), ("assessment_status", "invented-status")]:
            with self.subTest(field=field):
                state = copy.deepcopy(response["state"])
                state[field] = value
                document = original.decode("utf-8")
                replacement = "```json\n" + json.dumps(state, ensure_ascii=False, indent=2) + "\n```"
                self.current.write_text(STATE_BLOCK.sub(lambda _: replacement, document), encoding="utf-8")
                corrupted = self.current.read_bytes()
                self.run_cli("status", expected_code=2)
                self.assertEqual(corrupted, self.current.read_bytes())
                self.current.write_bytes(original)
        state = copy.deepcopy(response["state"])
        state["items"]["A2"]["evidence"] = [{"id": "front", "path": "evidence/front.jpg",
            "required": True, "availability": "missing", "captured_at": "not-a-date"}]
        replacement = "```json\n" + json.dumps(state, ensure_ascii=False, indent=2) + "\n```"
        self.current.write_text(STATE_BLOCK.sub(lambda _: replacement, original.decode("utf-8")), encoding="utf-8")
        corrupted = self.current.read_bytes()
        self.run_cli("status", expected_code=2)
        self.assertEqual(corrupted, self.current.read_bytes())

    def test_atomic_replace_failure_and_permission_failure_keep_last_good_archive(self):
        self.initialize()
        self.assertTrue((SCRIPTS / "panel_store.py").is_file(), "panel_store implementation is required")
        sys.path.insert(0, str(SCRIPTS))
        self.addCleanup(lambda: sys.path.remove(str(SCRIPTS)))
        module = importlib.import_module("panel_store")
        store = module.Store(self.state_dir)
        real_replace = module.os.replace
        for fault in [OSError("simulated replace failure"), PermissionError("simulated unwritable state directory")]:
            with self.subTest(fault=type(fault).__name__):
                original = self.current.read_bytes()
                current_revision = self.disk_state()["revision"]

                def refuse_current(source, destination, *args, **kwargs):
                    if Path(destination).resolve() == self.current.resolve():
                        raise fault
                    return real_replace(source, destination, *args, **kwargs)

                with mock.patch.object(module.os, "replace", side_effect=refuse_current):
                    with self.assertRaises(Exception):
                        store.record("A1", {"inputs": {"height_cm": fact(174, unit="cm")}}, current_revision)
                self.assertEqual(original, self.current.read_bytes())
                store.read()
                self.assertFalse((self.state_dir / ".write.lock").exists())


if __name__ == "__main__":
    unittest.main()
