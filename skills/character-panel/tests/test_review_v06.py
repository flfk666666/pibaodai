"""Fictional v0.6 review checks: content scores, evidence and regional coordinates."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
KINDS = {'A1':'height_preference','B2':'bench_platform_proxy','B3':'continuous_swim_task',
         'E1':'saturating_ratio','E2':'saturating_ratio','E3':'saturating_ratio',
         'E4':'debt_burden','E5':'surplus_margin','F1':'gated_capacity'}


def book_fixture():
    return {'version':'character-rules-v0.6','axes':[
        {'id':axis,'name':'Fictional axis '+axis,'weight_units':1,'items':[
            {'id':axis+str(n),'name':'Fictional item','weight_units':1,
             'score_kind':'numeric' if axis+str(n) in KINDS else 'anchor',
             **({'numeric_rule':{'kind':KINDS[axis+str(n)],'params':{}}} if axis+str(n) in KINDS else
                {'anchors':{str(x):'Fictional condition '+str(x) for x in (0,25,50,75,100)}})}
            for n in range(1,7)]} for axis in 'ABCDEF']}


def report_fixture():
    raw = {'A1':{'height_cm':180},
           'B2':{'body_weight_kg':85,'bench_press_1rm_kg':110},
           'B3':{'continuous_swim_m':100},
           'E1':{'after_tax_recurring_income':6000,'necessary_expenses_same_period':3000},
           'E2':{'personal_net_assets_cny':100000,'necessary_annual_expenses_cny':36000},
           'E3':{'available_liquid_funds_cny':18000,'necessary_monthly_expenses_cny':3000},
           'E4':{'confirmed_no_debt':True,'monthly_debt_service_cny':0,'monthly_after_tax_income_cny':6000},
           'E5':{'after_tax_income':6000,'actual_expenses':4000,'same_period':True},
           'F1':{'availability':'self_reported_available','available_support_cny':100000,'necessary_annual_expenses_cny':36000}}
    return {'rating_type':'weighted_character','version':'weighted-character-v0.6',
            'protocol_version':'character-rules-v0.6','source_revision':7,
            'assessment_facts':{'self_annual_cny':100000},
            'axes':[{'id':axis,'items':[{'id':axis+str(n),'selected_anchor':None if axis+str(n) in KINDS else 75,
             **({'numeric_inputs':raw[axis+str(n)]} if axis+str(n) in KINDS else {}),
             'evaluation':{'status':'rated','reason':'Authored fictional task evidence.',
                'evidence':[{'source_type':'fictional_self_report','summary':'Fictional observed task','observed_at':'2025-02-03'}]},
             'coverage':{'level':'usable','scope':'Only the fictional task','gaps':[],'higher_unassessed':True}}
             for n in range(1,7)]} for axis in 'ABCDEF']}


class ReviewV06Tests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('review_v06_tests',ROOT/'scripts/review_v06.py')
        self.engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.engine)
        self.temp = tempfile.TemporaryDirectory(prefix='review-v06-')
        self.rules = Path(self.temp.name)/'rules.json'
        self.rules.write_text(json.dumps(book_fixture()),encoding='utf-8')
        self.patcher = patch.object(self.engine,'RULES_PATH',self.rules)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.addCleanup(self.temp.cleanup)

    def item(self,report,identifier):
        return next(i for a in report['axes'] for i in a['items'] if i['id']==identifier)

    def test_all_positive_weights_and_transparent_calculation(self):
        result = self.engine.calculate_report(report_fixture())
        self.assertEqual(36,len([i for a in result['axes'] for i in a['items']]))
        self.assertAlmostEqual(100,sum(i['global_weight'] for a in result['axes'] for i in a['items']))
        self.assertTrue(all(i['global_weight']>0 for a in result['axes'] for i in a['items']))
        self.assertAlmostEqual(100,result['overall']['known_weight_pct'])
        self.assertAlmostEqual(result['overall']['score_exact'],sum(i['contribution'] for a in result['axes'] for i in a['items']))
        self.assertIn('formula',self.item(result,'E3')['calculation'])

    def test_evidence_count_and_coverage_never_change_supported_anchor(self):
        report = report_fixture()
        before = copy.deepcopy(report)
        self.item(report,'C1')['coverage']['level']='limited'
        limited = self.engine.calculate_report(report)
        self.item(report,'C1')['coverage']['level']='broad'
        self.item(report,'C1')['evaluation']['evidence']*=8
        broad = self.engine.calculate_report(report)
        self.assertEqual(75,self.item(limited,'C1')['score'])
        self.assertEqual(75,self.item(broad,'C1')['score'])
        self.assertEqual(before['axes'][0],report['axes'][0])

    def test_missing_evidence_or_selection_is_unknown_not_basic_or_zero(self):
        report = report_fixture()
        self.item(report,'A2')['evaluation']['evidence']=[]
        self.item(report,'C2')['selected_anchor']=None
        self.item(report,'C2')['followup']={'positive_signal':True,'question':'Which alternative did you exclude?','status':'pending'}
        result = self.engine.calculate_report(report)
        for identifier in ('A2','C2'):
            self.assertIsNone(self.item(result,identifier)['score'])
            self.assertEqual([0,100],self.item(result,identifier)['score_range'])
        self.assertLess(result['overall']['known_weight_pct'],100)
        self.assertGreater(result['overall']['upper'],result['overall']['lower'])

    def test_invalid_anchor_is_rejected(self):
        report = report_fixture()
        self.item(report,'C1')['selected_anchor']=60
        with self.assertRaisesRegex(ValueError,'anchor'):
            self.engine.calculate_report(report)

    def test_evidenced_provisional_null_anchor_keeps_explicit_unresolved_range(self):
        report = report_fixture()
        item = self.item(report,'B5')
        item.update(selected_anchor=None,score_range=[50,75],
                    range_reason='Fictional material supports either 50 or 75; task impact remains unresolved.')
        item['evaluation']['status']='provisional'
        before=copy.deepcopy(report)
        result=self.engine.calculate_report(report)
        pending=self.item(result,'B5')
        self.assertIsNone(pending['score'])
        self.assertEqual([50,75],pending['score_range'])
        self.assertEqual('provisional',pending['evaluation']['status'])
        self.assertEqual([50,75],pending['calculation']['score_range'])
        self.assertEqual(before,report)
        self.assertEqual(result,self.engine.calculate_report(result))

    def test_no_material_or_unexplained_null_cannot_claim_narrowed_range(self):
        for remove_evidence,remove_reason in ((True,False),(False,True)):
            report=report_fixture()
            item=self.item(report,'B5')
            item.update(selected_anchor=None,score_range=[50,75],range_reason='Fictional unresolved neighbouring anchors.')
            item['evaluation']['status']='provisional'
            if remove_evidence:item['evaluation']['evidence']=[]
            if remove_reason:item.pop('range_reason')
            with self.subTest(no_evidence=remove_evidence,no_reason=remove_reason),self.assertRaisesRegex(ValueError,'range'):
                self.engine.calculate_report(report)

    def test_unavailable_family_support_cannot_be_compensated_by_capacity(self):
        report = report_fixture()
        item = self.item(report,'F1')
        item['numeric_inputs']['availability']='unavailable'
        item['numeric_inputs']['available_support_cny']=10000000
        self.assertEqual(0,self.item(self.engine.calculate_report(report),'F1')['score'])
        item['numeric_inputs']['availability']='unknown'
        result = self.item(self.engine.calculate_report(report),'F1')
        self.assertIsNone(result['score'])
        self.assertEqual(0,result['score_range'][0])
        self.assertGreater(result['score_range'][1],90)

    def test_cash_curve_is_continuous_at_former_step_boundary(self):
        report = report_fixture()
        self.item(report,'E3')['numeric_inputs']['available_liquid_funds_cny']=17999
        low = self.item(self.engine.calculate_report(report),'E3')['score']
        self.item(report,'E3')['numeric_inputs']['available_liquid_funds_cny']=18000
        high = self.item(self.engine.calculate_report(report),'E3')['score']
        self.assertGreater(high,low)
        self.assertLess(high-low,.01)

    def test_numeric_intervals_propagate_and_explicit_ranges_cannot_hide_them(self):
        report = report_fixture()
        self.item(report,'E3')['numeric_inputs']['available_liquid_funds_cny']=[3000,6000]
        item = self.item(self.engine.calculate_report(report),'E3')
        self.assertAlmostEqual(25,item['score_range'][0])
        self.assertAlmostEqual(40,item['score_range'][1])
        self.item(report,'E3')['score_range']=[30,35]
        with self.assertRaisesRegex(ValueError,'range'):
            self.engine.calculate_report(report)

    def test_source_is_unchanged_dates_preserved_and_result_idempotent(self):
        report = report_fixture()
        before = copy.deepcopy(report)
        result = self.engine.calculate_report(report)
        self.assertEqual(before,report)
        self.assertEqual(result,self.engine.calculate_report(result))
        self.assertEqual('2025-02-03',self.item(result,'C1')['evaluation']['evidence'][0]['observed_at'])

    def test_regions_only_adjust_height_and_income_not_asset_cash_support(self):
        report = report_fixture()
        report['regions']=[{'id':'fiction','label':'Fictional region','height_reference_cm':170,
             'height_source':{'source_url':'https://example.org/fiction','year':2020},
             'income_rows':[{'label':'Fictional salary','annual_cny':200000,'source_url':'https://example.org/fiction'}],
             'other_coords':{'actual_resource':'unchanged fictional support'}}]
        result = self.engine.calculate_report(report)
        review = result['regions'][0]['review']
        self.assertEqual(6,len(review['axes']))
        self.assertEqual({'A1','E1'},{i['id'] for a in review['axes'] for i in a['items'] if i['score']!=self.item(result,i['id'])['score']})
        self.assertEqual(report['regions'][0]['other_coords'],result['regions'][0]['other_coords'])
        self.assertEqual(10,review['height']['delta_cm'])

    def test_unrounded_case_selection_is_order_independent(self):
        report = report_fixture()
        report['regions']=[{'id':'fiction','label':'Fictional','height_reference_cm':170,
          'income_rows':[{'label':'Lower salary','annual_cny':100000},{'label':'Higher salary','annual_cny':100100}]}]
        first = self.engine.calculate_report(report)['regions'][0]['review']
        report['regions'][0]['income_rows'].reverse()
        second = self.engine.calculate_report(report)['regions'][0]['review']
        self.assertEqual('Higher salary',first['selected_case'])
        self.assertEqual(first['selected_case'],second['selected_case'])

    def test_region_without_income_still_has_six_axes_and_missing_marker(self):
        report = report_fixture()
        report['regions']=[{'id':'fiction','label':'Fictional','income_rows':[]}]
        review = self.engine.calculate_report(report)['regions'][0]['review']
        self.assertEqual(6,len(review['axes']))
        self.assertIsNone(self.item({'axes':review['axes']},'E1')['score'])
        self.assertEqual('unavailable',review['income']['status'])
        self.assertTrue(review['limitations'])


if __name__ == '__main__':
    unittest.main()
