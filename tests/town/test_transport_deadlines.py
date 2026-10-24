import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

from mercy.town import model
from mercy.town.api_gateway import configuration
from mercy.town.factory import build
from mercy.town.harness import run


class TransportDeadlineTests(unittest.TestCase):
    def test_total_model_deadline_does_not_wait_for_blocked_reader(self):
        def stalled(*args):
            time.sleep(.3)
            return {}, '{}'
        start = time.monotonic()
        with patch.object(model, '_request', stalled), self.assertRaises(TimeoutError):
            model.request([], timeout=.03)
        self.assertLess(time.monotonic() - start, .2)

    def test_non_json_wire_is_logged_and_next_reply_can_submit(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size): return b'<html>temporarily unavailable</html>'
        with patch.dict(os.environ, {'BASE_URL': 'https://example.test', 'API_KEY': 'test-only'}), patch.object(model.urllib.request, 'urlopen', return_value=Response()):
            with patch.dict(os.environ, {}, clear=True):
                with patch.dict(os.environ, {'BASE_URL': 'https://example.test', 'API_KEY': 'test-only'}):
                    raw, wire = model._request([])
        self.assertIsNone(raw)
        replies = iter([(raw, wire), ({'choices': [{'message': {'function_call': {'name': 'submit_report', 'arguments': '{"findings":[]}'}}}]}, '{}')])
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'suffix.txt'; path.write_text('Proceed normally.\n')
            with patch.dict(os.environ, {'APPEND_FILE': str(path)}):
                summary = run(build('last_witness'), folder, steps=2, transport=lambda *a, **kw: next(replies))
            rows = [json.loads(s) for s in (Path(folder) / 'episode.jsonl').read_text().splitlines()]
        self.assertEqual(summary['termination_reason'], 'failure')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['model_output_raw'], wire)
        self.assertTrue(rows[0]['errors'])

    def test_npc_key_fallback_requires_explicit_configuration(self):
        with patch.dict(os.environ, {'API_KEY': 'detective-only', 'BASE_URL': 'https://example.test', 'MODEL': 'generic'}, clear=True):
            self.assertFalse(configuration(True)[0])
            with patch.dict(os.environ, {'ALLOW_SHARED_NPC_KEY': '1'}):
                self.assertEqual(configuration(True)[0], 'detective-only')
            with patch.dict(os.environ, {'NPC_API_KEY': 'separate', 'NPC_BASE_URL': 'https://npc.test', 'NPC_MODEL': 'character'}):
                self.assertEqual(configuration(True), ('separate', 'https://npc.test', 'character'))
