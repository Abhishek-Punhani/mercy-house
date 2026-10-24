import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from mercy.town.factory import build
from mercy.town.reference import gates
from mercy.town.tasks import TASKS
from mercy.town.harness import instructions, parse, run, bounded_result


class SubmissionContractTests(unittest.TestCase):
    def test_five_tasks_and_every_gate_including_replay(self):
        self.assertGreaterEqual(len(TASKS), 5)
        self.assertGreaterEqual(len({t['difficulty'] for t in TASKS.values()}), 2)
        with TemporaryDirectory() as folder:
            for task in TASKS:
                row = gates(task, 19, Path(folder) / task)
                self.assertTrue(row['passed'])
                self.assertEqual(row['reference'], 1.)
                self.assertEqual(row['noop'], 0.)
                self.assertEqual(build(task, 19).state_hash(), row['starting_hash'])

    def test_appended_instructions_are_exact_including_crlf(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'judge.txt'
            path.write_bytes(b'  Keep these spaces.\r\nSecond line.\r\n')
            with patch.dict(os.environ, {'APPEND_FILE': 'judge.txt'}):
                self.assertTrue(instructions(folder).endswith(path.read_bytes().decode()))
            path.write_bytes(b'  \r\n')
            with patch.dict(os.environ, {'APPEND_FILE': 'judge.txt'}), self.assertRaises(ValueError):
                instructions(folder)

    def test_parser_accepts_native_legacy_and_structured_text(self):
        examples = [
            {'tool_calls': [{'id': 'provided', 'function': {'name': 'look', 'arguments': '{}'}}]},
            {'function_call': {'name': 'look', 'arguments': {}}},
            {'content': '{"tool":"look","args":{}}'},
        ]
        for value in examples:
            _, calls = parse({'choices': [{'message': value}]}, 1)
            self.assertEqual(calls[0]['function']['name'], 'look')
            self.assertEqual(json.loads(calls[0]['function']['arguments']), {})

    def test_malformed_reply_consumes_step_and_extra_calls_are_not_executed(self):
        world = build('last_witness', 7)
        initial_history = len(world.history)
        responses = [
            {'choices': None},
            {'choices': [{'message': {'tool_calls': [{'function': {'name': 'look', 'arguments': '{}'}} for _ in range(11)]}}]},
            {'choices': [{'message': {'tool_calls': [{'function': {'name': 'submit_report', 'arguments': '{"findings":[]}'}}]}}]},
        ]
        wires = []
        def transport(messages, tools, timeout):
            value = responses[len(wires)]
            wire = '  ' + json.dumps(value) + '\n'
            wires.append(wire)
            return value, wire
        with TemporaryDirectory() as folder:
            append = Path(folder) / 'append.txt';append.write_text('Judge suffix\n')
            with patch.dict(os.environ, {'APPEND_FILE': str(append)}):
                summary = run(world, Path(folder), steps=3, transport=transport)
            rows = [json.loads(line) for line in (Path(folder) / 'episode.jsonl').read_text().splitlines()]
        self.assertEqual(summary['termination_reason'], 'failure')
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(world.history) - initial_history, 11) # ten look calls and one report
        self.assertIn('not executed', rows[1]['tool_result'][-1]['error'])
        self.assertTrue(rows[0]['errors'])
        self.assertEqual(rows[1]['model_output_raw'], wires[1])
        self.assertTrue(rows[1]['model_input']['messages'][0]['content'].endswith('Judge suffix\n'))
        required = {'timestamp', 'step', 'seed', 'model_input', 'model_output_raw', 'parsed_actions', 'tool_result', 'errors', 'state', 'reward', 'tokens', 'latency_ms'}
        self.assertTrue(all(required <= set(row) for row in rows))

    def test_forced_end_scores_empty_and_missing_append_never_calls_model(self):
        world = build('last_witness', 7)
        def transport(messages, tools, timeout):
            value = {'choices': [{'message': {'content': 'I am thinking.'}}]}
            return value, json.dumps(value)
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'append.txt';path.write_text('Continue\n')
            with patch.dict(os.environ, {'APPEND_FILE': str(path)}):
                summary = run(world, Path(folder), steps=1, transport=transport)
            self.assertEqual(summary['termination_reason'], 'step_cap')
            self.assertEqual(summary['result']['score'], 0.)
            with patch.dict(os.environ, {'APPEND_FILE': str(Path(folder) / 'absent')}), self.assertRaises(ValueError):
                run(build('last_witness', 7), Path(folder), transport=lambda *_: self.fail('Model must not be called'))

    def test_false_accusation_spam_and_duplicate_findings_cannot_inflate_score(self):
        world = build('last_witness', 7)
        claim = {'actor': 'dev', 'predicate': 'killed', 'object': 'mira', 'sources': []}
        world.step('submit_report', {'findings': [claim] * 50})
        self.assertEqual(world.result['score'], 0.)
        self.assertEqual(len(world.result['false_findings']), 1)

    def test_output_cap_returns_valid_json(self):
        value = bounded_result({'long': 'x' * 20000})
        self.assertTrue(value['truncated'])
        self.assertLess(len(json.dumps(value).encode()), 8200)


if __name__ == '__main__':
    unittest.main()
