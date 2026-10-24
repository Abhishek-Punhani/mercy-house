import json
import random
import unittest

from mercy.rl.policy import Selector
from mercy.rl.public import Notebook, features
from mercy.rl.skills import SKILLS, checkpoint, restore, propose, reward, reference
from mercy.rl.train_skills import rollout


class SkillTrainingTests(unittest.TestCase):
    def test_all_references_solve_and_noops_fail(self):
        for skill in SKILLS:
            for seed in (141000, 241001):
                case = checkpoint(skill, seed)
                self.assertEqual(reference(case)[0], 1., (skill, seed))
                _, value, _ = rollout(Selector(), case, random.Random(1), noop=True)
                self.assertEqual(value, 0., (skill, seed))

    def test_collect_acknowledgement_keeps_public_description(self):
        book = Notebook({'now': {}})
        book.observe({'tool': 'search', 'args': {'surface': 'desk'}},
                     {'findings': [{'record_id': 'r1', 'object_id': 'o1', 'description': 'A signed letter', 'label': 'letter'}]})
        book.observe({'tool': 'collect', 'args': {'oid': 'o1'}}, {'record_id': 'r1', 'secured': 'o1'})
        self.assertEqual(book.records['r1']['description'], 'A signed letter')
        self.assertIn('o1', book.secured)

    def test_witness_identity_varies_without_leaking_to_notebook(self):
        identities = set()
        for seed in range(141000, 141010):
            case = checkpoint('witness', seed)
            w, book = restore(case)
            killed = next(e['id'] for e in w.journal if e['kind'] == 'fatal_injury')
            identities.update(pid for pid in ('bina', 'padma', 'hari', 'kamala', 'ritu')
                              if any(m['event'] == killed for m in w.states[pid]['memories']))
            public = json.dumps(book.packet(10))
            for forbidden in ('propositions', 'audit_rows', 'world journal', 'true_witness'):
                self.assertNotIn(forbidden, public)
        self.assertGreaterEqual(len(identities), 3)

    def test_rumor_accusation_does_not_score(self):
        w, book = restore(checkpoint('statement_review', 141000))
        rumor = next(a for a in propose('statement_review', book) if a['tool'] == 'submit_report' and a['args']['findings'])
        self.assertEqual(rumor['args']['findings'][0]['actor'], 'dev')
        w.step(rumor['tool'], rumor['args'])
        self.assertEqual(reward('statement_review', w)[0], 0.)
        self.assertTrue(w.result['false_findings'])

    def test_family_stake_is_public_only_after_interview_and_affects_candidate_features(self):
        w, book = restore(checkpoint('delegation', 141000))
        action = {'tool': 'search', 'args': {'surface': 'visitors book', 'by': 'kabir'}}
        vector = features(book, action, 10, 10)
        self.assertEqual(vector['delegated_family_unsupervised'], 1.)
        supervised = {'tool': 'search', 'args': {'surface': 'visitors book', 'by': 'kabir', 'supervise': True}}
        self.assertEqual(features(book, supervised, 10, 10)['delegated_family_unsupervised'], 0.)
        # The selected action really changes the world rather than merely a label.
        w.step(action['tool'], action['args'])
        self.assertTrue(any(e['kind'] == 'concealment' for e in w.journal))

    def test_no_automatic_report_at_budget_and_frozen_evaluation(self):
        case = checkpoint('navigation', 141000)
        policy = Selector({'tool:look': 100.})
        before = dict(policy.weights)
        _, value, info = rollout(policy, case, random.Random(3), budget=2, greedy=True)
        self.assertEqual(value, 0.)
        self.assertEqual(info['termination'], 'step_cap')
        self.assertEqual(policy.weights, before)


if __name__ == '__main__':
    unittest.main()
