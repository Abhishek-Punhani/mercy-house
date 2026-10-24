import unittest
from mercy.town.agents import FixtureAgent
from mercy.town.setting import setting
from mercy.town.world import Town

class CaseReviewTests(unittest.TestCase):
    def test_routes_are_bidirectional_and_houses_exist(self):
        places,people,detective=setting()
        for pid,p in people.items():
            self.assertIn(p['home'],places);self.assertIn(p['location'],places)
            for field in ('family','history','relationships','goals','temperament','memories','public_voice','daily_routine'):self.assertTrue(p[field],(pid,field))
        for key,place in places.items():
            for dst in place['exits']:self.assertIn(key,places[dst]['exits'],(key,dst))
        self.assertIn('quarry',places['forest']['exits'])
    def test_burials_require_discovery_and_digging_tool(self):
        w=Town(7,FixtureAgent());w.simulate(4);w.arrive();w.location='garden'
        visible=w.step('search',{'surface':'winter beds'})
        self.assertFalse(any(x['label']=='grave cloth' for x in visible['findings']))
        self.assertIn('error',w.step('excavate',{'surface':'winter beds'}))
        tool=w.step('search',{'surface':'tool shed'})['findings'][0]
        w.step('collect',{'oid':tool['object_id']})
        found=w.step('excavate',{'surface':'winter beds'})
        self.assertTrue(any(x['label']=='grave cloth' for x in found['findings']))
    def test_partial_witness_and_garment_ownership_do_not_identify_fatal_actor(self):
        w=Town(7,FixtureAgent());w.simulate(4);w.arrive();w.people['sera']['location']='archive';w.people_here()
        testimony=w.step('ask',{'pid':'sera','question':'What did you see through the hatch?','approach':'reassure'})
        floor=w.step('search',{'surface':'floor'})['findings']
        w.location='das_house'
        furniture=w.step('search',{'surface':'parlor table'})['findings']
        cuff=next(r for r in floor if r['label']=='torn cuff');coat=next(r for r in furniture if r['label']=='household shawl')
        comparison=w.step('compare',{'records':[cuff['record_id'],coat['record_id']]})
        evidence=[comparison['record_id'],testimony['record_id']]+[r['record_id'] for r in floor]
        w.step('submit_report',{'findings':[{'actor':'savitri','predicate':'killed','object':'mira','sources':evidence}]})
        self.assertFalse(any(x['predicate']=='killed' for x in w.result['supported_findings']))
        self.assertEqual(w.result['score'],0.)
    def test_garment_presence_without_witness_does_not_prove_murder(self):
        w=Town(7,FixtureAgent());w.simulate(4);w.arrive()
        floor=w.step('search',{'surface':'floor'})['findings'];w.location='das_house'
        coat=next(r for r in w.step('search',{'surface':'parlor table'})['findings'] if r['label']=='household shawl')
        cuff=next(r for r in floor if r['label']=='torn cuff')
        link=w.step('compare',{'records':[cuff['record_id'],coat['record_id']]})
        w.step('submit_report',{'findings':[{'actor':'savitri','predicate':'killed','object':'mira','sources':[link['record_id']]+[r['record_id'] for r in floor]}]})
        self.assertEqual(w.result['score'],0.)

if __name__=='__main__':unittest.main()

class ReportIdentityTests(unittest.TestCase):
    def test_full_names_are_equivalent_to_observed_ids(self):
        w=Town(7,FixtureAgent());w.simulate(4);w.arrive()
        self.assertEqual(w.entity_id('Dr. Mira Sen'),'mira')
        self.assertEqual(w.entity_id('Savitri Das'),'savitri')
        result=w.step('submit_report',{'findings':[{'actor':'Savitri Das','predicate':'killed','object':'Dr. Mira Sen','sources':[]}]})
        self.assertTrue(result['submitted'])
        self.assertEqual(w.result['false_findings'],[])
        self.assertEqual(w.result['score'],0.)
    def test_unrecognized_semantics_not_labeled_factually_false(self):
        w=Town(7,FixtureAgent());w.simulate(4);w.arrive()
        w.step('submit_report',{'findings':[{'actor':'Savitri Das','predicate':'concealed','object':'some old remains','sources':[]}]})
        self.assertEqual(w.result['false_findings'],[])
        self.assertTrue(w.result['unrecognized_findings'])

class EvidenceCausalityTests(unittest.TestCase):
    def test_shawl_damage_is_created_by_the_attack(self):
        w=Town(7,FixtureAgent())
        coat=next(o for o in w.objects.values() if o['key']=='coat')
        self.assertNotIn('torn',coat['text']);self.assertEqual(coat['carried_by'],'savitri')
        w.simulate(4)
        self.assertIn('torn',coat['text']);self.assertIsNotNone(coat['event'])
        self.assertIsNone(coat['carried_by']);self.assertEqual(coat['location'],'das_house')
    def test_remote_actor_not_offered_knowledge_of_unheard_incident(self):
        w=Town(7,FixtureAgent())
        w.people['dev']['location']='garden'
        w.simulate(2)
        self.assertFalse(any(m['source']=='heard_sound' for m in w.states['dev']['memories']))
        w.people['dev']['location']='courtyard'
        actions=w.prelude_actions('dev')
        self.assertNotIn('enter_to_help',{a['action_id'] for a in actions})
