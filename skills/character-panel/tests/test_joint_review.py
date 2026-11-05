"""Authored fictional checks for the non-compensatory joint interpretation layer."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def fixture(score=75):
    return {'version':'weighted-character-v0.6','source_revision':9,
            'axes':[{'id':axis,'name':'Fictional '+axis,'score':score,
                     'items':[{'id':axis+str(n),'name':'Fictional '+axis+str(n),
                               'score':score,'score_range':[score,score],
                               'coverage':{'level':'usable','scope':'Authored fictional task',
                                           'gaps':[],'higher_unassessed':True}}
                              for n in range(1,7)]} for axis in 'ABCDEF']}


def set_score(report, identifier, score, bounds=None):
    item=next(item for axis in report['axes'] for item in axis['items'] if item['id']==identifier)
    item['score']=score
    item['score_range']=bounds if bounds is not None else ([score,score] if score is not None else [0,100])


class JointTests(unittest.TestCase):
    def engine(self):
        path=ROOT/'scripts/joint_review.py'
        self.assertTrue(path.exists(),'Joint interpretation layer is not implemented')
        spec=importlib.util.spec_from_file_location('joint_review',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def axis(self, result, axis):
        return next(a for a in result['joint_assessment']['axes'] if a['id']==axis)

    def test_tall_alone_is_not_overall_appearance_strength(self):
        data=fixture();set_score(data,'A1',100);set_score(data,'A2',25);set_score(data,'A3',25)
        axis=self.axis(self.engine().calculate_joint(data),'A')
        self.assertNotEqual('multi_strength',axis['state_code'])
        self.assertEqual('limited',next(c for c in axis['checks'] if c['id']=='A.profile')['result'])

    def test_alternative_appearance_route_does_not_require_tallness(self):
        data=fixture();set_score(data,'A1',25)
        axis=self.axis(self.engine().calculate_joint(data),'A')
        self.assertEqual('multi_strength',axis['state_code'])
        self.assertEqual('met',next(c for c in axis['checks'] if c['id']=='A.profile')['result'])

    def test_missing_key_is_unknown_not_failure_or_low_ability(self):
        data=fixture();set_score(data,'A2',None)
        axis=self.axis(self.engine().calculate_joint(data),'A')
        self.assertEqual('pending',axis['state_code'])
        self.assertEqual('unknown',next(c for c in axis['checks'] if c['id']=='A.profile')['result'])
        self.assertTrue(any('A2' in text for text in axis['unknowns']))
        self.assertFalse(any('A2' in text for text in axis['bottlenecks']))

    def test_recovery_constraint_is_not_cancelled_by_strong_lift(self):
        data=fixture();set_score(data,'B2',100);set_score(data,'B5',50)
        axis=self.axis(self.engine().calculate_joint(data),'B')
        self.assertEqual('strength_with_constraint',axis['state_code'])
        self.assertTrue(any('B5' in text for text in axis['bottlenecks']))

    def test_debt_or_cash_alone_cannot_establish_whole_financial_strength(self):
        data=fixture(score=25);set_score(data,'E3',100);set_score(data,'E4',100)
        axis=self.axis(self.engine().calculate_joint(data),'E')
        self.assertNotEqual('multi_strength',axis['state_code'])
        self.assertTrue(axis['bottlenecks'])

    def test_unknown_surplus_blocks_full_finance_claim_but_keeps_known_floor(self):
        data=fixture();set_score(data,'E5',None)
        axis=self.axis(self.engine().calculate_joint(data),'E')
        self.assertEqual('pending',axis['state_code'])
        self.assertTrue(axis['strengths'])
        self.assertTrue(any('E5' in text for text in axis['unknowns']))

    def test_money_and_housing_do_not_erase_lack_of_care(self):
        data=fixture();set_score(data,'F1',100);set_score(data,'F2',100);set_score(data,'F3',25)
        axis=self.axis(self.engine().calculate_joint(data),'F')
        self.assertEqual('strength_with_constraint',axis['state_code'])
        self.assertTrue(any('F3' in text for text in axis['bottlenecks']))

    def test_boundary_uncertainty_stays_unknown_not_false_shortfall(self):
        data=fixture();set_score(data,'B4',75,[50,75])
        check=next(c for c in self.axis(self.engine().calculate_joint(data),'B')['checks'] if c['id']=='B.activity')
        self.assertEqual('unknown',check['result'])

    def test_all_36_items_are_used_and_original_report_is_unchanged(self):
        data=fixture();before=deepcopy(data);engine=self.engine();result=engine.calculate_joint(data)
        self.assertEqual(before,data)
        self.assertEqual(before['axes'],result['axes'])
        ids={identifier for axis in result['joint_assessment']['axes'] for check in axis['checks'] for identifier in check['item_ids']}
        self.assertEqual({a+str(n) for a in 'ABCDEF' for n in range(1,7)},ids)
        self.assertEqual(result,engine.calculate_joint(result))
        self.assertIn('not_population_standard',result['joint_assessment']['rule_origin'])

    def test_verified_problem_solving_chain_is_distinct_from_management_score(self):
        data=fixture();set_score(data,'C3',25);set_score(data,'D4',100)
        overall=self.engine().calculate_joint(data)['joint_assessment']['overall']
        chain=next(c for c in overall['established_chains'] if c['id']=='thinking_to_delivery')
        self.assertEqual('limited',chain['result'])
        self.assertTrue(any('C3' in text for text in overall['constraints']))

    def test_missing_language_is_not_invented_as_low_capability(self):
        result=self.engine().calculate_joint(fixture())
        overall=result['joint_assessment']['overall']
        self.assertTrue(any('语言' in text for text in overall['unknowns']))
        self.assertFalse(any('语言能力低' in text for text in overall['constraints']))

    def test_regions_use_same_rules_without_overwriting_scores(self):
        data=fixture();regional=deepcopy(data['axes']);regional[0]['items'][0]['score']=50;regional[0]['items'][0]['score_range']=[50,50]
        data['regions']=[{'id':'fiction','review':{'axes':regional,'overall':{'score':70}}}]
        original=deepcopy(data['regions'])
        result=self.engine().calculate_joint(data)
        self.assertEqual(original[0]['review']['axes'],result['regions'][0]['review']['axes'])
        self.assertEqual('multi_strength',result['regions'][0]['review']['joint_assessment']['axes'][0]['state_code'])

    def test_regional_wage_coordinate_is_not_called_living_expense_coverage(self):
        data=fixture();regional=deepcopy(data['axes'])
        item=regional[4]['items'][0]
        item.update(score=30,score_range=[30,30],score_origin='regional_coordinate',
                    calculation={'inputs':{'own_gross_annual_cny':[90000,90000],'reference_gross_annual_cny':210000}})
        data['regions']=[{'id':'fiction','review':{'axes':regional,'overall':{'score':70}}}]
        result=self.engine().calculate_joint(data)
        joint=result['regions'][0]['review']['joint_assessment']
        axis=next(a for a in joint['axes'] if a['id']=='E')
        base=self.axis(result,'E')
        check=next(c for c in axis['checks'] if c['id']=='E.income')
        self.assertEqual(base['state_code'],axis['state_code'])
        self.assertEqual(base['checks'],axis['checks'])
        self.assertEqual(75,next(o for o in check['observed'] if o['id']=='E1')['score'])
        reference=axis['contextual_references'][0]
        self.assertEqual('limited',reference['result'])
        self.assertIn('工资',reference['label'])
        self.assertAlmostEqual(90000/210000,reference['observed']['ratio'])
        self.assertFalse(any('E1' in t for t in axis['bottlenecks']))
        self.assertFalse(any('E1' in t for t in joint['overall']['constraints']))
        self.assertEqual(regional,result['regions'][0]['review']['axes'])

    def test_regional_height_prominence_does_not_replace_global_appearance_preference(self):
        data=fixture();set_score(data,'A1',80);set_score(data,'A5',50)
        regional=deepcopy(data['axes'])
        regional[0]['items'][0].update(score=40,score_range=[40,40],score_origin='regional_coordinate')
        data['regions']=[{'id':'fiction','height_reference_cm':180,'review':{'axes':regional,'height':{'height_cm':175,'reference_cm':180,'delta_cm':-5,'score':40}}}]
        result=self.engine().calculate_joint(data)
        base=self.axis(result,'A');local=result['regions'][0]['review']['joint_assessment']['axes'][0]
        self.assertEqual(base['checks'],local['checks'])
        self.assertEqual(base['state_code'],local['state_code'])
        self.assertEqual('limited',local['contextual_references'][0]['result'])
        self.assertIn('吸引力',local['contextual_references'][0]['reason'])


if __name__=='__main__':unittest.main()
