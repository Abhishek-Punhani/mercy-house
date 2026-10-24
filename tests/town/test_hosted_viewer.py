import json
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

from mercy.viewer.server import Manager,configuration,handler,public_origin

DEFAULTS={'API_KEY':'test-server-key','BASE_URL':'https://configured.example/v1','MODEL':'test',
          'NPC_API_KEY':'test-character-key','NPC_BASE_URL':'https://characters.example','NPC_MODEL':'test'}


class HostedViewerTests(unittest.TestCase):
    def test_public_demo_uses_visitor_key_for_both_roles_and_never_server_key(self):
        defaults={**DEFAULTS,'MERCY_PUBLIC_DEMO':'1'}
        with self.assertRaises(ValueError):configuration({'use_configured_key':True},defaults)
        with self.assertRaises(ValueError):configuration({'api_key':'visitor-key','base_url':'https://another.example'},defaults)
        c=configuration({'api_key':'visitor-key'},defaults)
        self.assertEqual(c['key'],'visitor-key');self.assertEqual(c['npc_key'],'visitor-key')
        self.assertEqual(c['base_url'],c['npc_base'])
        with TemporaryDirectory() as folder,patch('mercy.viewer.server.credentials',return_value=defaults):
            settings=Manager(folder).settings()
            self.assertTrue(settings['public_demo']);self.assertFalse(settings['key_configured'])
            self.assertNotIn('test-server-key',json.dumps(settings))

    def test_public_run_control_token_not_exposed_in_replay_and_required_for_stop(self):
        from mercy.viewer.server import Run
        defaults={**DEFAULTS,'MERCY_PUBLIC_DEMO':'1'}
        with TemporaryDirectory() as folder,patch('mercy.viewer.server.credentials',return_value=defaults):
            manager=Manager(folder);run=Run('a123456789',{});run.control_token='private-run-control';run.closed=True
            manager.runs[run.id]=run
            self.assertNotIn(run.control_token,json.dumps(run.public()))
            server=ThreadingHTTPServer(('127.0.0.1',0),handler(manager));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base='http://127.0.0.1:'+str(server.server_port)
            try:
                headers={'X-Mercy-CSRF':manager.csrf}
                req=urllib.request.Request(base+'/api/runs/'+run.id+'/stop',data=b'{}',headers=headers)
                with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(req)
                self.assertEqual(error.exception.code,403)
                headers['X-Mercy-Run-Control']=run.control_token
                with urllib.request.urlopen(urllib.request.Request(base+'/api/runs/'+run.id+'/stop',data=b'{}',headers=headers)) as response:self.assertEqual(response.status,200)
            finally:server.shutdown();server.server_close();thread.join()

    def test_public_origin_is_explicit_single_https_origin(self):
        self.assertEqual(public_origin('https://MercyHouse.abhi07.xyz:443/'),'https://mercyhouse.abhi07.xyz')
        self.assertIsNone(public_origin(''))
        for value in ('http://mercyhouse.abhi07.xyz','https://user:pw@mercyhouse.abhi07.xyz','https://mercyhouse.abhi07.xyz/path','https://mercyhouse.abhi07.xyz?x=1','https://mercyhouse.abhi07.xyz#x','https://mercyhouse.abhi07.xyz\n'):
            with self.assertRaises(ValueError):public_origin(value)

    def test_configured_key_cannot_be_forwarded_to_another_provider(self):
        for url in ('https://attacker.example/v1','https://configured.example/other-path'):
            with self.assertRaises(ValueError):configuration({'base_url':url,'use_configured_key':True},DEFAULTS)
        c=configuration({'use_configured_key':True},DEFAULTS)
        self.assertEqual(c['key'],'test-server-key')
        c=configuration({'api_key':'own-provider-key','base_url':'https://another-provider.example/v1'},DEFAULTS)
        self.assertEqual(c['key'],'own-provider-key')
        self.assertEqual(c['npc_key'],'test-character-key')

    def test_public_host_requires_matching_https_origin_and_csrf(self):
        origin='https://mercyhouse.abhi07.xyz'
        with TemporaryDirectory() as folder,patch('mercy.viewer.server.credentials',return_value={**DEFAULTS,'MERCY_PUBLIC_ORIGIN':origin}):
            manager=Manager(Path(folder));server=ThreadingHTTPServer(('127.0.0.1',0),handler(manager))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base='http://127.0.0.1:'+str(server.server_port)
            try:
                def request(path,headers=None,post=False):
                    return urllib.request.urlopen(urllib.request.Request(base+path,data=b'{}' if post else None,headers=headers or {}))
                with request('/api/config',{'Host':'mercyhouse.abhi07.xyz'}) as response:
                    value=response.read().decode();self.assertNotIn('test-server-key',value);self.assertNotIn('test-character-key',value)
                for bad_origin in (None,'http://mercyhouse.abhi07.xyz','https://other.example','null'):
                    headers={'Host':'mercyhouse.abhi07.xyz','X-Mercy-CSRF':manager.csrf}
                    if bad_origin is not None:headers['Origin']=bad_origin
                    with self.assertRaises(urllib.error.HTTPError) as error:request('/api/runs',headers,True)
                    self.assertEqual(error.exception.code,403)
                with patch.object(manager,'start',return_value={'id':'test-run'}) as launch:
                    headers={'Host':'mercyhouse.abhi07.xyz','Origin':origin,'X-Mercy-CSRF':manager.csrf}
                    with request('/api/runs',headers,True) as response:self.assertEqual(response.status,202)
                    launch.assert_called_once_with({})
                for host in ('evil.example','mercyhouse.abhi07.xyz.evil.example','mercyhouse.abhi07.xyz:8443'):
                    with self.assertRaises(urllib.error.HTTPError) as error:request('/api/config',{'Host':host,'X-Forwarded-Host':'mercyhouse.abhi07.xyz','X-Forwarded-Proto':'https'})
                    self.assertEqual(error.exception.code,403)
                # Explicit public configuration doesn't break local health checks.
                with request('/api/config') as response:self.assertEqual(response.status,200)
            finally:server.shutdown();server.server_close();thread.join()

    def test_public_host_denied_when_not_explicitly_configured(self):
        with TemporaryDirectory() as folder,patch('mercy.viewer.server.credentials',return_value=DEFAULTS):
            manager=Manager(folder);server=ThreadingHTTPServer(('127.0.0.1',0),handler(manager))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                req=urllib.request.Request('http://127.0.0.1:'+str(server.server_port)+'/api/config',headers={'Host':'mercyhouse.abhi07.xyz','X-Forwarded-Host':'localhost'})
                with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(req)
                self.assertEqual(error.exception.code,403)
            finally:server.shutdown();server.server_close();thread.join()
