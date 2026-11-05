"""Fictional examples for explicit rules, missing data, and report boundaries."""
import copy
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "score_review.py"


def item(identifier, weight, score):
    return {"id": identifier, "weight": weight, "score": score,
            "anchor": "编写的行为锚点" if score is not None else "尚无可评分材料",
            "reason": "编写的演示依据，不是真人记录"}


def report_fixture():
    return {"rating_type": "anchored_review", "version": "anchored-review-v0.2",
            "baseline": 60, "population_percentile": None,
            "axes": [{"id": identifier, "items": [item(identifier + "1", 100, 60)]}
                     for identifier in "ABCDEF"],
            "regions": [{"name": "虚构地区", "reference": 123}]}


class ScoreReviewTests(unittest.TestCase):
    def calculator(self):
        self.assertTrue(SCRIPT.is_file(), "The explicit-rule calculator is not implemented yet")
        spec = importlib.util.spec_from_file_location("score_review", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_weighted_mean_is_reproducible_and_rounds_half_up(self):
        module = self.calculator()
        result = module.calculate_axis([item("X", 52.5, 80), item("Y", 47.5, 60)])
        self.assertEqual(71, result["score"])
        self.assertEqual(100, result["known_weight"])
        self.assertEqual(100, result["coverage_pct"])
        self.assertEqual(70.5, result["lower"])
        self.assertEqual(70.5, result["upper"])
        self.assertEqual(11, result["delta_from_60"])
        self.assertFalse(result["partial"])
        self.assertIn("52.5", result["formula"])

    def test_unknown_does_not_count_as_zero_or_shrink_the_declared_denominator(self):
        module = self.calculator()
        result = module.calculate_axis([item("X", 30, 80), item("Y", 30, 60), item("Z", 40, None)])
        self.assertEqual(70, result["score"])
        self.assertEqual(60, result["known_weight"])
        self.assertEqual(60, result["coverage_pct"])
        self.assertEqual(42, result["lower"])
        self.assertEqual(82, result["upper"])
        self.assertEqual(2, result["scored_items"])
        self.assertEqual(3, result["total_weighted_items"])
        self.assertTrue(result["partial"])

    def test_all_unknown_stays_unknown_and_zero_weight_facts_are_not_scored(self):
        module = self.calculator()
        result = module.calculate_axis([item("fact", 0, None), item("unknown", 100, None)])
        self.assertIsNone(result["score"])
        self.assertIsNone(result["delta_from_60"])
        self.assertEqual((0, 100), (result["lower"], result["upper"]))
        self.assertEqual(0, result["coverage_pct"])
        self.assertEqual(1, result["total_weighted_items"])
        with self.assertRaises(ValueError):
            module.calculate_axis([item("fact", 0, 100), item("known", 100, 60)])

    def test_invalid_weights_ids_scores_or_explanations_are_rejected(self):
        module = self.calculator()
        invalid = [[], [item("X", 99, 60)], [item("X", 100, 60), item("X", 0, None)],
                   [item("X", -1, None), item("Y", 101, 60)], [item("X", True, 60)],
                   [item("X", float("nan"), 60)], [item("X", float("inf"), 60)],
                   [item("X", "100", 60)], [item("", 100, 60)],
                   [{**item("X", 100, 60), "anchor": " "}],
                   [{**item("X", 100, 60), "reason": None}]]
        invalid.extend([[item("X", 100, score)] for score in [True, -1, 101, 75, 60.0, "60", float("nan")]])
        for items in invalid:
            with self.subTest(items=items), self.assertRaises(ValueError):
                module.calculate_axis(items)

    def test_input_is_not_mutated_and_region_changes_do_not_change_axis_scores(self):
        module = self.calculator()
        report = report_fixture()
        before = copy.deepcopy(report)
        first = module.calculate_report(report)
        self.assertEqual(before, report)
        report["regions"] = [{"name": "另一个虚构地区", "reference": 999999}]
        second = module.calculate_report(report)
        self.assertEqual([60] * 6, [axis["score"] for axis in first["axes"]])
        self.assertEqual(first["axes"], second["axes"])
        first["axes"][0]["items"][0]["reason"] = "changed copy"
        self.assertEqual(before["axes"], report["axes"])

    def test_report_contract_rejects_invalid_axes_version_and_population_claims(self):
        module = self.calculator()
        for field, value in [("rating_type", "percentile"), ("version", "unknown"),
                             ("baseline", 50), ("baseline", 60.0), ("population_percentile", 60)]:
            report = report_fixture()
            report[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                module.calculate_report(report)
        for axes in [[], report_fixture()["axes"][:-1], report_fixture()["axes"] + [None]]:
            report = report_fixture()
            report["axes"] = axes
            with self.assertRaises(ValueError):
                module.calculate_report(report)
        report = report_fixture()
        del report["axes"][0]["items"]
        with self.assertRaises(ValueError):
            module.calculate_report(report)
        result = module.calculate_report(report_fixture())
        self.assertEqual(60, result["baseline"])
        self.assertIsNone(result["population_percentile"])


if __name__ == "__main__":
    unittest.main()
