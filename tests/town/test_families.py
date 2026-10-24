import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from mercy.town.factory import build, ReferenceActors
from mercy.town.family_data import definition
from mercy.town.family_world import FamilyTown
from mercy.town.reference import solve, gates
from mercy.town.world import Town


FAMILIES=('lantern_room','second_passenger','bell_before_dawn')


class FamilyTests(unittest.TestCase):
    def test_repeated_gate_export_remains_one_episode(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)
            for _ in range(2):gates('lantern_room',37,path)
            for kind in ('reference','noop'):
                rows=[json.loads(s) for s in (path/kind/'episode.jsonl').read_text().splitlines()]
                self.assertEqual([r['step'] for r in rows],list(range(1,len(rows)+1)))
                self.assertEqual(sum(r['parsed_actions'][0]['tool']=='submit_report' for r in rows),1)

    def test_seeded_reset_restore_and_role_variation(self):
        for family in FAMILIES:
            roles=set()
            for seed in range(12):
                world=build(family,seed);roles.add(world.case['culprit'])
                self.assertEqual(world.state_hash(),build(family,seed).state_hash())
                restored=Town.restore(json.loads(json.dumps(world.export_private())),ReferenceActors())
                self.assertIsInstance(restored,FamilyTown)
                self.assertEqual(restored.state_hash(),world.state_hash())
                self.assertEqual(restored.opening(),world.opening())
            self.assertEqual(len(roles),2)

    def test_all_new_reference_and_noop_gates_multiple_seeds(self):
        with TemporaryDirectory() as folder:
            for family in FAMILIES:
                for seed in (11,37,82):
                    row=gates(family,seed,Path(folder)/family/str(seed))
                    self.assertEqual((row['reference'],row['noop']),(1.,0.))

    def test_initial_observation_has_no_private_plan_or_foregone_answers(self):
        for family in FAMILIES:
            world=build(family,37);opening=world.opening();text=json.dumps(opening)
            for key in ('culprit','primary','secrets','material_targets','disclosure_relevance','target_predicates','required_claims'):
                self.assertNotIn('"'+key+'"',text)
            self.assertEqual(opening['notes'],[])
            self.assertNotIn('Mira',text)

    def test_no_attack_no_automatic_body(self):
        world=FamilyTown(37,ReferenceActors(),definition('lantern_room',37))
        self.assertTrue(world.states['oren']['alive'])
        self.assertFalse(any(k.startswith('body_') for k in [o['key'] for o in world.objects.values()]))
        with self.assertRaises(ValueError):world.arrive()

    def test_intact_coach_survives_and_unadulterated_drink_does_not_kill(self):
        for family,skip in [('second_passenger','tamper'),('bell_before_dawn','adulterate')]:
            world=FamilyTown(37,ReferenceActors(),definition(family,37))
            for verb,actor,target in world.case['tape']:
                if verb!=skip:world.perform(actor,verb,target)
            self.assertTrue(all(world.states[v]['alive'] for v in world.case['victims']))
            self.assertFalse(any(e['kind']=='fatal_injury' for e in world.journal))

    def test_witness_does_not_receive_unseen_fatal_causation(self):
        for family,pid in [('second_passenger','neri'),('bell_before_dawn','alba')]:
            world=build(family,37)
            self.assertFalse(any(m.get('proposition',{} ) and m['proposition']['predicate']=='killed' for m in world.states[pid]['memories']))
            self.assertTrue(any(m.get('proposition') for m in world.states[pid]['memories']))

    def test_correct_guess_or_own_notes_cannot_earn_credit(self):
        for family in FAMILIES:
            world=build(family,37)
            note=world.step('record_note',{'summary':'A guessed explanation.'})
            findings=[{**p,'sources':[note['record_id']]} for p in world.material_targets()]
            world.step('submit_report',{'findings':findings})
            self.assertEqual(world.result['score'],0.)

    def test_wrong_person_cannot_borrow_the_reference_proof(self):
        for family in FAMILIES:
            world=build(family,37);solve(world)
            snapshot=world.export_private();snapshot['ended']=False;snapshot['result']=None
            second=Town.restore(snapshot,ReferenceActors())
            claim=next(p for p in second.material_targets() if p['predicate']=='killed')
            wrong=next(pid for pid in second.people if pid not in second.case['victims'] and pid!=claim['actor'])
            second.step('submit_report',{'findings':[{**claim,'actor':wrong,'sources':list(second.receipts)}]})
            self.assertEqual(second.result['score'],0.)
            self.assertEqual(len(second.result['false_findings']),1)

    def test_foreknowledge_and_paper_edges_alone_do_not_prove_murder_or_forgery(self):
        world=build('bell_before_dawn',37)
        world.step('go',{'destination':'hall'})
        for surface in ('copying table','repair table'):world.step('search',{'surface':surface})
        world.step('go',{'destination':'square'});world.step('go',{'destination':'inn'})
        world.step('search',{'surface':'notice board'})
        ids={world.objects[r['source']]['key']:rid for rid,r in world.receipts.items() if r['kind']=='physical'}
        comparison=world.step('compare',{'records':[ids['warning'],ids['paper_'+world.case['culprit']]]})
        world.step('submit_report',{'findings':[{'actor':world.case['culprit'],'predicate':'forged','object':'warning_letter','sources':[comparison['record_id']]}]})
        self.assertEqual(world.result['score'],0.)
