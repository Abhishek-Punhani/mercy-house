"""Provider wire adapters and a DNS-pinned, public-only HTTPS transport."""
import http.client
import ipaddress
import json
import socket
import ssl
from urllib.parse import urlsplit

PROVIDERS = [
    {'id': 'configured', 'name': 'Hackathon / configured provider', 'base_url': ''},
    {'id': 'openai', 'name': 'OpenAI', 'base_url': 'https://api.openai.com/v1'},
    {'id': 'anthropic', 'name': 'Anthropic / Claude', 'base_url': 'https://api.anthropic.com/v1'},
    {'id': 'gemini', 'name': 'Google Gemini', 'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai'},
    {'id': 'openrouter', 'name': 'OpenRouter', 'base_url': 'https://openrouter.ai/api/v1'},
    {'id': 'groq', 'name': 'Groq', 'base_url': 'https://api.groq.com/openai/v1'},
    {'id': 'deepseek', 'name': 'DeepSeek', 'base_url': 'https://api.deepseek.com/v1'},
    {'id': 'mistral', 'name': 'Mistral', 'base_url': 'https://api.mistral.ai/v1'},
    {'id': 'together', 'name': 'Together AI', 'base_url': 'https://api.together.xyz/v1'},
    {'id': 'fireworks', 'name': 'Fireworks AI', 'base_url': 'https://api.fireworks.ai/inference/v1'},
    {'id': 'xai', 'name': 'xAI', 'base_url': 'https://api.x.ai/v1'},
    {'id': 'cerebras', 'name': 'Cerebras', 'base_url': 'https://api.cerebras.ai/v1'},
    {'id': 'custom', 'name': 'Custom / Azure / OpenAI-compatible', 'base_url': ''},
]


def endpoint_url(base):
    if not isinstance(base, str) or len(base) > 500 or any(ord(c) <= 32 for c in base):
        raise ValueError('Invalid provider endpoint')
    url = urlsplit(base)
    if (url.scheme != 'https' or not url.hostname or url.username or url.password
            or url.query or url.fragment or url.port not in (None, 443)):
        raise ValueError('Use a public HTTPS endpoint on port 443, without credentials or query parameters')
    return url


def public_addresses(base):
    url = endpoint_url(base)
    try:
        addresses = list(dict.fromkeys(x[4][0] for x in socket.getaddrinfo(url.hostname, 443, type=socket.SOCK_STREAM)))
    except OSError:
        raise ValueError('Provider hostname could not be resolved') from None
    if not addresses or any(not ipaddress.ip_address(ip).is_global or ipaddress.ip_address(ip).is_multicast for ip in addresses):
        raise ValueError('Provider must resolve only to public internet addresses')
    return addresses


def provider_request(base, key, payload):
    url = endpoint_url(base)
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
    if url.hostname == 'api.anthropic.com':
        system, messages = [], []
        for message in payload['messages']:
            role = message['role']
            if role in ('system', 'developer'):
                system.append(message.get('content') or '')
                continue
            if role == 'tool':
                content = [{'type': 'tool_result', 'tool_use_id': message['tool_call_id'], 'content': message.get('content') or ''}]
                role = 'user'
            else:
                content = []
                if message.get('content'):
                    content.append({'type': 'text', 'text': message['content']})
                for call in message.get('tool_calls', []):
                    content.append({'type': 'tool_use', 'id': call['id'], 'name': call['function']['name'],
                                    'input': json.loads(call['function']['arguments'])})
            if not content:
                continue
            if messages and messages[-1]['role'] == role:
                messages[-1]['content'].extend(content)
            else:
                messages.append({'role': role, 'content': content})
        if payload.get('response_format', {}).get('type') == 'json_object':
            system.append('Return only one valid JSON object, without markdown fences.')
        body = {'model': payload['model'], 'max_tokens': payload['max_tokens'], 'system': '\n\n'.join(system), 'messages': messages}
        if payload.get('tools'):
            body['tools'] = [{'name': t['function']['name'], 'description': t['function'].get('description', ''),
                              'input_schema': t['function']['parameters']} for t in payload['tools']]
        headers = {'Content-Type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01'}
        return base.rstrip('/') + ('/messages' if url.path.rstrip('/').endswith('/v1') else '/v1/messages'), headers, body
    body = dict(payload)
    if url.hostname == 'api.openai.com':
        body['max_completion_tokens'] = body.pop('max_tokens')
    path = url.path.rstrip('/')
    # Any explicit versioned/custom path is the caller's API root, not /v1/v1.
    suffix = '/chat/completions' if path else '/v1/chat/completions'
    return base.rstrip('/') + suffix, headers, body


def provider_response(base, value):
    if endpoint_url(base).hostname != 'api.anthropic.com':
        return value
    blocks = value.get('content', [])
    message = {'role': 'assistant', 'content': '\n'.join(b['text'] for b in blocks if b.get('type') == 'text') or None}
    calls = [{'id': b['id'], 'type': 'function', 'function': {'name': b['name'], 'arguments': json.dumps(b['input'])}}
             for b in blocks if b.get('type') == 'tool_use']
    if calls:
        message['tool_calls'] = calls
    return {'id': value.get('id'), 'model': value.get('model'), 'choices': [{'index': 0, 'message': message,
            'finish_reason': 'tool_calls' if calls else 'length' if value.get('stop_reason') == 'max_tokens' else 'stop'}],
            'usage': value.get('usage', {}), 'provider_protocol': 'anthropic_messages'}


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, hostname, address, timeout):
        super().__init__(hostname, timeout=timeout, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        # Connect to the validated IP, with certificate validation/SNI for the original host.
        # No second DNS lookup, redirects, proxy env, or caller-controlled Host header.
        sock = socket.create_connection((self.address, 443), self.timeout)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except Exception:
            sock.close()
            raise


def request_public_json(endpoint, headers, body, timeout):
    url = endpoint_url(endpoint)
    addresses = public_addresses(endpoint)
    connection = PinnedHTTPSConnection(url.hostname, addresses[0], timeout)
    try:
        connection.request('POST', url.path or '/', json.dumps(body).encode(), headers)
        response = connection.getresponse()
        wire = response.read(200001)
        if response.status != 200 or len(wire) > 200000:
            raise ValueError('Provider rejected the request or response too large')
        value = json.loads(wire)
        if not isinstance(value, dict) or value.get('error'):
            raise ValueError('Invalid provider response')
        return value
    finally:
        connection.close()
