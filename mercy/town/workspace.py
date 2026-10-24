"""Unprivileged public command workspace. No world code, keys or control mount."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import resource
import signal
import subprocess
import tempfile
import threading
import time

LOCK = threading.Lock()


def cleanup():
    # Also remove detached children. The container has its own PID namespace,
    # a single serialized command, no other user workloads and a 64-PID limit.
    current = os.getpid()
    for entry in os.listdir('/proc'):
        if entry.isdigit() and int(entry) not in (1, current):
            try:
                if os.stat('/proc/' + entry).st_uid == os.getuid():
                    os.kill(int(entry), signal.SIGKILL)
            except (ProcessLookupError, PermissionError, FileNotFoundError):
                pass


def limits():
    resource.setrlimit(resource.RLIMIT_FSIZE, (1_000_000, 1_000_000))
    resource.setrlimit(resource.RLIMIT_CPU, (55, 55))


def execute(command, seconds):
    if not isinstance(command, str) or not 1 <= len(command) <= 16000:
        raise ValueError('Command must contain 1–16000 characters')
    seconds = max(.1, min(59., float(seconds)))
    started = time.monotonic()
    env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/workspace',
           'TOWN_GATEWAY_URL': os.getenv('TOWN_GATEWAY_URL', 'http://harness:8002'),
           'PYTHONDONTWRITEBYTECODE': '1'}
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen(['/bin/bash', '-c', command], cwd='/workspace', env=env,
                                   stdout=stdout, stderr=stderr, start_new_session=True, preexec_fn=limits)
        timed_out = False
        try:
            process.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=2)
        finally:
            cleanup()
        stdout.seek(0); stderr.seek(0)
        out, err = stdout.read(16001), stderr.read(8001)
    return {'exit_code': process.returncode, 'timed_out': timed_out,
            'stdout': out[:16000].decode('utf-8', errors='replace'),
            'stderr': err[:8000].decode('utf-8', errors='replace'),
            'truncated': len(out) > 16000 or len(err) > 8000,
            'seconds': round(time.monotonic() - started, 3)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        try:
            if self.path != '/execute':
                raise ValueError('Unknown operation')
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 20000:
                raise ValueError('Invalid request size')
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict) or set(data) != {'command', 'seconds'}:
                raise ValueError('Expected command and seconds')
            with LOCK:
                result = execute(data['command'], data['seconds'])
            code = 200
        except Exception:
            result, code = {'error': 'Command rejected or workspace unavailable'}, 400
        try:
            self.send_response(code); self.end_headers(); self.wfile.write(json.dumps(result).encode())
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 8003), Handler).serve_forever()
