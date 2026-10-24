import json
import unittest
from mercy.town.world import Town
from mercy.town.agents import FixtureAgent

class TownTests(unittest.TestCase):
    def build(self,hide=True):
        a=FixtureAgent(hide=hide);w=Town(7,a);w.simulate(4);w.arrive();return w,a
    def test_murder_is_executed_not_assumed(self):
        a=FixtureAgent(force_murder=False);w=Town(7,a)
        self.assertFalse(w.simulate(4)['incident_occurred'])
        self.assertFalse(any(e['kind']=='fatal_injury' for e in w.journal))
        with self.assertRaises(ValueError):w.arrive()
    def test_initial_observation_has_no_solution_or_catalog(self):
        w,_=self.build();intro=json.dumps(w.arrive()) if False else json.dumps({'your_life':w.detective,'now':w.look()})
        for forbidden in ('required_claims','catalog','savitri_killed_mira','forged_threat','personal enemy','trust me','ward key'):
            self.assertNotIn(forbidden,intro)
        self.assertNotIn('savitri',json.dumps(w.look()).lower())
    def test_agent_has_only_personal_knowledge(self):
        w,a=self.build()
        for pid,packet in a.packets:
            self.assertEqual(packet['person']['id'],pid)
            self.assertNotIn('journal',packet)
            self.assertNotIn('states',packet)
        mira_death=next(e for e in w.journal if e['kind']=='fatal_injury')
        self.assertFalse(any(m['event']==mira_death['id'] for m in w.states['leena']['memories']))
        partial=[m for m in w.states['sera']['memories'] if m['source']=='partial_observation']
        self.assertTrue(partial)
        self.assertNotIn('Savitri',partial[0]['text'])
    def test_search_requires_local_feature(self):
        w,_=self.build()
        self.assertIn('error',w.step('search',{'surface':'correspondence drawer'}))
        self.assertIn('error',w.step('go',{'destination':'rao_house'}))
        result=w.step('search',{'surface':'floor'})
        self.assertTrue(result['findings'])
        self.assertTrue(all('proposition' not in x and 'event' not in x for x in result['findings']))
    def test_subordinate_can_hide_real_object(self):
        w,_=self.build();w.step('go',{'destination':'hall'})
        result=w.step('search',{'surface':'visitors book','by':'kabir'})
        self.assertFalse(any(x['label']=='folded envelope' for x in result['findings']))
        self.assertTrue(any(e['kind']=='concealment' for e in w.journal))
        self.assertTrue(any(o['hidden_by']=='kabir' for o in w.objects.values()))
    def test_supervision_and_other_subordinate_change_outcome(self):
        for by,supervise in [('kabir',True),('anya',False)]:
            w,_=self.build();w.step('go',{'destination':'hall'})
            result=w.step('search',{'surface':'visitors book','by':by,'supervise':supervise})
            self.assertTrue(any(x['label']=='folded envelope' for x in result['findings']))
            self.assertFalse(any(e['kind']=='concealment' for e in w.journal))
    def test_interrogation_is_not_remote_omniscience(self):
        w,_=self.build()
        self.assertIn('error',w.step('ask',{'pid':'leena','question':'Who killed Mira?'}))
        result=w.step('ask',{'pid':'anya','question':'What did you see?'})
        self.assertNotIn('Savitri strikes',json.dumps(result))
    def test_no_reward_for_guessing(self):
        w,_=self.build()
        w.step('submit_report',{'findings':[{'actor':'savitri','predicate':'killed','object':'mira','sources':[]}]})
        self.assertEqual(w.result['score'],0.)
    def test_replay_and_checkpoint(self):
        w,_=self.build();v,_=self.build()
        self.assertEqual(w.state_hash(),v.state_hash())
        snap=json.loads(json.dumps(w.export_private()))
        restored=Town.restore(snap,FixtureAgent())
        self.assertEqual(w.state_hash(),restored.state_hash())
        self.assertEqual(w.step('search',{'surface':'floor'}),restored.step('search',{'surface':'floor'}))
    def test_same_location_not_mind_reading(self):
        w,_=self.build()
        private=json.dumps(w.packet('anya',[{'action_id':'wait'}]))
        self.assertNotIn('Nalin has been delivering',private)
        self.assertNotIn('My correction ledger remains',private)


class FurtherBoundaryTests(unittest.TestCase):
    def test_partial_witness_cannot_name_murderer_for_score(self):
        a=FixtureAgent();w=Town(7,a);w.simulate(4);w.arrive()
        w.people['sera']['location']='archive'
        w.step('people_here',{})
        testimony=w.step('ask',{'pid':'sera','question':'What did you see?'})
        traces=w.step('search',{'surface':'floor'})['findings']
        w.step('submit_report',{'findings':[{'actor':'savitri','predicate':'killed','object':'mira','sources':[testimony['record_id']]+[r['record_id'] for r in traces]}]})
        self.assertEqual(w.result['score'],0)
    def test_witness_does_not_receive_detective_unshown_records(self):
        a=FixtureAgent();w=Town(7,a);w.simulate(4);w.arrive()
        records=w.step('search',{'surface':'desk'})
        w.people_here()
        w.step('ask',{'pid':'anya','question':'What do you know?'})
        self.assertEqual(a.packets[-1][1]['presented_material'],[])
    def test_repeated_search_reuses_record(self):
        a=FixtureAgent();w=Town(7,a);w.simulate(4);w.arrive()
        first=w.step('search',{'surface':'floor'})
        second=w.step('search',{'surface':'floor'})
        self.assertEqual(first['findings'],second['findings'])


class SecuredEvidenceTests(unittest.TestCase):
    def test_subordinate_cannot_secretly_rehide_recorded_or_collected_item(self):
        for collect in (False,True):
            a=FixtureAgent();w=Town(7,a);w.simulate(4);w.arrive()
            w.step('go',{'destination':'hall'})
            found=w.step('search',{'surface':'visitors book'})['findings']
            letter=next(x for x in found if x['label']=='folded envelope')
            if collect:w.step('collect',{'oid':letter['object_id']})
            w.step('search',{'surface':'visitors book','by':'kabir'})
            self.assertIsNone(w.objects[letter['object_id']]['hidden_by'])

if __name__=='__main__':unittest.main()
