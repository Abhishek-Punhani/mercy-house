import unittest
from mercy.env import Environment
from mercy.baselines import gates, reference

class WorldTests(unittest.TestCase):
    def test_gates_all_tasks_and_roles(self):
        for row in gates(range(12)):
            self.assertTrue(row['passed'],row)
    def test_seed_replay(self):
        a,b=Environment(seed=7),Environment(seed=7)
        self.assertEqual(a.state_hash(),b.state_hash())
        for e in list(a.case['evidence'].values())[:5]:
            self.assertEqual(a.step(e['action'],{'evidence_id':e['id']}),b.step(e['action'],{'evidence_id':e['id']}))
            self.assertEqual(a.state_hash(),b.state_hash())
    def test_guess_without_evidence(self):
        env=Environment()
        env.step('submit_report',{'claims':[{'claim_id':'savitri_killed_mira','status':'established','evidence_ids':env.case['proofs']['savitri_killed_mira']}]})
        self.assertEqual(env.result['score'],0)
    def test_wrong_culprit_with_all_evidence(self):
        env=Environment()
        for e in env.case['evidence'].values(): env.step(e['action'],{'evidence_id':e['id']})
        env.step('submit_report',{'claims':[{'claim_id':'dev_killed_mira','status':'established','evidence_ids':env.state['acquired']}]})
        self.assertEqual(env.result['score'],0)
    def test_invalid_paths_do_not_mutate_acquired(self):
        env=Environment(); before=list(env.state['acquired'])
        for value in ('../../mercy/case.py','/result','E000',None,{},[]):
            self.assertIn('error',env.step('examine',{'evidence_id':value}))
        self.assertEqual(env.state['acquired'],before)
    def test_destruction_and_preservation(self):
        for preserve in (True,False):
            env=Environment(); eid=next(e['id'] for e in env.case['evidence'].values() if e['key']=='draft')
            if preserve: env.step('preserve',{'evidence_id':eid})
            env.step('confront',{'character':'savitri'})
            result=env.step('examine',{'evidence_id':eid})
            self.assertEqual('error' not in result,preserve)
    def test_duplicate_citations_cannot_multiply_reward(self):
        env=reference('mira_murder',7)
        self.assertEqual(env.result['score'],1)
        self.assertIn('error',env.step('submit_report',{'claims':[]}))
    def test_no_private_dossiers_in_observation(self):
        env=Environment()
        for person in env.observe()['characters'].values():
            self.assertNotIn('secret',person)
        self.assertNotIn('truth',env.observe())


class LiveTrajectoryRegressionTests(unittest.TestCase):
    def test_valid_alternative_reports(self):
        import json
        from pathlib import Path
        for fixture,task in [('full_inquest','full_inquest'),('ninth_ward','ninth_ward'),('full_inquest-medical','full_inquest')]:
            env=Environment(task,8)
            actions=json.loads((Path(__file__).parent/'fixtures'/f'{fixture}-seed8.json').read_text())
            for action in actions:
                env.step(action['tool'],action['args'])
            self.assertEqual(env.result['score'],1.0,env.result)

if __name__=='__main__': unittest.main()
