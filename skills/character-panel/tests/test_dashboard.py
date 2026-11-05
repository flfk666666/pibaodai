"""Rendering boundaries for authored, fictional character cards."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_dashboard.py"
TEMPLATE = '<!doctype html><script id="profile-data" type="application/json">__REPORT_JSON__</script>'


def fixture():
    return {
        "rating_type": "subjective", "version": "subjective-review-v0.1",
        "title": "稳步成长", "name": "演示角色", "date": "2026-01-01",
        "meta": [], "intro": "编写的演示", "facts": [],
        "axes": [{"id": axis, "name": axis, "short": axis, "score": 60,
                  "kicker": "示例", "evidence": "编写的材料", "confidence": "待验证",
                  "summary": "示例", "reasons": [], "watch": [], "actions": []}
                 for axis in "ABCDEF"],
        "priorities": [], "method": {"label": "AI主观初评", "text": "非排名"},
        "skipped": [],
    }


class DashboardTests(unittest.TestCase):
    def life_fixture(self):
        report=json.loads((ROOT/'examples'/'review-v06.json').read_text(encoding='utf-8'))
        report['presentation_version']='life-direction-v0.8'
        report['life_direction']={'version':'life-direction-report-v1','source_revision':3,
            'source_path':'life-direction/current.md','title':'人生方向',
            'headline':'已有行动，方向待梳理','summary':'编写的虚构人物演示',
            'overview':{'desired_life':None,'confirmation':'尚待本人回答'},
            'observations':[{'label':'持续与调节','status':'待补','summary':'未知不是零分','score':None}],
            'directions':[{'id':'album','title':'整理家人照片','kind':'goal','score':None,
                'axis_links':[{'axis_id':'D','role':'支持','text':'虚构任务练习'}]}],
            'interview':{'direction_id':'life-overview','section_id':'L1','prompt':'你想过怎样的生活？'}}
        return report

    def test_life_layer_preserves_six_axes_and_escapes_raw_answers(self):
        report=self.life_fixture();module=self.renderer()
        report['life_direction']['overview']['desired_life']='</script><img src=x>'
        before=copy.deepcopy(report)
        old=copy.deepcopy(report);old.pop('life_direction');old['presentation_version']='joint-profile-v0.7'
        expected=json.loads(re.search(r'type="application/json">(.*?)</script>',module.build_dashboard(old,TEMPLATE),re.S).group(1))
        html=module.build_dashboard(report,TEMPLATE)
        rendered=json.loads(re.search(r'type="application/json">(.*?)</script>',html,re.S).group(1))
        self.assertEqual(expected['axes'],rendered['axes'])
        self.assertEqual(expected['overall'],rendered['overall'])
        self.assertEqual(expected.get('regions'),rendered.get('regions'))
        self.assertEqual(before,report)
        self.assertEqual(report['life_direction'],rendered['life_direction'])
        self.assertNotIn('</script><img',html)

    def test_life_layer_requires_separate_state_revision_and_no_invented_scores(self):
        changes=[lambda r:r.pop('life_direction'),
            lambda r:r['life_direction'].update(source_revision=0),
            lambda r:r['life_direction']['observations'][0].update(score=60),
            lambda r:r['life_direction']['directions'][0].update(score=100),
            lambda r:r['life_direction']['directions'][0]['axis_links'][0].update(axis_id='G'),
            lambda r:r['life_direction']['directions'].append(copy.deepcopy(r['life_direction']['directions'][0]))]
        for change in changes:
            r=self.life_fixture();change(r)
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.renderer().build_dashboard(r,TEMPLATE)

    def improvement_fixture(self):
        report=fixture()
        report['recommendation_protocol']='real-life-improvement-v1'
        for axis in report['axes']:
            axis.pop('actions',None)
            axis['improvement_plan']={'title':'把普通任务做得更稳','target_items':[axis['id']+'3'],
                'current_gap':'虚构人物需要在实际任务里练习，而不是补交材料。',
                'target':'能在普通任务中独立完成所选环节。',
                'standard_basis':'对应该任务的公开行为锚点，练习周期不是评分门槛。',
                'steps':['在真实任务里实行一次事先约定的做法。'],
                'success':'所选实际任务能完成，而不是交一份评测记录。',
                'sources':[]}
            axis['assessment_maintenance']=['旧材料的日期仍待核，不作为提升动作。']
        return report

    def test_real_life_plans_keep_maintenance_separate_and_escape_untrusted_text(self):
        report=self.improvement_fixture()
        report['axes'][0]['improvement_plan']['title']='</script><img src=x>'
        before=copy.deepcopy(report)
        output=self.renderer().build_dashboard(report,TEMPLATE)
        result=json.loads(re.search(r'type="application/json">(.*?)</script>',output,re.S).group(1))
        self.assertEqual(before,result)
        self.assertEqual(before,report)
        self.assertNotIn('</script><img',output)

    def test_explicit_improvement_protocol_rejects_incomplete_or_mixed_plans(self):
        bad_changes=[
            lambda r:r['axes'][0]['improvement_plan'].pop('success'),
            lambda r:r['axes'][0]['improvement_plan'].update(target_items=['F3']),
            lambda r:r['axes'][0]['improvement_plan'].update(steps=[]),
            lambda r:r['axes'][0]['improvement_plan'].update(sources=[{'title':'bad','url':'javascript:alert(1)'}]),
            lambda r:r['axes'][0].update(actions=['填好表格就当作提升']),
            lambda r:r['axes'][0].update(assessment_maintenance='not a list'),
        ]
        for change in bad_changes:
            report=self.improvement_fixture();change(report)
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.renderer().build_dashboard(report,TEMPLATE)

    def test_joint_presentation_adds_context_without_rescoring_or_mutating_input(self):
        report=json.loads((ROOT/'examples'/'review-v06.json').read_text(encoding='utf-8'))
        module=self.renderer()
        plain=json.loads(re.search(r'type="application/json">(.*?)</script>',module.build_dashboard(report,TEMPLATE),re.S).group(1))
        report['presentation_version']='joint-profile-v0.7'
        report['financial_facts']={'cash_total_cny':60000,'liquid_cash_cny':[10000,20000],
            'monthly_necessary_cny':5000,'personal_net_assets_cny':90000,'family_support_cny':20000,
            'family_available':True,'family_support_within_days':7}
        report['holistic_summary']={'verdict':'</script><img src=x>'}
        before=copy.deepcopy(report)
        output=module.build_dashboard(report,TEMPLATE)
        result=json.loads(re.search(r'type="application/json">(.*?)</script>',output,re.S).group(1))
        self.assertIn('joint_assessment',result)
        self.assertEqual(6,len(result['joint_assessment']['axes']))
        self.assertEqual([a['score'] for a in plain['axes']],[a['score'] for a in result['axes']])
        self.assertEqual([40000,50000],result['financial_context']['funding_layers']['restricted_cash_cny'])
        self.assertEqual(before,report)
        self.assertEqual(report['holistic_summary'],result['holistic_summary'])
        self.assertNotIn('</script><img',output)

    def test_v06_routes_raw_items_to_new_engine_and_skips_legacy_income(self):
        fixture_spec=importlib.util.spec_from_file_location('v06_dashboard_fixture',ROOT/'tests'/'test_review_v06.py')
        fixtures=importlib.util.module_from_spec(fixture_spec)
        fixture_spec.loader.exec_module(fixtures)
        report=fixtures.report_fixture()
        report.update(title='虚构角色',name='Fictional adult',date='2025-02-03',
                      method={'label':'Experimental v0.6 content review'},intro='</script><img src=x onerror=alert(1)>')
        # A carried historical block must not trigger legacy processing in v0.6.
        report['benchmarks']={'version':'regional-income-v0.3','groups':'not a legacy input'}
        before=copy.deepcopy(report)
        module=self.renderer()
        original=module.importlib.util.spec_from_file_location
        called=[]
        def trace(name,path,*args,**kwargs):
            called.append(Path(path).name)
            return original(name,path,*args,**kwargs)
        with patch.object(module.importlib.util,'spec_from_file_location',side_effect=trace):
            output=module.build_dashboard(report,TEMPLATE)
        result=json.loads(re.search(r'type="application/json">(.*?)</script>',output,re.S).group(1))
        self.assertEqual(['review_v06.py'],called)
        self.assertEqual(6,len(result['axes']))
        self.assertEqual(36,result['overall']['known_items'])
        self.assertTrue(all(type(axis['score']) is int for axis in result['axes']))
        self.assertEqual(report['benchmarks'],result['benchmarks'])
        self.assertNotIn('</script><img',output)
        self.assertEqual(before,report)

    def test_weighted_v04_recomputes_36_items_and_overall(self):
        module=self.renderer();report=fixture()
        report.update(rating_type='weighted_character',version='weighted-character-v0.4')
        for axis,weight in zip(report['axes'],[20,15,15,20,20,10]):
            axis['axis_weight']=weight
            axis['items']=[{'id':axis['id']+str(index+1),'weight':item_weight,'score':60,'anchor':'虚构锚点','reason':'编写材料'}
                           for index,item_weight in enumerate([20,20,15,15,15,15])]
        output=module.build_dashboard(report,TEMPLATE)
        result=json.loads(re.search(r'type="application/json">(.*?)</script>',output,re.S).group(1))
        self.assertEqual(60,result['overall']['score'])
        self.assertEqual(36,result['overall']['known_items'])

    def test_regional_income_is_recalculated_without_changing_axes(self):
        module = self.renderer()
        report = fixture()
        report['benchmarks'] = {'version': 'regional-income-v0.3', 'self_annual_cny': 100000,
            'fx': {'rate_date': '2026-01-02', 'cny_per_unit': {'CNY': 1}},
            'groups': [{'id': 'fiction', 'regional_score': {'score': 3},
                        'income_rows': [{'label': '虚构参照', 'source_amount': 50000, 'currency': 'CNY', 'frequency': 'year'}]}]}
        output = module.build_dashboard(report, TEMPLATE)
        result = json.loads(re.search(r'type="application/json">(.*?)</script>', output, re.S).group(1))
        self.assertEqual(80, result['benchmarks']['groups'][0]['regional_score']['score'])
        self.assertEqual([60] * 6, [axis['score'] for axis in result['axes']])
        self.assertEqual(3, report['benchmarks']['groups'][0]['regional_score']['score'])

    def renderer(self):
        self.assertTrue(SCRIPT.is_file(), "The offline dashboard renderer is not implemented yet")
        spec = importlib.util.spec_from_file_location("character_dashboard", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_untrusted_text_cannot_end_the_embedded_data_script(self):
        module = self.renderer()
        report = fixture()
        report["intro"] = '</script><img src=x onerror="alert(1)">\u2028'
        before = copy.deepcopy(report)
        output = module.build_dashboard(report, TEMPLATE)
        self.assertNotIn('</script><img', output)
        encoded = re.search(r'type="application/json">(.*?)</script>', output, re.S).group(1)
        self.assertEqual(report, json.loads(encoded))
        self.assertEqual(before, report)

    def test_missing_axis_or_invalid_scores_are_rejected(self):
        module = self.renderer()
        for bad_score in (True, 101, -1, float("nan"), "75"):
            report = fixture()
            report["axes"][0]["score"] = bad_score
            with self.subTest(score=bad_score), self.assertRaises(ValueError):
                module.build_dashboard(report, TEMPLATE)
        report = fixture()
        report["axes"].pop()
        with self.assertRaises(ValueError):
            module.build_dashboard(report, TEMPLATE)

    def test_unknown_axis_stays_null_and_headline_has_a_hard_limit(self):
        module = self.renderer()
        report = fixture()
        report["axes"][0]["score"] = None
        output = module.build_dashboard(report, TEMPLATE)
        encoded = re.search(r'type="application/json">(.*?)</script>', output, re.S).group(1)
        self.assertIsNone(json.loads(encoded)["axes"][0]["score"])
        report["title"] = "一二三四五六七八九十一"
        with self.assertRaises(ValueError):
            module.build_dashboard(report, TEMPLATE)

    def test_anchored_report_uses_items_instead_of_an_invented_axis_number(self):
        module = self.renderer()
        report = fixture()
        report.update(rating_type="anchored_review", version="anchored-review-v0.2", baseline=60)
        for axis in report["axes"]:
            axis["score"] = 99
            axis["items"] = [{"id": axis["id"] + "1", "weight": 100, "score": 60,
                              "anchor": "编写的够用锚点", "reason": "虚构材料达到此锚点"}]
        output = module.build_dashboard(report, TEMPLATE)
        encoded = re.search(r'type="application/json">(.*?)</script>', output, re.S).group(1)
        result = json.loads(encoded)
        self.assertEqual(60, result["axes"][0]["score"])
        self.assertEqual(99, report["axes"][0]["score"])
        report = fixture()
        report["rating_type"] = "official-percentile"
        with self.assertRaises(ValueError):
            module.build_dashboard(report, TEMPLATE)


if __name__ == "__main__":
    unittest.main()
