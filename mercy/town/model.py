"""Trusted model transport; optional fixed-destination API gateway."""
import json
import os
from pathlib import Path
import urllib.request
import threading
import queue


def _request(messages, tools=None, timeout=60, max_tokens=3500):
    payload = {'model': os.getenv('MODEL', 'gpt-6-luna'), 'messages': messages, 'max_tokens': max_tokens}
    if tools:
        payload['tools'] = tools
    gateway = os.getenv('MODEL_GATEWAY_URL')
    if gateway:
        url = gateway.rstrip('/') + '/detective'
        token = Path(os.getenv('WORLD_TOKEN_FILE', '/control/token')).read_text().strip()
        headers = {'X-World-Token': token, 'Content-Type': 'application/json'}
    else:
        base = os.environ['BASE_URL'].rstrip('/')
        url = base + ('/chat/completions' if base.endswith('/v1') else '/v1/chat/completions')
        headers = {'Authorization': 'Bearer ' + os.environ['API_KEY'], 'Content-Type': 'application/json'}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=max(.1, timeout)) as response:
        wire = response.read(200001)
    if len(wire) > 200000:
        raise ValueError('Model response exceeded size cap')
    try:
        raw = json.loads(wire)
    except (ValueError, UnicodeDecodeError):
        # Preserve unreadable provider output in the reply log. The harness
        # consumes this reply and gives feedback instead of crashing.
        raw = None
    return raw, wire.decode('utf-8')


def request(messages, tools=None, timeout=60, max_tokens=3500):
    result=queue.Queue(maxsize=1)
    def work():
        try:result.put((True,_request(messages,tools,timeout,max_tokens)))
        except Exception as exc:result.put((False,exc))
    threading.Thread(target=work,daemon=True).start()
    try:ok,value=result.get(timeout=max(.1,timeout))
    except queue.Empty:raise TimeoutError('Model request deadline exceeded') from None
    if not ok:raise value
    return value
