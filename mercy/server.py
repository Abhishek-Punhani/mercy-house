"""Private world service: never publish its port or mount it into an agent shell."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from .env import Environment

env = None
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass
    def do_POST(self):
        global env
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0 < size <= 65536:
                raise ValueError('Invalid request size')
            data=json.loads(self.rfile.read(size))
            if self.path == '/reset':
                env=Environment(data['task_id'],data['seed']); result=env.observe()
            elif env is None:
                raise ValueError('Reset first')
            elif self.path == '/step':
                result=env.step(data['action'],data['args'])
            elif self.path == '/result':
                # Trusted harness only. This endpoint is never exposed as an agent tool.
                result={'result':env.result,'state_hash':env.state_hash(),'terminated':env.state['terminated']}
            elif self.path == '/finish':
                result=env.finish(data['reason'])
            else:
                raise ValueError('Unknown endpoint')
            raw=json.dumps(result).encode(); self.send_response(200)
        except Exception as exc:
            raw=json.dumps({'error':str(exc)[:300]}).encode(); self.send_response(400)
        self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(raw)

if __name__ == '__main__':
    HTTPServer(('0.0.0.0',8000),Handler).serve_forever()
