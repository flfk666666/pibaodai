"""Fictional 36-item weighting and scenario tests."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

def fixture():
    weights={'A':[20,25,20,10,15,10],'B':[15,25,20,15,15,10],
             'C':[15,20,25,20,10,10],'D':[25,20,15,15,15,10],
             'E':[20,15,25,10,15,15],'F':[20,15,15,25,15,10]}
    top=dict(zip('ABCDEF',[20,15,15,20,20,10]))
    return {'rating_type':'weighted_character','version':'weighted-character-v0.4',
      'axes':[{'id':key,'name':key,'axis_weight':top[key],
               'items':[{'id':key+str(i+1),'name':'编写的子项','weight':weight,
                         'score':60,'reason':'编写的材料','anchor':'项目锚点'}
                        for i,weight in enumerate(weights[key])]} for key in 'ABCDEF']}

class WeightedTests(unittest.TestCase):
    def module(self):
        path=ROOT/'scripts/weighted_character.py'
        self.assertTrue(path.exists(),'Full weighted character engine is not implemented')
        spec=importlib.util.spec_from_file_location('weighted_character',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_all_36_items_have_real_positive_global_weight(self):
        data=fixture();before=copy.deepcopy(data)
        result=self.module().calculate_report(data)
        self.assertEqual(60,result['overall']['score'])
        self.assertEqual(100,result['overall']['coverage_pct'])
        self.assertAlmostEqual(100,sum(i['global_weight'] for a in result['axes'] for i in a['items']))
        self.assertTrue(all(i['global_weight']>0 for a in result['axes'] for i in a['items']))
        self.assertEqual(before,data)

    def test_regional_range_envelopes_all_reference_cases(self):
        module=self.module();data=fixture()
        data['assessment_facts']={'self_annual_cny':100000,'net_assets_snapshot_cny':300000,
            'cash_low_cny':30000,'cash_high_cny':40000,'family_support_cny':200000,'family_availability_score':40}
        data['benchmarks']={'version':'regional-income-v0.3','self_annual_cny':100000,
            'fx':{'rate_date':'2026-01-02','cny_per_unit':{'CNY':1}},'groups':[
              {'id':'fiction','income_rows':[{'source_amount':200000,'currency':'CNY','frequency':'year'},
                                             {'source_amount':50000,'currency':'CNY','frequency':'year'}]}]}
        review=module.calculate_report(data)['benchmarks']['groups'][0]['character_review']
        self.assertEqual(min(case['lower'] for case in review['case_scores']),review['lower'])
        self.assertEqual(max(case['upper'] for case in review['case_scores']),review['upper'])

    def test_case_selection_uses_unrounded_score_independent_of_row_order(self):
        module=self.module();data=fixture()
        data['assessment_facts']={'self_annual_cny':100000}
        rows=[{'label':'higher score','source_amount':100000,'currency':'CNY','frequency':'year'},
              {'label':'lower score','source_amount':100100,'currency':'CNY','frequency':'year'}]
        data['benchmarks']={'version':'regional-income-v0.3','self_annual_cny':100000,
          'fx':{'rate_date':'2026-01-02','cny_per_unit':{'CNY':1}},'groups':[
            {'id':'fiction','income_rows':rows}]}
        for order in (rows,list(reversed(rows))):
            data['benchmarks']['groups'][0]['income_rows']=order
            review=module.calculate_report(data)['benchmarks']['groups'][0]['character_review']
            self.assertEqual({60},{case['score'] for case in review['case_scores']})
            self.assertEqual('lower score',review['selected_case'])
            self.assertEqual(min(case['score_exact'] for case in review['case_scores']),review['score_exact'])

    def test_audit_fields_reconcile_known_denominator_and_full_bounds(self):
        data=fixture();data['axes'][0]['items'][2]['score']=None
        data['axes'][1]['items'][1]['score']=72.3
        overall=self.module().calculate_report(data)['overall']
        self.assertAlmostEqual(5806.125,overall['weighted_numerator'])
        self.assertAlmostEqual(5806.125/96,overall['score_exact'])
        self.assertEqual(round(overall['weighted_numerator']/100,4),overall['lower'])
        self.assertAlmostEqual(overall['lower']+4,overall['upper'])

    def test_height_changes_appearance_and_overall_not_just_text(self):
        data=fixture();data['axes'][0]['items'][0]['score']=100
        result=self.module().calculate_report(data)
        self.assertEqual(68,result['axes'][0]['score'])
        self.assertEqual(62,result['overall']['score'])
        self.assertEqual(4,result['axes'][0]['items'][0]['global_weight'])

    def test_regional_height_exposes_gap_cap_and_known_axis_weight(self):
        data=fixture();data['axes'][0]['items'][0]['score']=100
        data['axes'][0]['items'][2]['score']=None
        data['assessment_facts']={'height_cm':182}
        data['benchmarks']={'version':'regional-income-v0.3','self_annual_cny':100000,
            'fx':{'rate_date':'2026-01-02','cny_per_unit':{'CNY':1}},'groups':[
              {'id':identifier,'income_rows':[{'source_amount':100000,'currency':'CNY','frequency':'year'}],
               'character_settings':settings}
              for identifier,settings in [('shorter',{'height_reference_cm':165,'height_reference_label':'虚构样本'}),
                 ('taller',{'height_reference_cm':175,'height_reference_label':'虚构样本'}),('missing',{})]]}
        groups=self.module().calculate_report(data)['benchmarks']['groups']
        short,tall,missing=[g['character_review']['axes'][0]['height_comparison'] for g in groups]
        self.assertEqual(17,short['delta_cm']);self.assertEqual(111,short['uncapped_score'])
        self.assertTrue(short['capped']);self.assertEqual(100,short['score'])
        self.assertEqual(81,tall['score']);self.assertFalse(tall['capped'])
        self.assertEqual(20,short['within_axis_weight'])
        self.assertEqual(25,short['effective_known_axis_weight'])
        self.assertEqual(25,short['appearance_contribution'])
        self.assertEqual('fallback',missing['status']);self.assertIsNone(missing['delta_cm'])

    def test_partial_family_capacity_changes_regional_range(self):
        data=fixture();data['axes'][5]['items'][0].update(score=None,score_range=[30,80])
        data['assessment_facts']={'family_support_cny':100000}
        data['benchmarks']={'version':'regional-income-v0.3','self_annual_cny':100000,
          'fx':{'rate_date':'2026-01-02','cny_per_unit':{'CNY':1}},'groups':[
            {'id':'fiction','income_rows':[{'source_amount':500000,'currency':'CNY','frequency':'year'}]}]}
        result=self.module().calculate_report(data)
        axis=result['benchmarks']['groups'][0]['character_review']['axes'][5]
        change=next(i for i in axis['changed_items'] if i['id']=='F1')
        self.assertIsNone(change['regional_score'])
        self.assertLess(axis['score_low'],result['axes'][5]['score_low'])

    def test_missing_items_keep_weight_and_bounds_without_zero_penalty(self):
        data=fixture();data['axes'][0]['items'][2]['score']=None;data['axes'][4]['items'][4]['score']=None
        result=self.module().calculate_report(data)
        self.assertEqual(60,result['overall']['score'])
        self.assertEqual(93,result['overall']['coverage_pct'])
        self.assertAlmostEqual(55.8,result['overall']['lower'])
        self.assertAlmostEqual(62.8,result['overall']['upper'])

    def test_numeric_curves_and_explicit_uncertainty(self):
        module=self.module()
        self.assertEqual(88,module.height_preference_score(182))
        self.assertEqual(100,module.height_preference_score(193))
        self.assertEqual(70,module.piecewise_score(117,[(0,0),(60,20),(80,40),(104,60),(130,80),(158,100)]))
        self.assertEqual(60,module.swim_score(200))
        self.assertEqual(80,module.asset_year_score(4))
        self.assertEqual(60,module.cash_month_score(4))
        self.assertEqual(100,module.family_capacity_score(3))
        self.assertEqual(70,module.family_support_score(300000,90000,40))
        self.assertEqual(0,module.family_support_score(0,90000,100))
        data=fixture();data['axes'][1]['items'][4].update(score=40,score_range=[20,60])
        result=module.calculate_report(data)
        self.assertLess(result['overall']['lower'],result['overall']['upper'])

    def test_invalid_weights_and_scores_cannot_hide_items(self):
        module=self.module()
        for change in ['zero','missing','invalid']:
            data=fixture()
            if change=='zero':data['axes'][0]['items'][0]['weight']=0
            elif change=='missing':data['axes'][0]['items'].pop()
            else:data['axes'][0]['items'][0]['score']=float('nan')
            with self.subTest(change=change),self.assertRaises(ValueError):module.calculate_report(data)

    def test_full_regional_scenario_uses_six_axes_and_assets(self):
        module=self.module();data=fixture()
        data['assessment_facts']={'height_cm':182,'self_annual_cny':100000,'net_assets_snapshot_cny':300000,
            'cash_low_cny':30000,'cash_high_cny':40000,'family_support_cny':200000,'family_availability_score':40}
        data['benchmarks']={'version':'regional-income-v0.3','self_annual_cny':100000,
            'fx':{'rate_date':'2026-01-02','cny_per_unit':{'CNY':1}},
            'groups':[{'id':'fiction','label':'编写的地区','income_rows':[{'source_amount':200000,'currency':'CNY','frequency':'year','label':'虚构参照'}],
                       'character_settings':{'communication_score':40,'communication_range':[20,60],'housing_score':40,'care_score':None,'network_score':None},
                       'character_summary':{'verdict':'编写的结论'}}]}
        before=copy.deepcopy(data);result=module.calculate_report(data)
        review=result['benchmarks']['groups'][0]['character_review']
        self.assertEqual(6,len(review['axes']))
        self.assertEqual(100,sum(a['weight'] for a in review['axes']))
        self.assertEqual(60,review['axes'][1]['score'])
        self.assertEqual(60,review['axes'][2]['score'])
        changed={i['id'] for a in review['axes'] for i in a['changed_items']}
        self.assertTrue({'E1','E2','E3','F1','D3'}.issubset(changed))
        self.assertEqual(before,data)

if __name__=='__main__':unittest.main()
