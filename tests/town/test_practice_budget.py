import contextlib
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from mercy.town.budget import reply_limit
from mercy.town.factory import build
from mercy.town.harness import run
from mercy.town.tasks import TASKS

class PracticeBudgetTests(unittest.TestCase):
    def test_judging_stays_40_and_only_harder_practice_cases_get_100(self):
        for task,details in TASKS.items():
            self.assertEqual(reply_limit(task),40)
            self.assertEqual(reply_limit(task,True),100 if details['difficulty'] in ('intermediate','advanced') else 40)
        self.assertEqual(reply_limit(None,True),40)

    def execute(self,practice):
        sent=[]
        def transport(messages,tools,timeout):
            sent.append(messages[0]['content'])
            value={'choices':[{'message':{'content':'I am still investigating.'}}]}
            return value,json.dumps(value)
        with TemporaryDirectory() as folder:
            suffix=Path(folder)/'judge.txt';text='Keep this exact suffix: 40 replies in quoted text.\r\n';suffix.write_bytes(text.encode())
            with patch.dict(os.environ,{'APPEND_FILE':str(suffix)}),contextlib.redirect_stdout(io.StringIO()):
                summary=run(build('last_witness',7),Path(folder),steps=100,transport=transport,practice=practice)
            self.assertTrue(all(s.endswith(text) for s in sent))
            self.assertEqual(summary['result']['score'],0)
            return summary,sent

    def test_practice_really_allows_100_model_replies(self):
        summary,sent=self.execute(True)
        self.assertEqual(len(sent),100);self.assertEqual(summary['reply_limit'],100)
        self.assertEqual(summary['termination_reason'],'step_cap')
        self.assertIn('at most 100 replies',sent[0]);self.assertTrue(summary['practice'])

    def test_requesting_100_without_practice_still_stops_at_40(self):
        summary,sent=self.execute(False)
        self.assertEqual(len(sent),40);self.assertEqual(summary['reply_limit'],40)
        self.assertIn('at most 40 replies',sent[0]);self.assertFalse(summary['practice'])
