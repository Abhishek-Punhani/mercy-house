import json
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from mercy.town.service import WorldService, handler

class ServiceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.service=WorldService('test-token',self.tmp.name)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),handler(self.service))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.tmp.cleanup()
    def post(self,path,data,token='test-token'):
        req=urllib.request.Request(self.base+path,data=json.dumps(data).encode(),headers={'X-World-Token':token,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=3) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as exc:
            raw=exc.read();return exc.code,json.loads(raw) if raw else None
    def init(self):return self.post('/initialize',{'backend':'fixture','rounds':4,'seed':7})
    def test_unauthenticated_requests_have_no_state_or_files(self):
        for path in ('/initialize','/status','/action','/final','/snapshot'):
            self.assertEqual(self.post(path,{},token='wrong')[0],403)
        self.assertIsNone(self.service.world)
    def test_no_snapshot_endpoint_or_early_score(self):
        code,reply=self.init();self.assertEqual(code,200)
        self.assertNotIn('journal',json.dumps(reply))
        self.assertNotIn('required_claims',json.dumps(reply))
        self.assertEqual(self.post('/snapshot',{})[0],400)
        self.assertEqual(self.post('/final',{})[0],400)
        self.assertTrue((Path(self.tmp.name)/'world.json').is_file())
    def test_arbitrary_actions_cannot_reach_admin_api(self):
        self.init()
        for action in ('/initialize','/final','read_file','exec'):
            code,r=self.post('/action',{'action':action,'args':{}})
            self.assertEqual(code,200);self.assertIn('error',r['observation'])
    def test_final_only_after_terminal_submission(self):
        self.init();self.post('/action',{'action':'submit_report','args':{'findings':[]}})
        code,r=self.post('/final',{});self.assertEqual(code,200);self.assertEqual(r['score'],0.)
        _,r=self.post('/action',{'action':'look','args':{}});self.assertIn('error',r['observation'])

if __name__=='__main__':unittest.main()
