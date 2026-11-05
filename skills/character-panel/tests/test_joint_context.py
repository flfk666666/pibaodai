"""Authored fictional ownership and liquidity stress cases."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class JointContextTests(unittest.TestCase):
    def module(self):
        spec=importlib.util.spec_from_file_location('joint_context',ROOT/'scripts/joint_context.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

    def fixture(self):
        return {'cash_total_cny':60000,'liquid_cash_cny':[10000,20000],
                'monthly_necessary_cny':5000,'net_monthly_income_cny':[8000,9000],
                'personal_net_assets_cny':200000,'family_support_cny':120000,
                'family_support_within_days':7,'family_available':True,
                'monthly_rent_cny':2000,'fallback_housing_available':True,
                'restricted_cash_early_access':None,'asset_date':'fictional historical date'}

    def test_cash_buckets_do_not_add_the_same_balance_twice(self):
        facts=self.fixture();before=copy.deepcopy(facts);result=self.module().calculate_context(facts)
        self.assertEqual([40000,50000],result['funding_layers']['restricted_cash_cny'])
        self.assertEqual(60000,result['funding_layers']['cash_total_cny'])
        self.assertEqual(200000,result['funding_layers']['personal_net_assets_cny'])
        self.assertIsNone(result['funding_layers']['verified_earmarked_emergency_fund_cny'])
        self.assertEqual(before,facts)

    def test_restricted_unknown_and_family_not_current_cash(self):
        result=self.module().calculate_context(self.fixture())
        self.assertEqual([2,4],result['liquid_buffer_months'])
        six=next(row for row in result['stress_windows'] if row['months']==6)
        self.assertEqual([10000,20000],six['liquid_gap_cny'])
        self.assertEqual('unresolved',six['all_cash_access_status'])
        self.assertEqual(120000,result['funding_layers']['family_support_cny'])
        self.assertFalse(result['funding_layers']['family_in_personal_assets'])

    def test_fallback_is_conditional_not_another_country_budget(self):
        result=self.module().calculate_context(self.fixture())
        case=result['fallback_housing_scenario']
        self.assertEqual(3000,case['necessary_baseline_cny'])
        self.assertTrue(case['conditional'])
        self.assertIn('income_not_transferred',case['assumptions'])
        facts=self.fixture();facts['fallback_housing_available']=None
        self.assertIsNone(self.module().calculate_context(facts)['fallback_housing_scenario'])

    def test_invalid_cash_overlap_rejected_and_missing_not_zero(self):
        facts=self.fixture();facts['liquid_cash_cny']=[50000,70000]
        with self.assertRaises(ValueError):self.module().calculate_context(facts)
        facts=self.fixture();facts['cash_total_cny']=None
        result=self.module().calculate_context(facts)
        self.assertIsNone(result['funding_layers']['restricted_cash_cny'])
        self.assertEqual([2,4],result['liquid_buffer_months'])

if __name__=='__main__':unittest.main()
