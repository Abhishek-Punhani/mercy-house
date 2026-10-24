"""Regression checks for evidence/biography contradictions found in the audit."""
import runpy
from pathlib import Path
import unittest

from mercy.town.factory import build, ReferenceActors
from mercy.town.family_data import definition
from mercy.town.family_world import FamilyTown
from mercy.town.reference import solve
from mercy.town.world import Town


class CaseAuditRegressions(unittest.TestCase):
    def investigated(self, task='mercy_inquest', seed=7):
        world=build(task,seed)
        solve(world)
        snapshot=world.export_private();snapshot['ended']=False;snapshot['result']=None
        return Town.restore(snapshot,ReferenceActors())

    def physical_ids(self,world):
        return {world.objects[r['source']]['key']:rid for rid,r in world.receipts.items() if r['kind']=='physical'}

    def test_new_families_have_a_source_only_trace_with_both_assailants(self):
        investigate=runpy.run_path(str(Path(__file__).with_name('public_feasibility.py')))['investigate']
        for task in ('lantern_room','second_passenger','bell_before_dawn'):
            for seed in (0,1):
                with self.subTest(task=task,seed=seed):
                    world=build(task,seed)
                    row=investigate(world.step,world.opening())
                    self.assertTrue(world.result['success'])
                    self.assertLessEqual(row['conservative_batched_reply_bound'],40)

    def test_payer_is_not_the_physical_carrier(self):
        world=self.investigated('garden_burials')
        world.step('submit_report',{'findings':[{'actor':'savitri','predicate':'moved','object':'burials','sources':list(world.receipts)}]})
        self.assertEqual(world.result['score'],0.)
        self.assertEqual(world.result['false_findings'],[{'actor':'savitri','predicate':'moved','object':'burials'}])
        self.assertFalse(any(o.get('proposition')=={'actor':'savitri','predicate':'moved','object':'burials'} for o in world.objects.values()))

    def test_grave_relocation_alias_preserves_proof_requirements(self):
        from mercy.town.verifier import targets,normalize
        for phrase in ('grave relocation','burial relocation','relocation of graves'):
            with self.subTest(phrase=phrase):
                world=self.investigated()
                findings=[{**p,'object':phrase if p['predicate']=='commissioned' else p['object'],'sources':list(world.receipts)} for p in targets(world)]
                world.step('submit_report',{'findings':findings})
                self.assertEqual(world.result['score'],1.)
                self.assertTrue(world.result['success'])
                empty=build('mercy_inquest',7)
                empty.step('submit_report',{'findings':[{'actor':'savitri','predicate':'commissioned','object':phrase,'sources':[]}]})
                self.assertEqual(empty.result['score'],0.)
                self.assertEqual(len(empty.result['unsupported_findings']),1)
        for phrase in ('not grave relocation','a claim about grave relocation'):
            claim={'actor':'savitri','predicate':'commissioned','object':phrase,'sources':[]}
            self.assertEqual(normalize(build('mercy_inquest',7),claim)['object'],phrase)

    def test_register_cover_initials_and_omission_do_not_prove_writer(self):
        world=self.investigated();ids=self.physical_ids(world)
        comparison=world.step('compare',{'records':[ids['correction_ledger'],ids['parish_register']]})
        world.step('submit_report',{'findings':[{'actor':'vedant','predicate':'altered','object':'death_register','sources':[comparison['record_id']]}]})
        self.assertEqual(world.result['score'],0.)
        self.assertEqual(len(world.result['unsupported_findings']),1)

    def test_independent_receipt_supports_register_attribution(self):
        for split in (False,True):
            world=self.investigated();ids=self.physical_ids(world)
            groups=[['correction_ledger','parish_register'],['correction_ledger','vedant_sample']] if split else [['correction_ledger','parish_register','vedant_sample']]
            sources=[world.step('compare',{'records':[ids[k] for k in group]})['record_id'] for group in groups]
            claim={'actor':'vedant','predicate':'altered','object':'death_register'}
            world.step('submit_report',{'findings':[{**claim,'sources':sources}]})
            self.assertEqual(world.result['supported_findings'],[claim])
            self.assertEqual(world.result['unsupported_findings'],[])

    def test_optional_delivery_is_supported_without_adding_a_target(self):
        world=self.investigated('bell_before_dawn');ids=self.physical_ids(world)
        self.assertEqual(len(world.material_targets()),3)
        findings=[{**p,'sources':list(world.receipts)} for p in world.material_targets()]
        delivered={'actor':'niv','predicate':'relayed','object':'warning_letter'}
        findings.append({**delivered,'sources':[ids['warning'],ids['delivery']]})
        world.step('submit_report',{'findings':findings})
        self.assertEqual(world.result['score'],1.)
        self.assertTrue(world.result['success'])
        self.assertIn(delivered,world.result['supported_findings'])
        self.assertEqual(world.result['material_events_total'],3)

    def test_delivery_docket_records_what_was_observable_at_delivery(self):
        world=FamilyTown(7,ReferenceActors(),definition('bell_before_dawn',7))
        for verb,actor,target in world.case['tape']:
            world.perform(actor,verb,target)
            if verb=='deliver':break
        self.assertEqual(world.people['tessa']['location'],'inn')
        text=world.item('delivery')['text']
        self.assertIn('still in the common room',text)
        self.assertNotIn('entered the chapel',text)

    def test_counterfactual_safe_coach_has_no_prewritten_wreck(self):
        world=FamilyTown(7,ReferenceActors(),definition('second_passenger',7))
        self.assertNotIn('wheel folded',world.visible_scene('forest'))
        for verb,actor,target in world.case['tape']:
            if verb!='tamper':world.perform(actor,verb,target)
        self.assertEqual(world.mechanism['coach_outcome'],'safe')
        self.assertTrue(all(world.states[v]['alive'] for v in world.case['victims']))
        self.assertNotIn('wheel folded',world.visible_scene('forest'))
        self.assertNotEqual(world.item('brake_trace')['surface'],'wreckage')
        self.assertFalse(any(o['key'].startswith('body_') for o in world.objects.values()))

    def test_spade_memory_and_signature_features_are_physically_possible(self):
        world=build('mercy_inquest',7)
        spade=next(o for o in world.objects.values() if o['key']=='spade')
        self.assertEqual(spade['surface'],'tool shed')
        self.assertTrue(any('tool shed' in m['text'] for m in world.states['dev']['memories']))
        threat=next(o for o in world.objects.values() if o['key']=='planted_threat')
        self.assertIn('warned',threat['text'])
        self.assertIn('d',threat['text'])


if __name__=='__main__':unittest.main()
