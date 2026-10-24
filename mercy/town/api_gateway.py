"""Trusted fixed-destination model gateway; the only externally networked role."""
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time
import urllib.request

TOKEN = Path(os.getenv('WORLD_TOKEN_FILE', '/control/token'))
LOCK = threading.Lock()
RECENT = []


def configuration(npc=False):
    shared = os.getenv('ALLOW_SHARED_NPC_KEY', '0') == '1'
    if npc:
        return (os.getenv('NPC_API_KEY') or (os.getenv('API_KEY', '') if shared else ''),
                os.getenv('NPC_BASE_URL') or (os.getenv('BASE_URL', '') if shared else ''),
                os.getenv('NPC_MODEL') or os.getenv('MODEL', ''))
    return os.getenv('API_KEY', ''), os.getenv('BASE_URL', ''), os.getenv('MODEL', '')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Model redirects are disabled')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        if self.path not in ('/detective', '/character', '/ready') or not hmac.compare_digest(self.headers.get('X-World-Token', ''), TOKEN.read_text().strip()):
            self.send_response(403); self.end_headers(); return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 250000:
                raise ValueError('Invalid request size')
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict) or set(data) - {'model', 'messages', 'tools', 'max_tokens', 'response_format'}:
                raise ValueError('Invalid model request')
            if not isinstance(data.get('messages'), list):
                raise ValueError('Messages required')
            if self.path == '/ready':
                roles = {role: bool(key and base.startswith('https://') and model)
                         for role, (key, base, model) in [('detective', configuration()), ('character', configuration(True))]}
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps(roles).encode()); return
            npc = self.path == '/character'
            key, base, model = configuration(npc)
            if not key or not base or not model:
                raise ValueError('Model role is not configured')
            if not base.startswith('https://'):
                raise ValueError('External model endpoint must use HTTPS')
            with LOCK:
                now = time.monotonic()
                RECENT[:] = [x for x in RECENT if now - x < 60]
                if len(RECENT) >= 60:
                    raise ValueError('Model gateway request rate exceeded; retry later')
                RECENT.append(now)
            payload = {'model': model, 'messages': data['messages'], 'max_tokens': min(650 if npc else 3500, int(data.get('max_tokens', 650 if npc else 3500)))}
            for field in ('tools', 'response_format'):
                if field in data:
                    payload[field] = data[field]
            base = base.rstrip('/')
            endpoint = base + ('/chat/completions' if base.endswith('/v1') else '/v1/chat/completions')
            req = urllib.request.Request(endpoint, data=json.dumps(payload).encode(),
                    headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            with urllib.request.build_opener(NoRedirect()).open(req, timeout=15 if npc else 55) as response:
                wire = response.read(200001)
            if len(wire) > 200000:
                raise ValueError('Provider response too large')
            code = 200
        except Exception:
            code, wire = 502, b'{"error":"Configured model API unavailable or request rejected"}'
        try:
            self.send_response(code); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(wire)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 8001), Handler).serve_forever()
