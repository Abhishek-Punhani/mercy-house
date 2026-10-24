import json
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch
from http.server import ThreadingHTTPServer

from mercy.viewer.events import opening, observation, replay
from mercy.viewer.server import Manager, Run, handler, configuration


DEFAULTS={'API_KEY':'configured-detective-test','BASE_URL':'https://test.example/v1','MODEL':'generic',
          'NPC_API_KEY':'configured-town-test','NPC_BASE_URL':'https://town.example','NPC_MODEL':'town'}


class ViewerBoundaryTests(unittest.TestCase):
    def test_projection_drops_private_metadata_and_provider_reasoning(self):
        received=observation({'record_id':'r1','words':'An ordinary answer.','propositions':[{'actor':'secret'}],
                              'eligible_recall_ids':['secret-id'],'memories':[{'text':'private canary'}]})
        self.assertNotIn('propositions',received);self.assertNotIn('memories',received)
        row={'step':1,'model_output_parsed':{'choices':[{'message':{'content':'My stated plan.','reasoning_content':'private canary'}}]},'parsed_actions':[],'tool_result':[]}
        events=replay({'now':{},'private_world':'private canary'},[row],None)
        self.assertNotIn('private canary',json.dumps(events))
        self.assertEqual(events[1]['note'],'My stated plan.')

    def test_provider_override_does_not_fund_town_with_judge_key(self):
        chosen=configuration({'model':'other-model','base_url':'https://other.example/v1','api_key':'judge-test','seed':12},DEFAULTS)
        self.assertEqual(chosen['key'],'judge-test');self.assertEqual(chosen['npc_key'],'configured-town-test')
        shared={k:v for k,v in DEFAULTS.items() if not k.startswith('NPC_')};shared['ALLOW_SHARED_NPC_KEY']='1'
        chosen=configuration({'api_key':'judge-override-test'},shared)
        self.assertEqual(chosen['npc_key'],'configured-detective-test')

    def test_invalid_role_and_endpoint_configuration_fail_before_launch(self):
        for base in ['http://insecure.test','https://user:password@example.test','https://example.test?key=x','https://example.test\n/x']:
            with self.assertRaises(ValueError):configuration({'api_key':'test','base_url':base},DEFAULTS)
        with self.assertRaises(ValueError):configuration({'api_key':'bad\r\nheader'},DEFAULTS)
        with self.assertRaises(ValueError):configuration({'api_key':'test','task_id':'../private'},DEFAULTS)
        with self.assertRaises(ValueError):configuration({'api_key':'test'},{'BASE_URL':'https://example.test','MODEL':'generic'})

    def test_http_denies_private_files_cross_origin_and_unauthed_starts(self):
        with TemporaryDirectory() as folder,patch('mercy.viewer.server.credentials',return_value=DEFAULTS):
            manager=Manager(folder);run=Run('recorded-test',{'kind':'recorded-model'});run.closed=True
            run.emit({'type':'opening','opening':{'now':{}}});manager.runs[run.id]=run
            server=ThreadingHTTPServer(('127.0.0.1',0),handler(manager));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base='http://127.0.0.1:'+str(server.server_port)
            try:
                with urllib.request.urlopen(base+'/api/config') as response:
                    text=response.read().decode();self.assertNotIn('configured-detective-test',text);self.assertNotIn('configured-town-test',text)
                for path in ['/../.env','/.env','/logs/private/world.json','/api/runs/../../private']:
                    with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(base+path)
                    self.assertEqual(error.exception.code,404)
                for headers in [{},{'X-Mercy-CSRF':manager.csrf,'Origin':'https://other.test'}]:
                    request=urllib.request.Request(base+'/api/runs',data=b'{}',headers={'Content-Type':'application/json',**headers})
                    with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(request)
                    self.assertEqual(error.exception.code,403)
                with urllib.request.urlopen(base+'/api/runs/recorded-test/events') as response:
                    self.assertIn('text/event-stream',response.headers['Content-Type']);self.assertIn(b'opening',response.read())
            finally:server.shutdown();server.server_close();thread.join()

    def test_memory_only_secret_and_persisted_event_redaction(self):
        with TemporaryDirectory() as folder:
            run=Run('test',{},Path(folder),('do-not-persist-test',))
            run.emit({'type':'status','message':'do-not-persist-test'})
            self.assertNotIn('do-not-persist-test',(Path(folder)/'public-events.jsonl').read_text())

    def test_live_build_freezes_source_without_copying_credentials(self):
        with TemporaryDirectory() as folder,patch('mercy.viewer.server.credentials',return_value=DEFAULTS):
            root=Path(folder);(root/'mercy').mkdir();(root/'mercy/code.py').write_text('PUBLIC = True\n');(root/'.env').write_text('API_KEY=must-not-copy-test\n')
            for name in ('Dockerfile.world','Dockerfile.detective','Dockerfile.gateway','Dockerfile.workspace','.dockerignore'):(root/name).write_text('# fixture\n')
            target=root/'logs/run';target.mkdir(parents=True);(target/'public').mkdir();(target/'private').mkdir()
            manager=Manager(root);run=Run('a123456789',{},target)
            process=type('Completed',(),{'poll':lambda self:0})()
            config=configuration({'api_key':'judge-key-test'},DEFAULTS)
            with patch('mercy.viewer.server.subprocess.Popen',return_value=process) as launch,patch.object(manager,'down'):
                manager.execute(run,config)
            self.assertTrue(run.closed);self.assertEqual(run.status,'error')
            self.assertFalse((target/'source/.env').exists())
            self.assertNotIn('must-not-copy-test',(target/'source-manifest.json').read_text())
            self.assertNotIn('judge-key-test',(target/'compose.json').read_text())
            self.assertEqual(launch.call_args.kwargs['env']['MERCY_UI_API_KEY'],'judge-key-test')
            self.assertEqual((target/'source/mercy/code.py').read_text(),'PUBLIC = True\n')

    def test_public_live_tail_handles_wait_notes_and_actual_action_results(self):
        with TemporaryDirectory() as folder,patch('mercy.viewer.server.credentials',return_value=DEFAULTS):
            root=Path(folder);path=root/'public/run/task';path.mkdir(parents=True)
            (root/'private').mkdir();(root/'private/world.json').write_text('private canary')
            (path/'opening.json').write_text(json.dumps({'now':{'place':{'id':'archive','name':'Archive'}}}))
            events=[{'phase':'model_wait','reply':1},{'phase':'reply_note','reply':1,'note':'A stated plan.'},
                {'phase':'start','reply':1,'action':{'tool':'people_here','args':{}}},
                {'phase':'result','reply':1,'action':{'tool':'people_here','args':{}},'observation':{'people':[{'id':'witness','name':'A witness'}],'private_world':'private canary'}}]
            (path/'actions.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
            manager=Manager(root);run=Run('test',{},root)
            manager.consume(run);manager.consume(run)
            self.assertEqual([e['type'] for e in run.events],['opening','activity','reply','activity','action'])
            self.assertNotIn('private canary',json.dumps(run.events))
