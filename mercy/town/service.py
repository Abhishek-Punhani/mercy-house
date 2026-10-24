"""Private world service. No host port; authenticated orchestration only."""
import hmac
import json
import os
from pathlib import Path
import secrets
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .agents import ModelAgent, FixtureAgent
from .world import Town
from .io import append_log, write_json

class WorldService:
    def __init__(self,token,folder):self.token=token;self.folder=Path(folder);self.world=None;self.lock=threading.RLock()
    def dispatch(self,path,data):
        if path=='/tasks':
            from .tasks import TASKS, description
            return {'tasks':[description(key) for key in TASKS]}
        if path=='/gate':
            from .reference import gates
            from .tasks import task_id
            if set(data)!={'task_id','seed'} or type(data['seed']) is not int:raise ValueError('Invalid gate configuration')
            key=task_id(data['task_id']);folder=self.folder/'gates'/key
            gate=gates(key,data['seed'],folder)
            return {'gate':gate,'trajectories':{name:[json.loads(row) for row in (folder/name/'episode.jsonl').read_text().splitlines()] for name in ('reference','noop')},
                    'summaries':{name:json.loads((folder/name/'summary.json').read_text()) for name in ('reference','noop')}}
        if path=='/reset':
            from .factory import build
            if set(data)-{'task_id','seed','backend'}:raise ValueError('Unexpected reset configuration')
            backend=data.get('backend','llm')
            if backend not in ('fixture','llm'):raise ValueError('Invalid character backend')
            agent=ModelAgent(audit=lambda row:append_log(self.folder/'actors.jsonl',row)) if backend=='llm' else None
            self.world=build(data.get('task_id','last_witness'),data.get('seed',7),agent)
            self.persist()
            return {'opening':self.world.opening(),'state_hash':self.world.state_hash(),'seed':self.world.seed,'run_id':self.folder.name,'incident_occurred':True}
        if path=='/initialize':
            if self.world is not None:raise ValueError('Already initialized')
            if set(data)-{'backend','seed','rounds','pressure'}:raise ValueError('Unexpected configuration')
            backend=data.get('backend','llm');rounds=data.get('rounds',4);seed=data.get('seed',7)
            if backend not in ('fixture','llm') or type(rounds) is not int or not 1<=rounds<=12 or type(seed) is not int:raise ValueError('Invalid configuration')
            agent=FixtureAgent() if backend=='fixture' else ModelAgent(audit=lambda row:append_log(self.folder/'actors.jsonl',row))
            world=Town(seed,agent,pressure=data.get('pressure','urgent'))
            outcome=world.simulate(rounds)
            write_json(self.folder/'prelude.json',world.export_private())
            self.world=world
            if not outcome['incident_occurred']:return {'incident_occurred':False,'run_id':self.folder.name}
            initial=world.arrive();self.persist()
            return {'incident_occurred':True,'opening':initial,'run_id':self.folder.name}
        if self.world is None:raise ValueError('Not initialized')
        w=self.world
        if path=='/finish':
            reason=data.get('reason')
            if reason not in ('success','failure','step_cap','time_cap','crash'):raise ValueError('Invalid termination')
            if not w.ended:w.step('submit_report',{'findings':[],'narrative':'No final report before termination.'})
            w.termination_reason=reason;self.persist()
            return {'result':w.result,'state_hash':w.state_hash(),'ended':True,'minutes':w.clock}
        if path=='/action':
            if not {'action','args'}<=set(data) or set(data)-{'action','args','seconds'}:raise ValueError('Invalid request')
            budget=data.get('seconds',60)
            if type(budget) not in (int,float) or not .1<=budget<=60:raise ValueError('Invalid action deadline')
            if w.agents is not None:w.agents.deadline=time.monotonic()+budget
            observation=w.step(data['action'],data['args']);self.persist()
            return {'observation':observation,'ended':w.ended,'state_hash':w.state_hash(),'minutes':w.clock}
        if path=='/status':return {'ended':w.ended,'state_hash':w.state_hash(),'minutes':w.clock}
        if path=='/final':
            if not w.ended:raise ValueError('No score before report submission')
            return w.result
        raise ValueError('Unknown endpoint')
    def persist(self):
        write_json(self.folder/'world.json',self.world.export_private())
        write_json(self.folder/'audit.json',self.world.audit.rows)

def handler(service):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_GET(self):
            self.send_response(200 if self.path=='/health' else 404);self.end_headers()
        def do_POST(self):
            if not hmac.compare_digest(self.headers.get('X-World-Token',''),service.token):
                append_log(service.folder/'boundary-events.jsonl',{'event':'unauthenticated_request','path':self.path[:200]})
                self.send_response(403);self.end_headers();return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=65536:raise ValueError('Request too large')
                payload=json.loads(self.rfile.read(size))
                if not isinstance(payload,dict):raise ValueError('Object required')
                with service.lock:reply=service.dispatch(self.path,payload)
                code=200
            except (ValueError,TypeError,KeyError):reply={'error':'Invalid or unavailable operation'};code=400
            except Exception:reply={'error':'World service failed safely'};code=500
            self.send_response(code);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(reply).encode())
    return Handler

def main():
    tokenfile=Path(os.getenv('WORLD_TOKEN_FILE','/control/token'));tokenfile.parent.mkdir(parents=True,exist_ok=True)
    token=secrets.token_hex(32);tokenfile.write_text(token);tokenfile.chmod(0o600)
    folder=Path(os.getenv('PRIVATE_LOG_DIR','/logs/private'))/str(time.time_ns())
    service=WorldService(token,folder)
    ThreadingHTTPServer(('0.0.0.0',8000),handler(service)).serve_forever()

if __name__=='__main__':main()
