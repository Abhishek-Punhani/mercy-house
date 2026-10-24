import copy
import json
import math
import random
import tempfile
from pathlib import Path
import unittest

from mercy.rl.policy import Selector
from mercy.rl.public import Notebook, features
from mercy.rl.curriculum import checkpoint, restore, propose, terminal_reward
from mercy.rl.train import evaluate, rollout
from mercy.rl.live import validate_candidates, run_selected_detective


class SelectorTests(unittest.TestCase):
    def test_log_policy_gradient_matches_numerical_derivative(self):
        rows = [{'a': 1., 'b': .3}, {'a': -.4, 'b': .7}, {'b': -.1}]
        selector = Selector({'a': .4, 'b': -.2})
        probabilities = selector.probabilities(rows)
        gradient = selector.log_gradient(rows, 1, probabilities)
        for key in ('a', 'b'):
            plus = Selector({**selector.weights, key: selector.weights[key] + 1e-6})
            minus = Selector({**selector.weights, key: selector.weights[key] - 1e-6})
            numerical = (math.log(plus.probabilities(rows)[1]) - math.log(minus.probabilities(rows)[1])) / 2e-6
            self.assertAlmostEqual(gradient[key], numerical, places=6)

    def test_terminal_reward_update_increases_sampled_action_probability(self):
        selector = Selector()
        rows = [{'tool:search': 1.}, {'tool:submit_report': 1.}]
        before = selector.probabilities(rows)
        selector.update([([(rows, 0, before)], 1.)], baseline=0.)
        self.assertGreater(selector.probabilities(rows)[0], before[0])

    def test_features_do_not_encode_names_ids_or_hidden_packet_keys(self):
        book = Notebook({'now': {'place': {'id': 'room'}}})
        action = {'tool': 'search', 'args': {'surface': 'desk'}}
        expected = features(book, action, 6, 6)
        book.opening['journal'] = 'PRIVATE_CANARY_KILLER'
        book.opening['private_biography'] = 'PRIVATE_CANARY_KILLER'
        book.records['random-private-looking-id'] = {'record_id': 'random-private-looking-id', 'description': 'Person Z committed a crime'}
        # Count is public and changes; raw text/names/IDs are never weight keys.
        actual = features(book, action, 6, 6)
        self.assertEqual(set(expected), set(actual))
        self.assertNotIn('CANARY', json.dumps(actual))
        self.assertNotIn('Person Z', json.dumps(actual))
        self.assertNotIn('random-private', json.dumps(actual))

    def test_candidate_permutation_preserves_probabilities(self):
        selector = Selector({'a': 2., 'b': -.3})
        rows = [{'a': 1.}, {'b': 1.}, {'a': .2, 'b': .7}]
        p = selector.probabilities(rows)
        q = selector.probabilities([rows[2], rows[0], rows[1]])
        self.assertEqual(q, [p[2], p[0], p[1]])

    def test_checkpoint_round_trip_and_nonfinite_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'policy.json'
            Selector({'tool:search': .3}).save(path)
            self.assertEqual(Selector.load(path).weights, {'tool:search': .3})
            path.write_text(json.dumps({'version': 1, 'feature_version': 1, 'weights': {'x': float('nan')}}))
            with self.assertRaises(ValueError):
                Selector.load(path)


class CurriculumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared = checkpoint(141001)

    def test_checkpoint_reproducible_and_proposer_has_only_public_data(self):
        again = checkpoint(141001)
        self.assertEqual(self.prepared[0]['state_hash'], again[0]['state_hash'])
        world, book = restore(self.prepared)
        text = json.dumps(book.packet(6))
        for forbidden in ('propositions', 'hidden_by', 'audit_rows', 'eligible_recall_ids', 'journal'):
            self.assertNotIn(forbidden, text)
        self.assertEqual(world.state_hash(), self.prepared[0]['state_hash'])
        before = copy.deepcopy(book.__dict__)
        propose(book)
        self.assertEqual(book.__dict__, before)

    def test_supported_reference_uses_real_tools_and_original_score(self):
        world, book = restore(self.prepared)
        for surface in ('stove', 'parlor table'):
            action = {'tool': 'search', 'args': {'surface': surface}}
            book.observe(action, world.step(action['tool'], action['args']))
        # No comparison: naming a plausible writer still has zero support reward.
        premature = next(a for a in propose(book) if a['tool'] == 'submit_report')
        clone_world, _ = restore(self.prepared)
        self.assertEqual(clone_world.step('submit_report', {'findings': []}), {'submitted': True})
        self.assertEqual(terminal_reward(clone_world)[0], 0.)
        self.assertTrue(premature['args']['findings'])
        compare = next(a for a in propose(book) if a['tool'] == 'compare')
        book.observe(compare, world.step(compare['tool'], compare['args']))
        report = next(a for a in propose(book) if a['tool'] == 'submit_report')
        world.step(report['tool'], report['args'])
        reward, result = terminal_reward(world)
        self.assertEqual(reward, 1.)
        self.assertAlmostEqual(result['score'], 1 / 3, places=5)
        self.assertEqual(result['supported_findings'][0]['predicate'], 'forged')

    def test_budget_finalization_cannot_invent_support_and_evaluation_freezes_weights(self):
        selector = Selector({'tool:look': 100.})
        before = dict(selector.weights)
        trajectory, reward, info = rollout(selector, self.prepared, random.Random(1), budget=2, greedy=True, trace=True)
        self.assertEqual(len(trajectory), 2)
        self.assertEqual(info['termination'], 'step_cap')
        self.assertEqual(reward, 0.)
        self.assertEqual(selector.weights, before)
        result, _ = evaluate(selector, [self.prepared], 2, repeats=1, budget=2, noop=True)
        self.assertEqual(result['mean_reward'], 0.)
        self.assertEqual(selector.weights, before)

    def test_proposal_metadata_cannot_inject_a_score_or_unknown_capability(self):
        with self.assertRaises(ValueError):
            validate_candidates({'candidates': [{'tool': 'search', 'args': {'surface': 'desk'}, 'score': 1}]})
        with self.assertRaises(ValueError):
            validate_candidates({'candidates': [{'tool': 'read_file', 'args': {'path': 'private.json'}}]})
        self.assertEqual(len(validate_candidates({'candidates': [{'tool': 'look', 'args': {}}, {'tool': 'look', 'args': {}}]})), 1)

    def test_frozen_selector_live_adapter_uses_public_packet_and_forces_empty_report(self):
        world, _ = restore(self.prepared)
        packets = []
        def proposer(packet):
            packets.append(packet)
            return [{'tool': 'look', 'args': {}}], {}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'policy.json'
            Selector().save(path)
            summary = run_selected_detective(world, Path(folder), path, steps=2, proposer=proposer)
            self.assertEqual(summary['reason'], 'step_cap')
            self.assertEqual(summary['result']['score'], 0.)
            self.assertNotIn('propositions', json.dumps(packets))
            self.assertNotIn('journal', json.dumps(packets))
            self.assertEqual(Selector.load(path).weights, {})


if __name__ == '__main__':
    unittest.main()
