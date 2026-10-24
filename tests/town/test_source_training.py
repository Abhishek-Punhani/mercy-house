import json
import random
import unittest
from mercy.rl.source_curriculum import SKILLS,scenario,checkpoint,restore,propose,reference
from mercy.rl.public import features
from mercy.rl.train_sources import rollout
from mercy.rl.policy import Selector

class SourceTrainingTests(unittest.TestCase):
    def test_reference_feasibility_and_noop_for_both_roles(self):
        for skill in SKILLS:
            roles=set()
            for seed in (920000,920001,920002,920003):
                c=checkpoint(skill,seed);roles.add(c.snapshot['case']['culprit'])
                self.assertEqual(reference(c),1.)
                _,value,_=rollout(Selector(),c,random.Random(0),noop=True)
                self.assertEqual(value,0.)
            self.assertEqual(len(roles),2)

    def test_correct_guess_without_acquired_support_is_zero(self):
        for skill in SKILLS:
            w=scenario(skill,920000);p=w.material_targets()[0]
            w.step('submit_report',{'findings':[{**p,'sources':[]}]})
            self.assertEqual(w.result['score'],0.)

    def test_public_candidates_and_features_have_no_private_case_fields(self):
        for skill in SKILLS:
            c=checkpoint(skill,920000);w,b=restore(c);cs=propose(skill,b)
            # Candidate generation receives no world or case; features whitelist
            # ordinary progress, tool and receipt-basis signals only.
            self.assertNotIn('culprit',json.dumps(b.packet(8)))
            vectors=[features(b,a,8,8) for a in cs]
            for row in vectors:
                self.assertTrue(all(isinstance(v,(float,int)) for v in row.values()))
                for marker in ('Della','Cyrus','920000','maren','tobin','culprit','primary'):
                    self.assertNotIn(marker,json.dumps(row))
            self.assertEqual(cs,propose(skill,b))

    def test_public_proposer_contains_a_supported_solution_for_each_role(self):
        from mercy.rl.source_curriculum import reward
        from mercy.town.factory import ReferenceActors
        from mercy.town.world import Town
        for skill in SKILLS:
            for seed in (920000,920001,920002,920003):
                case=checkpoint(skill,seed);_,book=restore(case);possible=False
                for action in [a for a in propose(skill,book) if a['tool'] in ('ask','compare')]:
                    world,next_book=restore(case)
                    result=world.step(action['tool'],action['args']);next_book.observe(action,result)
                    for report in [a for a in propose(skill,next_book) if a['tool']=='submit_report']:
                        trial=Town.restore(world.export_private(),ReferenceActors())
                        trial.step(report['tool'],report['args'])
                        possible=possible or reward(skill,trial)[0]==1
                self.assertTrue(possible,(skill,seed))

    def test_source_world_is_not_exact_episode_cast_or_elite_biography(self):
        for skill in SKILLS:
            c=checkpoint(skill,920000);w,b=restore(c);s=json.dumps(w.opening())
            for word in ('Patrick Jane','Kristina Frye','Anna Andrews','Savitri Das','Vedant Rao','Arun Mehra','Tara'):
                self.assertNotIn(word,s)
            self.assertEqual(w.incident_provenance['kind'],'original_source_mechanism_training_tape')
            public=json.dumps(b.packet(8))
            for old in ('Tessa','Niv','Ivo','Maren','Tobin','Oren','Nell'):
                self.assertNotIn(old,public)

if __name__=='__main__':unittest.main()
