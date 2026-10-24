"""Public-only detective harness and fixed-destination NPC API broker.

Its image contains no setting, world engine, private snapshots or solution code.
"""
import hmac
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import urllib.request
import time
from .detective import run_detective
from .io import write_json
from .io import append_log
from .harness import run as run_harness, instructions

TOKENFILE=Path(os.getenv('WORLD_TOKEN_FILE','/control/token'))

def rpc(path,payload,timeout=None):
    token=TOKENFILE.read_text().strip()
    req=urllib.request.Request(os.getenv('WORLD_URL','http://world:8000')+path,data=json.dumps(payload).encode(),headers={'X-World-Token':token,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout or (600 if path=='/initialize' else 120 if path=='/gate' else 60)) as response:return json.load(response)

class Proxy:
    def __init__(self,opening,observer=None):self.initial=opening;self.ended=False;self.clock=0;self.hash='';self.seed=int(os.getenv('SEED','7'));self.action_timeout=60;self.lock=threading.RLock();self.observer=observer;self.reply_count=0
    def opening(self):return self.initial
    def model_wait(self,step):
        if self.observer:self.observer({'phase':'model_wait','reply':step})
    def model_note(self,note,step):
        if self.observer and note:self.observer({'phase':'reply_note','reply':step,'note':note[:1800]})
    def step(self,action,args):
        if self.observer:self.observer({'phase':'start','action':{'tool':action,'args':args},'reply':self.reply_count})
        if action=='run_command':
            from .validation import validate_action
            validate_action(action,args)
            payload={'command':args['command'],'seconds':max(.1,self.action_timeout-1)}
            req=urllib.request.Request(os.getenv('WORKSPACE_URL','http://workspace:8003')+'/execute',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            try:
                with urllib.request.urlopen(req,timeout=self.action_timeout) as response:observation=json.load(response)
            except (OSError,TimeoutError):observation={'error':'Command workspace timed out or is unavailable; other tools remain available'}
            if observation.get('timed_out'):observation['error']='Command timed out; partial output is retained and other tools remain available'
            with self.lock:
                status=rpc('/status',{});self.ended=status['ended'];self.clock=status['minutes'];self.hash=status['state_hash']
            if self.observer:self.observer({'phase':'result','action':{'tool':action,'args':args},'observation':observation,'reply':self.reply_count,'state':self.hash,'minutes':self.clock})
            return observation
        with self.lock:
            result=rpc('/action',{'action':action,'args':args,'seconds':self.action_timeout},timeout=self.action_timeout);self.ended=result['ended'];self.clock=result['minutes'];self.hash=result['state_hash']
            if self.observer:self.observer({'phase':'result','action':{'tool':action,'args':args},'observation':result['observation'],'reply':self.reply_count,'state':self.hash,'minutes':self.clock})
            return result['observation']
    def state_hash(self):return self.hash
    @property
    def result(self):return rpc('/final',{}) if self.ended else None
    def finish(self,reason):
        result=rpc('/finish',{'reason':reason},timeout=120);self.ended=True;self.hash=result['state_hash'];self.clock=result['minutes'];return result['result']

def public_handler(controller):
    class PublicGateway(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_POST(self):
            try:
                if self.path!='/tool':raise ValueError('Unknown public route')
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=30000:raise ValueError('Invalid size')
                value=json.loads(self.rfile.read(size))
                if not isinstance(value,dict) or set(value)!={'action','args'} or value['action']=='run_command':raise ValueError('Invalid public action')
                from .validation import validate_action
                validate_action(value['action'],value['args'])
                proxy=controller.get('world')
                if proxy is None:raise ValueError('No active investigation')
                result=proxy.step(value['action'],value['args']);code=200
            except Exception:result={'error':'Unavailable public action; no privileged operation is exposed'};code=400
            try:
                self.send_response(code);self.end_headers();self.wfile.write(json.dumps(result).encode())
            except (BrokenPipeError,ConnectionResetError):pass
    return PublicGateway

class Broker(BaseHTTPRequestHandler):
    def log_message(self,*_):pass
    def do_POST(self):
        if self.path!='/character' or not hmac.compare_digest(self.headers.get('X-World-Token',''),TOKENFILE.read_text().strip()):
            self.send_response(403);self.end_headers();return
        code=200
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=200000:raise ValueError('Size')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict) or set(data)-{'model','messages','max_tokens','response_format'}:raise ValueError('Invalid broker request')
            messages=data.get('messages')
            if not isinstance(messages,list) or len(messages)>16:raise ValueError('Invalid messages')
            if not all(isinstance(m,dict) and set(m)=={'role','content'} and m['role'] in ('system','user','assistant') and isinstance(m['content'],str) for m in messages):raise ValueError('Invalid message')
            base=(os.getenv('NPC_BASE_URL') or os.environ['BASE_URL']).rstrip('/')
            endpoint=base+('/chat/completions' if base.endswith('/v1') else '/v1/chat/completions')
            body={'model':os.getenv('NPC_MODEL') or os.getenv('MODEL','gpt-6-luna'),'messages':messages,'max_tokens':650,'response_format':{'type':'json_object'}}
            key=os.getenv('NPC_API_KEY') or os.environ['API_KEY']
            req=urllib.request.Request(endpoint,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
            # Broker deadline precedes the world's 20-second client deadline.
            with urllib.request.urlopen(req,timeout=15) as response:wire=response.read(100001)
            if len(wire)>100000:raise ValueError('Response too large')
        except Exception:
            code=502;wire=b'{"error":"Character provider unavailable"}'
        try:
            self.send_response(code);self.end_headers();self.wfile.write(wire)
        except (BrokenPipeError,ConnectionResetError):
            # The caller may have timed out. It cannot gain a world action from
            # this transport failure, and no traceback/private input is printed.
            pass

def main():
    mode=os.getenv('MODE','full')
    if mode not in ('full','all','baselines'):raise ValueError('MODE must be full, all or baselines')
    if mode!='baselines':instructions()
    from .tasks import TASKS, task_id
    selected=list(TASKS) if mode in ('all','baselines') else [task_id(os.getenv('TASK_ID','lantern_room'))]
    seed=int(os.getenv('SEED','7'))
    controller={}
    gateway=ThreadingHTTPServer(('0.0.0.0',8002),public_handler(controller))
    threading.Thread(target=gateway.serve_forever,daemon=True).start()
    folder=Path(os.getenv('PUBLIC_LOG_DIR','/logs/public'))/str(time.time_ns());folder.mkdir(parents=True)
    gate_rows=[]
    for task in selected:
        gate=rpc('/gate',{'task_id':task,'seed':seed})
        gate_rows.append(gate['gate'])
        write_json(folder/'gate.json',gate_rows)
        for name,trajectory in gate['trajectories'].items():
            target=folder/'baselines'/task/name
            write_json(target/'summary.json',gate['summaries'][name])
            for row in trajectory:append_log(target/'episode.jsonl',row)
        print(json.dumps({'baseline_gate':gate['gate']}),flush=True)
        if not gate['gate']['passed']:raise RuntimeError('Gate rejected; model not called')
        if mode=='baselines':continue
        ready_url=os.getenv('MODEL_GATEWAY_URL','http://model-gateway:8001').rstrip('/')+'/ready'
        req=urllib.request.Request(ready_url,data=b'{"messages":[]}',headers={'Content-Type':'application/json','X-World-Token':TOKENFILE.read_text().strip()})
        with urllib.request.urlopen(req,timeout=10) as response:ready=json.load(response)
        if not ready.get('detective') or (os.getenv('NPC_BACKEND','llm')=='llm' and not ready.get('character')):
            raise RuntimeError('Model roles are not configured. Set MODEL/API_KEY/BASE_URL and independent NPC_MODEL/NPC_API_KEY/NPC_BASE_URL; development sharing must be explicitly enabled.')
        start=rpc('/reset',{'task_id':task,'seed':seed,'backend':os.getenv('NPC_BACKEND','llm')})
        run_folder=folder/task
        event_lock=threading.Lock()
        def observe(event):
            with event_lock:append_log(run_folder/'actions.jsonl',{'timestamp':time.time(),**event})
        world=Proxy(start['opening'],observer=observe);world.hash=start['state_hash'];world.seed=seed;controller['world']=world
        write_json(run_folder/'run.json',{'world_run_id':start.get('run_id'),'mode':mode,'task_id':task,'seed':seed})
        summary=run_harness(world,run_folder,40)
        print(json.dumps(summary),flush=True)
        controller.pop('world',None)
        if summary['termination_reason']=='crash':raise RuntimeError('Model run crashed; inspect logs')

if __name__=='__main__':main()
