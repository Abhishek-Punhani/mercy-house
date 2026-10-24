"""Run INSIDE a temporary harness container with the real isolated workspace.

This orchestration probe is never mounted into an evaluated actor workspace.
No provider call is made. Do not run workspace.execute on the host.
"""
import json
from pathlib import Path
import shlex
import threading
from http.server import ThreadingHTTPServer

from mercy.town.client import Proxy, rpc, public_handler

controller = {}
server = ThreadingHTTPServer(('0.0.0.0', 8002), public_handler(controller))
threading.Thread(target=server.serve_forever, daemon=True).start()
results = {}


def reset():
    start = rpc('/reset', {'task_id': 'last_witness', 'seed': 7, 'backend': 'fixture'})
    proxy = Proxy(start['opening'])
    proxy.hash = start['state_hash']
    controller['world'] = proxy
    return proxy


proxy = reset()


def command(text):
    result = proxy.step('run_command', {'command': text})
    if result.get('timed_out') or result.get('exit_code') != 0:
        raise AssertionError('Probe command failed: ' + str(result))
    return result


def town(tool, args=None):
    text = 'town ' + shlex.quote(tool) + ' ' + shlex.quote(json.dumps(args or {}))
    return json.loads(command(text)['stdout'])


assert town('look')['place']['id'] == 'archive'
results['real_command_to_public_world'] = True
check = '''import os, pathlib, urllib.request, urllib.error
assert not os.environ.get("API_KEY") and not os.environ.get("NPC_API_KEY")
assert not pathlib.Path("/control/token").exists()
assert not pathlib.Path("/app/mercy/town/world.py").exists()
assert not pathlib.Path("/app/mercy/town/verifier.py").exists()
assert not pathlib.Path("/app/mercy/town/family_data.py").exists()
assert not pathlib.Path("/app/mercy/town/family_proof.py").exists()
assert not pathlib.Path("/app/mercy/audit/review.py").exists()
assert not pathlib.Path("/app/mercy/rl/source_curriculum.py").exists()
assert not pathlib.Path("/app/mercy/town/data").exists()
try:
 urllib.request.urlopen("https://example.com",timeout=2)
 raise AssertionError("External egress unexpectedly available")
except (OSError,urllib.error.URLError): pass
try:
 urllib.request.urlopen(urllib.request.Request("http://world:8000/reset",data=b"{}"),timeout=2)
 raise AssertionError("Private route unexpectedly available")
except urllib.error.HTTPError as e: assert e.code==403
print("isolated")'''
assert command('python -c ' + shlex.quote(check))['stdout'].strip() == 'isolated'
results['no_keys_no_control_no_private_files_no_external_egress'] = True
before = proxy.state_hash()
denied = proxy.step('run_command', {'command': 'town /reset'})
assert denied.get('exit_code') == 1 and 'error' in json.loads(denied['stdout'])
assert before == proxy.state_hash()
results['public_gateway_cannot_reset_or_read_private_routes'] = True
proxy.action_timeout = 1.5
timed = proxy.step('run_command', {'command': 'sleep 4'})
assert timed.get('timed_out') or 'error' in timed
proxy.action_timeout = 60
assert town('look')['place']['id'] == 'archive'
results['timeout_then_continue'] = True
command('printf %s forged-proof > /workspace/proof.txt')
town('submit_report', {'findings': [{'actor': 'savitri', 'predicate': 'killed', 'object': 'mira', 'sources': ['/workspace/proof.txt']}]})
assert proxy.result['score'] == 0.
results['fake_workspace_evidence_cannot_score'] = True

# A real supported solution remains reachable after the boundary tests.
proxy = reset()
town('people_here')
floor = town('search', {'surface': 'floor'})['findings']
town('go', {'destination': 'hall'})
town('people_here')
sources = [r['record_id'] for r in floor]
for _ in range(2):
    statement = town('ask', {'pid': 'vedant', 'question': 'What did you personally see in the archive?', 'approach': 'reassure', 'show': sources})
    sources.append(statement['record_id'])
town('submit_report', {'findings': [{'actor': 'savitri', 'predicate': 'killed', 'object': 'mira', 'sources': sources}]})
assert proxy.result['score'] >= .95
results['legitimate_solution_through_real_commands'] = True
path = Path('/logs/public/command-isolation-probe.json')
path.write_text(json.dumps({'passed': True, 'checks': results}, indent=2) + '\n')
print(json.dumps({'passed': True, 'checks': results}), flush=True)
server.shutdown()
