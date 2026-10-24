import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from mercy.town.factory import build
from mercy.town.harness import run,interview_progress
from mercy.rl.public import Notebook
from mercy.town.tasks import TASKS,description


class InterviewDepthTests(unittest.TestCase):
    def test_interview_summary_uses_only_received_answers_and_acquired_sources(self):
        book=Notebook({'now':{}})
        for question,answer,show in [('When did you arrive?',{'words':'After the cry.','recollections':[{'basis':'hearsay','text':'Someone called for help.'}],'private_state':'must-not-appear'},[]),('What did you personally see?',{'words':'A doorway.','recollections':[{'basis':'direct_observation','text':'I saw the doorway.'}]},['r1']),('What did you personally see?',{'error':'Person not here'},[])]:
            book.observe({'tool':'ask','args':{'pid':'witness','question':question,'show':show}},answer)
        rows=interview_progress(book);self.assertEqual(rows[0]['questions_asked'],2)
        self.assertEqual(rows[0]['unique_questions'],2);self.assertEqual(rows[0]['firsthand_accounts'],1)
        self.assertEqual(rows[0]['shown_records'],['r1']);self.assertNotIn('must-not-appear',json.dumps(rows))
        for word in ('trust','fear','eligible_recall_ids','guilty'):self.assertNotIn(word,json.dumps(rows))

    def test_a_person_can_be_questioned_more_than_twice(self):
        world=build('lantern_room',7);world.step('people_here',{})
        floor=world.step('search',{'surface':'floor'})
        for question in ('Where were you standing?','What happened next?','What did you personally see?','Which details did you hear from others?'):
            response=world.step('ask',{'pid':'nell','question':question,'show':[r['record_id'] for r in floor['findings']],'approach':'reassure'})
            self.assertNotIn('error',response)
        self.assertEqual(len(world.states['nell']['dialogue']),4)

    def test_multiple_materials_and_internal_work_do_not_consume_extra_replies(self):
        class Handovers:
            seed=7;ended=False;result=None
            def opening(self):return {'task':{'task_id':'fixture','scope':'Check acquired material.'},'now':{}}
            def state_hash(self):return 'hash'
            def step(self,name,args):
                if name=='ask':return {'record_id':'r1','words':'Here are the records.','handed_over':[{'record_id':'r'+str(i),'description':'An acquired document.'} for i in range(2,7)]}
                if name=='submit_report':self.ended=True;self.result={'score':0.,'success':False};return {'submitted':True}
                return {'notice':'Observed'}
        calls=[]
        def transport(messages,tools,timeout):
            names=['ask','look','look'] if not calls else ['submit_report'];calls.append(messages)
            reply={'choices':[{'message':{'tool_calls':[{'function':{'name':name,'arguments':json.dumps({'findings':[]} if name=='submit_report' else {'pid':'person','question':'What can you provide?'} if name=='ask' else {})}} for name in names]}}]}
            return reply,json.dumps(reply)
        with TemporaryDirectory() as folder:
            p=Path(folder);(p/'append.txt').write_text('Investigate with the public tools.\n')
            with patch.dict(os.environ,{'APPEND_FILE':str(p/'append.txt')}):summary=run(Handovers(),p,steps=2,transport=transport)
            rows=[json.loads(s) for s in (p/'episode.jsonl').read_text().splitlines()]
        self.assertEqual(summary['detective_model_replies'],2);self.assertEqual(len(rows),2)
        self.assertEqual(len(rows[0]['parsed_actions']),3)
        self.assertEqual(len(rows[0]['tool_result'][0]['handed_over']),5)
        self.assertIn('public interview history',calls[1][-1]['content'])

    def test_briefings_exist_without_private_solution_or_acquired_evidence(self):
        for task in TASKS:
            brief=description(task)['briefing'];self.assertGreater(len(brief),150)
            self.assertNotIn('required_claims',brief)
            opening=build(task,7).opening();self.assertEqual(opening['task']['briefing'],brief)
            self.assertNotIn('Savitri',brief);self.assertNotIn('Vedant',brief)
