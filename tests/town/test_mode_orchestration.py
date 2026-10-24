import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from mercy.town import client
from mercy.town.tasks import TASKS, description


class ModeOrchestrationTests(unittest.TestCase):
    def exercise(self, mode):
        calls = []
        def rpc(path, payload):
            calls.append((path, payload['task_id']))
            if path == '/gate':
                return {'gate': {'passed': True}, 'trajectories': {'reference': [], 'noop': []},
                        'summaries': {'reference': {}, 'noop': {}}}
            self.assertEqual(path, '/reset')
            return {'opening': {'task': description(payload['task_id'])}, 'state_hash': 'test-state'}
        class Response(io.BytesIO):
            def __enter__(self): return self
        with TemporaryDirectory() as folder:
            token = Path(folder) / 'capability'; token.write_text('test-capability')
            suffix = Path(folder) / 'instructions'; suffix.write_text('A judge suffix.\n')
            env = {'MODE': mode, 'TASK_ID': 'borrowed_signature', 'SEED': '17', 'PUBLIC_LOG_DIR': folder, 'APPEND_FILE': str(suffix)}
            with patch.dict(os.environ, env), patch.object(client, 'TOKENFILE', token), patch.object(client, 'rpc', rpc), patch.object(client, 'ThreadingHTTPServer'), patch.object(client.threading, 'Thread'), patch.object(client.urllib.request, 'urlopen', side_effect=lambda *a, **kw: Response(b'{"detective":true,"character":true}')), patch.object(client, 'run_harness', return_value={'termination_reason': 'failure'}) as runner:
                client.main()
                self.last_harness_call=runner.call_args
                return calls, runner.call_count

    def test_baselines_checks_all_without_reset_or_model(self):
        calls, runs = self.exercise('baselines')
        self.assertEqual(calls, [('/gate', task) for task in TASKS])
        self.assertEqual(runs, 0)

    def test_full_selects_one_and_all_gates_each_before_model(self):
        calls, runs = self.exercise('full')
        self.assertEqual(calls, [('/gate', 'borrowed_signature'), ('/reset', 'borrowed_signature')])
        self.assertEqual(runs, 1)
        calls, runs = self.exercise('all')
        self.assertEqual(calls, [(path, task) for task in TASKS for path in ('/gate', '/reset')])
        self.assertEqual(runs, len(TASKS))

    def test_rejected_gate_prevents_model_and_reset(self):
        with TemporaryDirectory() as folder, patch.dict(os.environ, {'MODE':'baselines','PUBLIC_LOG_DIR':folder}), patch.object(client,'ThreadingHTTPServer'), patch.object(client.threading,'Thread'), patch.object(client,'rpc',return_value={'gate':{'passed':False},'trajectories':{},'summaries':{}}), patch.object(client,'run_harness') as runner:
            with self.assertRaises(RuntimeError): client.main()
            runner.assert_not_called()

    def test_explicit_practice_is_forwarded_to_the_harder_case_harness(self):
        with patch.dict(os.environ, {'MERCY_PRACTICE':'1'}):
            self.exercise('full')
        args,kwargs=self.last_harness_call
        self.assertEqual(args[2],100)
        self.assertTrue(kwargs['practice'])
