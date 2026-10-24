import json
import unittest
from unittest.mock import patch, MagicMock
from mercy.town.providers import provider_request, provider_response, endpoint_url, public_addresses, PinnedHTTPSConnection


class ProviderTests(unittest.TestCase):
    def test_compatible_paths_and_openai_output_token_field(self):
        payload={'model':'test','messages':[{'role':'user','content':'Hello'}],'max_tokens':300}
        for base in ('https://api.groq.com/openai/v1','https://generativelanguage.googleapis.com/v1beta/openai',
                     'https://openrouter.ai/api/v1','https://example.org/openai/v1'):
            endpoint,headers,body=provider_request(base,'visitor-key',payload)
            self.assertEqual(endpoint,base+'/chat/completions')
            self.assertEqual(headers['Authorization'],'Bearer visitor-key')
            self.assertEqual(body['max_tokens'],300)
        self.assertEqual(provider_request('https://example.org','k',payload)[0],'https://example.org/v1/chat/completions')
        body=provider_request('https://api.openai.com/v1','k',payload)[2]
        self.assertEqual(body['max_completion_tokens'],300);self.assertNotIn('max_tokens',body)

    def test_claude_tool_roundtrip_and_character_json_request(self):
        call={'id':'tool-1','type':'function','function':{'name':'look','arguments':'{"place":"hall"}'}}
        payload={'model':'claude-test','max_tokens':500,'messages':[{'role':'system','content':'Investigate.'},
            {'role':'user','content':'Begin'}, {'role':'assistant','content':None,'tool_calls':[call]},
            {'role':'tool','tool_call_id':'tool-1','content':'Observed hall'},
            {'role':'tool','tool_call_id':'tool-2','content':'Another result'}],
            'tools':[{'type':'function','function':{'name':'look','parameters':{'type':'object'},'description':'Look'}}],
            'response_format':{'type':'json_object'}}
        endpoint,headers,body=provider_request('https://api.anthropic.com/v1','visitor-key',payload)
        self.assertEqual(endpoint,'https://api.anthropic.com/v1/messages')
        self.assertEqual(headers['x-api-key'],'visitor-key');self.assertNotIn('Authorization',headers)
        self.assertEqual(body['messages'][1]['content'][0]['type'],'tool_use')
        self.assertEqual(len(body['messages'][2]['content']),2)
        self.assertEqual(body['tools'][0]['input_schema'],{'type':'object'})
        self.assertIn('JSON object',body['system'])
        value=provider_response('https://api.anthropic.com',{'content':[{'type':'text','text':'Inspecting'},
            {'type':'tool_use','id':'tool-1','name':'look','input':{'place':'hall'}}],'stop_reason':'tool_use'})
        actual=value['choices'][0]['message']['tool_calls'][0]
        self.assertEqual(actual['id'],call['id'])
        self.assertEqual(json.loads(actual['function']['arguments']),{'place':'hall'})
        self.assertEqual(value['choices'][0]['finish_reason'],'tool_calls')

    def test_custom_endpoint_cannot_reach_private_network_or_rebind(self):
        for base in ('http://example.org','https://user:pw@example.org','https://example.org?key=secret','https://example.org:8000'):
            with self.assertRaises(ValueError):endpoint_url(base)
        for ip in ('127.0.0.1','10.0.0.1','169.254.169.254','::1','fd00::1','::ffff:127.0.0.1','224.0.0.1','ff02::1'):
            with patch('mercy.town.providers.socket.getaddrinfo',return_value=[(None,None,None,None,(ip,443))]):
                with self.assertRaises(ValueError):public_addresses('https://custom.example/v1')
        with patch('mercy.town.providers.socket.getaddrinfo',return_value=[(None,None,None,None,('1.1.1.1',443))]):
            self.assertEqual(public_addresses('https://custom.example'),['1.1.1.1'])
        c=PinnedHTTPSConnection('custom.example','1.1.1.1',5);c._context=MagicMock()
        with patch('mercy.town.providers.socket.create_connection') as connect:
            c.connect();connect.assert_called_once_with(('1.1.1.1',443),5)
            self.assertEqual(c._context.wrap_socket.call_args.kwargs['server_hostname'],'custom.example')
