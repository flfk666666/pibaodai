"""Life-direction checkpoints, using authored fictional answers only."""
from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))


def fact(value, observed_at=None):
    return {'value':value,'observed_at':observed_at,'source':'authored_fictional_case'}


class LifeStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='life-direction-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)/'private-profile'

    def engine(self):
        self.assertTrue((ROOT/'scripts/life_store.py').exists(),'Life store is not implemented')
        return importlib.import_module('life_store')

    def start(self):
        self.module=self.engine();self.store=self.module.LifeStore(self.root)
        return self.store.init('fictional')

    def test_initial_state_has_five_sections_and_no_life_score(self):
        state=self.start()
        self.assertEqual('life-direction-v1',state['question_version'])
        self.assertEqual('life-overview',state['next_direction_id'])
        self.assertEqual('L1',state['next_section'])
        self.assertEqual('人生方向总览',state['directions']['life-overview']['title'])
        sections=state['directions']['life-overview']['sections']
        self.assertEqual(['L1','L2','L3','L4','L5'],list(sections))
        self.assertTrue(all(s['score'] is None for s in sections.values()))
        self.assertEqual(1,state['revision'])
        self.assertEqual(state,self.store.load())

    def test_partial_answer_survives_restart_with_cursor_and_date(self):
        self.start()
        saved=self.store.record('life-overview','L1',{'inputs':{'preferred_life':fact('Fictional quiet work life','2025-02-03')}},1)
        fresh=self.module.LifeStore(self.root)
        self.assertEqual(saved,fresh.load())
        self.assertEqual('partial',saved['directions']['life-overview']['sections']['L1']['input_status'])
        self.assertEqual('L1',fresh.status()['next_section'])
        self.assertTrue(fresh.status()['next_prompt'])

    def test_completion_does_not_require_filling_suggested_fields(self):
        self.start()
        state=self.store.record('life-overview','L1',{'inputs':{'current_direction':fact(None)},'input_status':'complete'},1)
        self.assertEqual('complete',state['directions']['life-overview']['sections']['L1']['input_status'])
        self.assertEqual('L2',state['next_section'])
        self.assertIsNone(state['directions']['life-overview']['sections']['L1']['inputs']['current_direction']['observed_at'])

    def test_local_correction_merges_inputs_preserves_other_sections_and_history(self):
        self.start()
        old=self.store.record('life-overview','L1',{'inputs':{'current_direction':fact('Fictional A','2025-02-03'),'reason':fact('curiosity')},'input_status':'complete'},1)
        second=self.store.record('life-overview','L2',{'inputs':{'formed_at':fact(None)}},2)
        saved=self.store.record('life-overview','L1',{'inputs':{'current_direction':fact('Fictional B','2025-02-04')}},3)
        self.assertEqual(second['directions']['life-overview']['sections']['L2'],saved['directions']['life-overview']['sections']['L2'])
        self.assertEqual(old['directions']['life-overview']['sections']['L1']['inputs']['reason'],saved['directions']['life-overview']['sections']['L1']['inputs']['reason'])
        versions=[self.module.parse(p.read_text(encoding='utf-8')) for p in (self.root/'life-direction/history').glob('*.md')]
        self.assertTrue(any(s==old for s in versions))
        self.assertTrue(any(s==second for s in versions))

    def test_stale_revision_and_writer_lock_refuse_overwrite(self):
        self.start();other=self.module.LifeStore(self.root)
        state=self.store.record('life-overview','L1',{'observations':'fictional'},1)
        with self.assertRaises(self.module.LifeError):other.record('life-overview','L1',{'observations':'lost'},1)
        self.assertEqual(state,self.store.load())
        lock=self.root/'life-direction/.write.lock';lock.write_text('{}',encoding='utf-8')
        with self.assertRaises(self.module.LifeError):self.store.pause(2)
        self.assertEqual(state,self.store.load())

    def test_skip_pause_resume_preserves_observation_dates_and_position(self):
        self.start()
        self.store.record('life-overview','L1',{'inputs':{'current_direction':fact('Fictional A','2025-02-03')},'input_status':'complete'},1)
        deferred=self.store.record('life-overview','L2',{'input_status':'deferred','observations':'date unknown'},2)
        paused=self.store.pause(3);resumed=self.store.resume(4)
        self.assertEqual('L3',deferred['next_section'])
        self.assertEqual('paused',paused['assessment_status'])
        self.assertEqual('in_progress',resumed['assessment_status'])
        self.assertEqual(paused['directions'],resumed['directions'])
        self.assertEqual('L3',resumed['next_section'])
        self.assertEqual('2025-02-03',resumed['directions']['life-overview']['sections']['L1']['inputs']['current_direction']['observed_at'])

    def test_add_direction_and_explicit_cursor_do_not_change_overview(self):
        before=self.start()
        added=self.store.add_direction('fictional-interest','Fictional interest','interest',1)
        self.assertEqual(before['directions']['life-overview'],added['directions']['life-overview'])
        state=self.store.record('fictional-interest','L1',{'inputs':{'preference':fact('Fictional preference')},'next_direction_id':'life-overview','next_section':'L4'},2)
        self.assertEqual('life-overview',state['next_direction_id'])
        self.assertEqual('L4',state['next_section'])

    def test_complete_group_stays_in_selected_direction_before_other_directions(self):
        self.start();self.store.add_direction('fictional-interest','Fictional interest','interest',1)
        state=self.store.record('fictional-interest','L1',{'input_status':'complete'},2)
        self.assertEqual('fictional-interest',state['next_direction_id'])
        self.assertEqual('L2',state['next_section'])

    def test_existing_six_axis_file_is_unchanged_and_identity_must_match(self):
        module=self.engine();self.root.mkdir(parents=True)
        document='six-axis fixture\n<!-- character-panel-state:v1 -->\n```json\n'+json.dumps({'profile_id':'fictional'})+'\n```\n'
        current=self.root/'current.md';current.write_text(document,encoding='utf-8')
        store=module.LifeStore(self.root)
        with self.assertRaises(module.LifeError):store.init('different')
        store.init('fictional');store.record('life-overview','L1',{'observations':'fictional'},1)
        self.assertEqual(document,current.read_text(encoding='utf-8'))

    def test_corrupt_or_duplicate_state_is_never_reset(self):
        self.start();current=self.root/'life-direction/current.md'
        corrupted=current.read_text(encoding='utf-8')+'\n'+self.module.MARKER
        current.write_text(corrupted,encoding='utf-8')
        with self.assertRaises(self.module.LifeError):self.store.load()
        with self.assertRaises(self.module.LifeError):self.store.init('fictional')
        self.assertEqual(corrupted,current.read_text(encoding='utf-8'))

    def test_missing_current_with_history_cannot_be_reinitialized(self):
        self.start();self.store.record('life-overview','L1',{'observations':'fictional'},1)
        self.store.current.unlink()
        with self.assertRaises(self.module.LifeError):self.store.init('fictional')

    def test_non_null_manual_scores_and_malformed_identity_are_rejected(self):
        state=self.start();state['score']=80
        self.store.current.write_text(self.module.render(state),encoding='utf-8')
        with self.assertRaises(self.module.LifeError):self.store.load()
        other_root=Path(self.temporary.name)/'malformed-profile';other_root.mkdir()
        (other_root/'current.md').write_text('<!-- character-panel-state:v1 -->\n```json\n[]\n```',encoding='utf-8')
        with self.assertRaises(self.module.LifeError):self.module.LifeStore(other_root).init('fictional')

    def test_public_paths_and_invalid_ids_dates_scores_are_rejected(self):
        module=self.engine()
        with self.assertRaises(module.LifeError):module.LifeStore(ROOT/'private-data')
        self.start()
        for payload in ({'score':75},{'inputs':{'formed_at':fact('unknown','last year')}},{'next_direction_id':'missing','next_section':'L1'}):
            with self.subTest(payload=payload),self.assertRaises(module.LifeError):self.store.record('life-overview','L1',payload,1)
        with self.assertRaises(module.LifeError):self.store.add_direction('../escape','Fictional','goal',1)
        with self.assertRaises(module.LifeError):self.store.add_direction('valid','Fictional','invalid',1)
        self.assertEqual(1,self.store.load()['revision'])

    def test_failed_atomic_replace_preserves_last_good_current(self):
        old=self.start();original=self.store._replace_text
        def fail_current(destination,text):
            if destination==self.store.current:raise OSError('authored write failure')
            return original(destination,text)
        with mock.patch.object(self.store,'_replace_text',side_effect=fail_current):
            with self.assertRaises(OSError):self.store.record('life-overview','L1',{'observations':'fictional'},1)
        self.assertEqual(old,self.store.load())
        self.assertFalse((self.root/'life-direction/.write.lock').exists())

    def test_cli_restart_and_render(self):
        self.engine()
        def run(*args):
            result=subprocess.run([sys.executable,str(ROOT/'scripts/life.py'),'--state-dir',str(self.root),*args],capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1'},timeout=20)
            self.assertEqual(0,result.returncode,result.stderr)
            return result.stdout
        first=json.loads(run('init','--profile-id','fictional'))
        self.assertEqual(1,first['revision'])
        status=json.loads(run('status'))
        self.assertEqual('L1',status['next_section'])
        self.assertIn('人生方向',run('render'))
        self.assertEqual('paused',json.loads(run('pause','--expect-revision','1'))['state']['assessment_status'])
        self.assertEqual('in_progress',json.loads(run('resume','--expect-revision','2'))['state']['assessment_status'])
        payload=Path(self.temporary.name)/'payload.json'
        payload.write_text(json.dumps({'inputs':{'reason':fact('Fictional reason','2025-02-03')},'input_status':'complete'}),encoding='utf-8')
        saved=json.loads(run('record','--direction','life-overview','--section','L1','--payload-file',str(payload),'--expect-revision','3'))
        self.assertEqual('L2',saved['next_section'])
        added=json.loads(run('add-direction','--id','fictional-goal','--title','Fictional goal','--kind','goal','--expect-revision','4'))
        self.assertEqual('fictional-goal',added['next_direction_id'])

    def test_two_cli_writers_with_same_revision_never_lose_an_answer(self):
        self.start()
        processes=[]
        for index in range(2):
            payload=Path(self.temporary.name)/f'writer-{index}.json'
            payload.write_text(json.dumps({'observations':f'fictional writer {index}'}),encoding='utf-8')
            args=[sys.executable,str(ROOT/'scripts/life.py'),'--state-dir',str(self.root),'record','--direction','life-overview','--section','L1','--payload-file',str(payload),'--expect-revision','1']
            processes.append(subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1'}))
        outputs=[p.communicate(timeout=20) for p in processes]
        self.assertEqual([0,2],sorted(p.returncode for p in processes))
        self.assertEqual(2,self.store.load()['revision'])
        winner=next(json.loads(out) for p,(out,err) in zip(processes,outputs) if p.returncode==0)
        self.assertEqual(winner['state'],self.store.load())


if __name__=='__main__':unittest.main()
