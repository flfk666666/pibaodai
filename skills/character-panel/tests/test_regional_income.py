"""Fictional currency, annualization, and regional-coordinate checks."""
import copy
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'regional_income.py'


class RegionalIncomeTests(unittest.TestCase):
    def module(self):
        self.assertTrue(SCRIPT.exists(), 'Regional income converter is not implemented yet')
        spec = importlib.util.spec_from_file_location('regional_income', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_annualization_and_currency_cross_rates(self):
        module = self.module()
        fx = module.cross_rates({'CNY': 8, 'USD': 2, 'JPY': 160})
        self.assertEqual(4, fx['USD'])
        self.assertEqual(.05, fx['JPY'])
        row = module.compare_income(96000, 2000, 'USD', 'month', fx)
        self.assertEqual(96000, row['annual_cny'])
        self.assertEqual(1, row['ratio'])
        self.assertEqual(60, row['score'])
        self.assertEqual(52, module.compare_income(104000, 500, 'USD', 'week', fx)['annual_factor'])

    def test_reference_score_anchors_and_clamping(self):
        module = self.module()
        for ratio, expected in [(0, 0), (.25, 20), (.5, 40), (1, 60), (2, 80), (4, 100), (16, 100)]:
            with self.subTest(ratio=ratio):
                result = module.compare_income(ratio * 100, 100, 'CNY', 'year', {'CNY': 1})
                self.assertEqual(expected, result['score'])
                self.assertEqual(ratio, result['ratio'])

    def test_missing_income_and_invalid_inputs(self):
        module = self.module()
        self.assertIsNone(module.compare_income(None, 100, 'CNY', 'year', {'CNY': 1})['score'])
        for bad in [0, -1, True, float('nan'), float('inf')]:
            with self.subTest(reference=bad), self.assertRaises(ValueError):
                module.compare_income(100, bad, 'CNY', 'year', {'CNY': 1})
        with self.assertRaises(ValueError):
            module.compare_income(100, 100, 'USD', 'day', {'USD': 7})
        with self.assertRaises(ValueError):
            module.compare_income(100, 100, 'USD', 'year', {'USD': 0})

    def test_independent_references_produce_range_without_mutation(self):
        module = self.module()
        data = {'version': 'regional-income-v0.3', 'self_annual_cny': 100,
                'fx': {'rate_date': '2026-01-02', 'cny_per_unit': {'CNY': 1}},
                'groups': [{'id': 'fiction', 'regional_score': {'summary': '编写的说明'},
                            'income_rows': [{'label': '甲参照', 'source_amount': 50, 'currency': 'CNY', 'frequency': 'year'},
                                            {'label': '乙参照', 'source_amount': 100, 'currency': 'CNY', 'frequency': 'year'}]}]}
        before = copy.deepcopy(data)
        result = module.calculate_benchmarks(data)
        score = result['groups'][0]['regional_score']
        self.assertIsNone(score['score'])
        self.assertEqual((60, 80), (score['score_low'], score['score_high']))
        self.assertEqual(before, data)
        self.assertEqual('编写的说明', score['summary'])


if __name__ == '__main__':
    unittest.main()
