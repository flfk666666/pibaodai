"""Fictional decision-contract and numeric-boundary checks."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ContractTests(unittest.TestCase):
    def module(self):
        path=ROOT/'scripts'/'rule_contract.py'
        self.assertTrue(path.exists(),'Decision protocol gate is missing')
        spec=importlib.util.spec_from_file_location('rule_contract',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_numeric_rules_use_values_and_exact_boundaries(self):
        m=self.module()
        self.assertEqual(100,m.numeric_result('A1',{'height_cm':190})['score'])
        self.assertAlmostEqual(72.307692,m.numeric_result('B2',{'body_weight_kg':85,'bench_1rm_kg':120})['score'],places=5)
        self.assertIsNone(m.numeric_result('B2',{'body_weight_kg':70,'bench_1rm_kg':100})['score'])
        self.assertEqual(60,m.numeric_result('B3',{'continuous_swim_m':200})['score'])
        self.assertEqual(40,m.numeric_result('E1',{'after_tax_recurring_income':1000,'necessary_expenses_same_period':1000})['score'])
        self.assertEqual(80,m.numeric_result('E2',{'personal_net_assets_cny':3000,'necessary_annual_expenses_cny':1000})['score'])
        self.assertEqual(80,m.numeric_result('E3',{'available_liquid_funds_cny':6000,'necessary_monthly_expenses_cny':1000})['score'])
        self.assertEqual(100,m.numeric_result('E4',{'monthly_debt_service_cny':0,'monthly_after_tax_income_cny':0,'confirmed_no_debt':True})['score'])
        self.assertEqual(0,m.numeric_result('E4',{'monthly_debt_service_cny':10,'monthly_after_tax_income_cny':0})['score'])
        self.assertEqual(60,m.numeric_result('E5',{'after_tax_income':1000,'actual_expenses':900,'same_period':True})['score'])

    def test_unknown_and_interval_do_not_gain_default_scores(self):
        m=self.module()
        self.assertIsNone(m.numeric_result('E5',{'after_tax_income':1000,'necessary_expenses':500})['score'])
        self.assertIsNone(m.numeric_result('E1',{'after_tax_recurring_income':1000,'necessary_expenses_same_period':0})['score'])
        interval=m.numeric_result('E3',{'available_liquid_funds_cny':[2000,4000],'necessary_monthly_expenses_cny':1000})
        self.assertEqual([40,60],interval['score_range'])
        family=m.numeric_result('F1',{'potential_support_cny':300000,'necessary_annual_expenses_cny':100000,'access_score':40})
        self.assertEqual(70,family['score'])
        partial=m.numeric_result('F1',{'potential_support_cny':300000,'necessary_annual_expenses_cny':100000})
        self.assertIsNone(partial['score']);self.assertEqual([50,100],partial['score_range'])
        self.assertEqual(0,m.numeric_result('F1',{'potential_support_cny':0})['score'])

    def test_registered_weight_rows_and_interpolation_are_explicit(self):
        m=self.module()
        reference={'population':'fictional male bench rows','source_url':'https://strengthlevel.com/strength-standards/bench-press/kg',
          'verified_at':'2026-01-01','rows':[{'body_weight_kg':70,'loads_kg':[40,60,80,100,120]},
                                           {'body_weight_kg':80,'loads_kg':[60,80,100,120,140]}]}
        self.assertEqual(60,m.numeric_result('B2',{'body_weight_kg':75,'bench_1rm_kg':90,'strength_reference':reference})['score'])
        self.assertIsNone(m.numeric_result('B2',{'body_weight_kg':65,'bench_1rm_kg':90,'strength_reference':reference})['score'])
        self.assertIsNone(m.numeric_result('E4',{'monthly_debt_service_cny':0,'monthly_after_tax_income_cny':1000})['score'])

    def test_full_protocols_and_fictional_worked_examples_exist(self):
        contract=self.module().load_contract()
        self.assertEqual(36,len(contract['items']))
        self.assertEqual([a+str(n) for a in 'ABCDEF' for n in range(1,7)],[i['id'] for i in contract['items']])
        required=('definition','required_inputs','evidence_protocol','decision_rule','missing_policy','range_policy',
                  'weight_reason','regional_policy','freshness','review_trigger','cannot_infer','worked_example')
        for item in contract['items']:
            for field in required:self.assertTrue(item.get(field),(item['id'],field))

    def test_score_requires_evidence_and_a_matched_anchor(self):
        m=self.module()
        item={'id':'C1','score':60,'reason':'编写案例','anchor':'编写锚点'}
        with self.assertRaisesRegex(ValueError,'evaluation'):m.validate_item(item)
        item['evaluation']={'status':'rated','evidence':[],'decision':'编写判定','limits':['仅一个案例'],'matched_anchor_score':60}
        with self.assertRaisesRegex(ValueError,'evidence'):m.validate_item(item)
        item['evaluation']['evidence']=[{'source_type':'self_report','summary':'虚构案例描述学习和应用过程','observed_at':None}]
        m.validate_item(item)
        item['score']=80
        with self.assertRaisesRegex(ValueError,'anchor'):m.validate_item(item)

    def test_numeric_tampering_and_absent_inputs_are_rejected(self):
        m=self.module()
        item={'id':'A1','score':60,'anchor':'编写锚点','reason':'编写材料','evaluation':{
            'status':'rated','evidence':[{'source_type':'self_report','summary':'虚构脱鞋测量记录','observed_at':None}],
            'decision':'按声明的男性高个偏好','limits':['项目偏好'],'matched_anchor_score':60}}
        with self.assertRaisesRegex(ValueError,'numeric_inputs'):m.validate_item(item)
        item['evaluation']['numeric_inputs']={'height_cm':190}
        with self.assertRaisesRegex(ValueError,'recompute'):m.validate_item(item)
        item['score']=100;item['evaluation']['matched_anchor_score']=100
        m.validate_item(item)

    def test_partial_numeric_range_cannot_hide_known_component(self):
        m=self.module()
        item={'id':'F1','score':None,'score_range':[0,0],'reason':'条件待补','evaluation':{
            'status':'awaiting_evidence','evidence':[{'source_type':'self_report','summary':'虚构潜在家庭支持','observed_at':None}],
            'decision':'容量已知条件未知','limits':['条件未确认'],'numeric_inputs':{
                'potential_support_cny':100000,'necessary_annual_expenses_cny':100000}}}
        with self.assertRaisesRegex(ValueError,'range'):m.validate_item(item)
        item['score_range']=[30,80];m.validate_item(item)

    def audited_report(self):
        spec=importlib.util.spec_from_file_location('weighted_fixture',ROOT/'tests'/'test_weighted_character.py')
        fixture_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture_module)
        report=fixture_module.fixture();report.update(version='weighted-character-v0.5',protocol_version='character-rules-v0.5')
        raw={'A1':{'height_cm':175},'B2':{'body_weight_kg':85,'bench_1rm_kg':104},'B3':{'continuous_swim_m':200},
          'E1':{'after_tax_recurring_income':2000,'necessary_expenses_same_period':1000},
          'E2':{'personal_net_assets_cny':2000,'necessary_annual_expenses_cny':1000},
          'E3':{'available_liquid_funds_cny':4000,'necessary_monthly_expenses_cny':1000},
          'E4':{'monthly_debt_service_cny':200,'monthly_after_tax_income_cny':1000},
          'E5':{'after_tax_income':1000,'actual_expenses':900,'same_period':True},
          'F1':{'potential_support_cny':1000,'necessary_annual_expenses_cny':1000,'access_score':60}}
        for axis in report['axes']:
            for item in axis['items']:
                item['evaluation']={'status':'rated','matched_anchor_score':60,'decision':'虚构案例支持60档','limits':['虚构单场景'],
                  'evidence':[{'source_type':'fictional_self_report','summary':'完全虚构材料','observed_at':None}]}
                if item['id'] in raw:item['evaluation']['numeric_inputs']=raw[item['id']]
                if item['id']=='B2':item['evaluation'].update(task_protocol='self_reported_or_recorded_standard_barbell_bench_1rm',reference_population='fictional selected male training row')
        return fixture_module.WeightedTests().module(),report

    def test_current_coordinates_and_relocation_are_separate(self):
        engine,report=self.audited_report()
        report['benchmarks']={'version':'regional-income-v0.3','self_annual_cny':100000,
          'fx':{'rate_date':'2026-01-02','cny_per_unit':{'CNY':1}},'groups':[{'id':'fiction','income_rows':[
            {'source_amount':100000,'currency':'CNY','frequency':'year','source_url':'https://example.org/fiction',
             'source_value':'虚构某年税前年工资','age_note':'虚构宽口径样本'}],
            'character_settings':{'communication_score':20,'housing_score':40,'care_score':None,'network_score':None}}]}
        checked=engine.calculate_report(report)
        self.assertEqual(9,checked['quality_review']['numeric_items'])
        self.assertEqual(36,checked['quality_review']['anchor_60_items'])
        group=checked['benchmarks']['groups'][0]
        self.assertEqual('coordinate_current_life',group['comparison_mode'])
        self.assertEqual(60,group['character_review']['axes'][3]['score'])
        self.assertEqual(54,group['relocation_review']['axes'][3]['score'])
        missing=next(i for i in group['character_review']['axes'][4]['changed_items'] if i['id']=='E2')
        self.assertEqual(20,missing['regional_score'])  # Derived from the verified asset original, not the global 60.

    def test_numeric_rounding_is_only_for_display_and_recalculation_is_stable(self):
        exact=60+20*(120-104)/(130-104)
        for entered_range,expected_range in (
            (None,None),([72.3,72.3],[exact,exact]),([60,80],[60,80]),([60,72.3],[60,exact])):
            with self.subTest(entered_range=entered_range):
                engine,report=self.audited_report()
                item=report['axes'][1]['items'][1]
                item['score']=72.3
                item['evaluation']['numeric_inputs']['bench_1rm_kg']=120
                if entered_range is not None:item['score_range']=entered_range
                checked=engine.calculate_report(report)
                checked_item=checked['axes'][1]['items'][1]
                self.assertEqual(exact,checked_item['score'])
                self.assertEqual(72.3,checked_item['score_entered'])
                self.assertEqual(expected_range,checked_item.get('score_range'))
                if entered_range!=expected_range:
                    self.assertEqual(entered_range,checked_item['score_range_entered'])
                self.assertAlmostEqual(6000+(exact-60)*3.75,checked['overall']['weighted_numerator'])
                self.assertEqual(checked,engine.calculate_report(checked))
                self.assertEqual(72.3,item['score'])  # The input report remains unchanged.

    def test_regional_source_and_age_scope_cannot_be_omitted(self):
        engine,report=self.audited_report()
        report['benchmarks']={'version':'regional-income-v0.3','self_annual_cny':100000,
          'fx':{'rate_date':'2026-01-02','cny_per_unit':{'CNY':1}},'groups':[{'id':'fiction','income_rows':[
            {'source_amount':100000,'currency':'CNY','frequency':'year'}]}]}
        with self.assertRaisesRegex(ValueError,'source'):engine.calculate_report(report)

    def test_regional_facts_cannot_disagree_with_verified_values(self):
        engine,report=self.audited_report()
        report['assessment_facts']={'height_cm':190}
        with self.assertRaisesRegex(ValueError,'disagree'):engine.calculate_report(report)

    def test_verified_height_interval_survives_local_conversion(self):
        engine,report=self.audited_report()
        report['axes'][0]['items'][0]['evaluation']['numeric_inputs']['height_cm']=[174,176]
        report['axes'][0]['items'][0]['score_range']=[56,64]
        report['benchmarks']={'version':'regional-income-v0.3','self_annual_cny':100000,
          'fx':{'rate_date':'2026-01-02','cny_per_unit':{'CNY':1}},'groups':[{'id':'fiction','income_rows':[
            {'source_amount':100000,'currency':'CNY','frequency':'year','source_url':'https://example.org/fiction',
             'source_value':'虚构税前年工资','age_note':'虚构年龄组'}],
            'character_settings':{'height_reference_cm':170,'height_reference_label':'虚构均高',
              'height_reference_source_url':'https://example.org/fiction'}}]}
        axis=engine.calculate_report(report)['benchmarks']['groups'][0]['character_review']['axes'][0]
        self.assertEqual((62,64),(axis['score_low'],axis['score_high']))

if __name__=='__main__':unittest.main()
