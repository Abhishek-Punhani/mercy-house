"""Loopback-only story observer and trusted, opt-in Docker run launcher.

Usage: python -m mercy.viewer.server --port 8787
The browser never receives private world/actor files or configured API keys.
"""
import argparse
import hmac
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import threading
import time
from urllib.parse import urlsplit, parse_qs

from mercy.town.tasks import TASKS, description, task_id
from .events import opening, observation, action_event, reply_event, verdict

ROOT=Path(__file__).resolve().parents[2]
STATIC=ROOT/'viewer'


def credentials():
    result={}
    if (ROOT/'.env').is_file():
        for line in (ROOT/'.env').read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                key,value=line.split('=',1);result[key.strip()]=value.strip().strip('"').strip("'")
    return {**result,**os.environ}


def configuration(data, defaults):
    if not isinstance(data,dict) or set(data)-{'task_id','seed','model','base_url','api_key','use_configured_key'}:raise ValueError('Unknown run option')
    task=task_id(data.get('task_id','lantern_room'))
    seed=data.get('seed',7)
    if type(seed) is not int or not -(2**63)<=seed<2**63:raise ValueError('Seed must be a signed 64-bit integer')
    model=data.get('model') or defaults.get('MODEL','gpt-6-luna')
    if not isinstance(model,str) or not re.fullmatch(r'[A-Za-z0-9._:/@+-]{1,160}',model):raise ValueError('Invalid model deployment name')
    base=data.get('base_url') or defaults.get('BASE_URL','')
    if not isinstance(base,str) or len(base)>500 or any(ord(c)<32 for c in base):raise ValueError('Invalid endpoint')
    url=urlsplit(base)
    if url.scheme!='https' or not url.hostname or url.username or url.password or url.query or url.fragment:raise ValueError('Use an HTTPS base URL without credentials, query or fragment')
    if type(data.get('use_configured_key',False)) is not bool:raise ValueError('Invalid configured-key option')
    key=defaults.get('API_KEY','') if data.get('use_configured_key') else data.get('api_key','')
    if not isinstance(key,str) or not 1<=len(key)<=1024 or any(c in key for c in '\r\n\x00'):raise ValueError('Provide an API key or choose the configured key')
    shared=defaults.get('ALLOW_SHARED_NPC_KEY')=='1'
    # Judge override NEVER becomes the town's credential implicitly.
    npc_key=defaults.get('NPC_API_KEY') or (defaults.get('API_KEY','') if shared else '')
    npc_base=defaults.get('NPC_BASE_URL') or (defaults.get('BASE_URL','') if shared else '')
    npc_model=defaults.get('NPC_MODEL') or defaults.get('MODEL','gpt-6-luna')
    if not npc_key or not npc_base.startswith('https://'):raise ValueError('Configure the town character endpoint and credential in the server .env first')
    return {'task_id':task,'seed':seed,'model':model,'base_url':base.rstrip('/'),'key':key,
            'npc_key':npc_key,'npc_base':npc_base,'npc_model':npc_model}


class Run:
    def __init__(self,ident,meta,folder=None,secrets_to_hide=()):
        self.id=ident;self.meta=meta;self.folder=folder;self.events=[];self.changed=threading.Condition()
        self.status='starting';self.process=None;self.stopped=False;self.closed=False;self.hidden=tuple(s for s in secrets_to_hide if s)
        self.seen={};self.project='mercy-ui-'+ident
    def emit(self,value):
        def redact(item):
            if isinstance(item,str):
                for secret in self.hidden:item=item.replace(secret,'[REDACTED]')
                return item
            if isinstance(item,list):return [redact(v) for v in item]
            if isinstance(item,dict):return {k:redact(v) for k,v in item.items()}
            return item
        value=redact(value)
        with self.changed:
            value['seq']=len(self.events)+1;self.events.append(value)
            if self.folder:
                with (self.folder/'public-events.jsonl').open('a') as file:file.write(json.dumps(value,ensure_ascii=False)+'\n')
            self.changed.notify_all()
    def public(self):return {'id':self.id,**self.meta,'status':self.status,'event_count':len(self.events)}


class Manager:
    def __init__(self,root=ROOT):
        self.root=Path(root);self.defaults=credentials();self.runs={};self.lock=threading.Lock();self.csrf=secrets.token_urlsafe(32)
        catalog=self.root/'viewer/data/catalog.json'
        if catalog.exists():
            for entry in json.loads(catalog.read_text()):
                path=self.root/'viewer/data'/(entry['id']+'.json')
                payload=json.loads(path.read_text());run=Run(entry['id'],entry);run.events=payload['events'];run.status='recorded';run.closed=True;self.runs[run.id]=run
        saved=self.root/'logs/ui-runs'
        if saved.exists():
            for path in sorted(saved.glob('*/meta.json')):
                try:
                    meta=json.loads(path.read_text());ident=path.parent.name
                    if not re.fullmatch(r'[a-f0-9]{10}',ident):continue
                    run=Run(ident,{**meta,'kind':'recorded-model','label':meta['label']+' · saved replay'})
                    eventfile=path.parent/'public-events.jsonl'
                    run.events=[json.loads(line) for line in eventfile.read_text().splitlines()]
                    run.status='recorded';run.closed=True;self.runs[ident]=run
                except (OSError,ValueError,KeyError):continue
    def settings(self):
        shared=self.defaults.get('ALLOW_SHARED_NPC_KEY')=='1'
        return {'tasks':[description(k) for k in TASKS],
          'defaults':{'model':self.defaults.get('MODEL','gpt-6-luna'),'base_url':self.defaults.get('BASE_URL',''),'seed':7},
          'key_configured':bool(self.defaults.get('API_KEY')),
          'characters_configured':bool(self.defaults.get('NPC_API_KEY') or shared and self.defaults.get('API_KEY')),
          'docker_available':__import__('shutil').which('docker') is not None}
    def start(self,data):
        config=configuration(data,self.defaults)
        with self.lock:
            if any(not r.closed for r in self.runs.values()):raise ValueError('A live investigation is already running')
            ident=secrets.token_hex(5);folder=self.root/'logs/ui-runs'/ident;folder.mkdir(parents=True)
            for kind in ('public','private'):(folder/kind).mkdir()
            meta={'id':ident,'kind':'live-model','label':TASKS[config['task_id']]['name']+' · '+config['model'],
                  'difficulty':TASKS[config['task_id']]['difficulty'],'family':TASKS[config['task_id']].get('family','mercy_house'),
                  'task_id':config['task_id'],'seed':config['seed'],'model':config['model'],'created_at':time.time(),
                  'description':'Live API detective with independent town character agents.'}
            (folder/'meta.json').write_text(json.dumps(meta,indent=2)+'\n')
            run=Run(ident,meta,folder,(config['key'],config['npc_key']));self.runs[ident]=run
            threading.Thread(target=self.execute,args=(run,config),daemon=True).start()
        return run.public()
    def stop(self,run):
        if run.closed:return
        run.stopped=True;run.status='stopping';run.emit({'type':'status','message':'Stopping the live containers. An interrupted run is not a graded success.'})
        threading.Thread(target=self.down,args=(run,),daemon=True).start()
    def command(self,run):
        return ['docker','compose','-f',str(self.root/'docker-compose.yml'),'-f',str(run.folder/'compose.json'),'-p',run.project]
    def down(self,run):
        if (run.folder/'compose.json').exists():
            try:subprocess.run(self.command(run)+['down'],cwd=self.root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
            except (OSError,subprocess.TimeoutExpired):pass
    def consume(self,run):
        if run.closed:return
        for path in sorted((run.folder/'public').glob('*/*/opening.json')):
            if str(path) not in run.seen:
                try:run.emit({'type':'opening','opening':opening(json.loads(path.read_text()))});run.seen[str(path)]=True;run.status='running'
                except (OSError,ValueError):continue
            actions=path.parent/'actions.jsonl';episodes=path.parent/'episode.jsonl'
            for source in (actions,episodes):
                if not source.exists():continue
                try:lines=source.read_text().splitlines(keepends=True)
                except OSError:continue
                position=run.seen.get(str(source),0)
                for line in lines[position:]:
                    if not line.endswith('\n'):break
                    try:value=json.loads(line)
                    except ValueError:break
                    if source==actions:
                        if value.get('phase')=='model_wait':run.emit({'type':'activity','reply':value.get('reply'),'action':{'tool':'model_request','args':{}}})
                        elif value.get('phase')=='reply_note':run.emit({'type':'reply','reply':value.get('reply'),'note':value.get('note')})
                        elif value.get('phase')=='start':run.emit({'type':'activity','reply':value.get('reply'),'action':value['action']})
                        else:run.emit(action_event(value['action'],value.get('observation',{}),value.get('reply'),value.get('minutes')))
                    else:run.emit(reply_event(value))
                    position+=1
                run.seen[str(source)]=position
            summary=path.parent/'summary.json'
            if summary.exists() and str(summary) not in run.seen:
                try:
                    value=json.loads(summary.read_text());run.emit({'type':'finished','termination':value['termination_reason'],'result':verdict(value['result'] or {}),'seconds':value.get('seconds')});run.seen[str(summary)]=True
                except (OSError,ValueError,KeyError):continue
    def execute(self,run,config):
        try:self._execute(run,config)
        except Exception:
            run.status='error'
            try:run.emit({'type':'run_error','message':'Unable to prepare the isolated run. No model call or successful grade is inferred.'})
            finally:
                self.down(run);run.hidden=();run.closed=True
                with run.changed:run.changed.notify_all()
    def _execute(self,run,config):
        context=run.folder/'source'
        context.mkdir()
        shutil.copytree(self.root/'mercy',context/'mercy',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for name in ('Dockerfile.world','Dockerfile.detective','Dockerfile.gateway','Dockerfile.workspace','.dockerignore'):
            shutil.copyfile(self.root/name,context/name)
        manifest={str(p.relative_to(context)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(context.rglob('*')) if p.is_file()}
        (run.folder/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        env=dict(os.environ)
        variables={'MODEL':config['model'],'API_KEY':config['key'],'BASE_URL':config['base_url'],
                  'NPC_API_KEY':config['npc_key'],'NPC_BASE_URL':config['npc_base'],'NPC_MODEL':config['npc_model']}
        aliases={name:'MERCY_UI_'+name for name in variables}
        env.update({aliases[k]:v for k,v in variables.items()})
        env.update({'MODE':'full','MODEL':config['model'],'TASK_ID':config['task_id'],'SEED':str(config['seed']),'NPC_BACKEND':'llm'})
        override={'services':{'model-gateway':{'environment':{k:'${'+alias+'}' for k,alias in aliases.items()}},
           'harness':{'volumes':[str(run.folder/'public')+':/logs/public']},
           'world':{'volumes':[str(run.folder/'private')+':/logs/private']}}}
        for role in ('world','harness','model-gateway','workspace'):
            override['services'].setdefault(role,{})['build']={'context':str(context)}
        (run.folder/'compose.json').write_text(json.dumps(override,indent=2)+'\n')
        run.status='building';run.emit({'type':'status','message':'Building isolated containers and checking the selected task’s reference/no-op gate.'})
        try:
            with (run.folder/'docker.log').open('w') as log:
                run.process=subprocess.Popen(self.command(run)+['up','--build','--abort-on-container-exit','--exit-code-from','harness'],cwd=self.root,env=env,stdout=log,stderr=subprocess.STDOUT)
                deadline=time.monotonic()+950
                while run.process.poll() is None:
                    self.consume(run)
                    if time.monotonic()>deadline or run.stopped:
                        run.stopped=True;self.down(run);break
                    time.sleep(.35)
                self.consume(run)
            graded=any(e['type']=='finished' for e in run.events)
            if not graded:
                run.emit({'type':'stopped' if run.stopped else 'run_error','message':'Investigation stopped before a graded report.' if run.stopped else 'The run could not finish. Check the local Docker log and model configuration; no success is inferred.'})
            run.status='stopped' if run.stopped else 'finished' if graded else 'error'
        except Exception:
            run.status='error';run.emit({'type':'run_error','message':'Unable to launch the isolated run. Confirm Docker is running and the configured model endpoints are reachable.'})
        finally:
            self.down(run);run.hidden=();run.closed=True
            with run.changed:run.changed.notify_all()


def handler(manager):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def local(self):
            host=self.headers.get('Host','').split(':')[0]
            return host in ('localhost','127.0.0.1')
        def send(self,value,code=200):
            data=json.dumps(value,ensure_ascii=False).encode();self.send_response(code)
            self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
        def do_GET(self):
            if not self.local():self.send({'error':'Loopback access only'},403);return
            url=urlsplit(self.path);path=url.path
            if path=='/api/config':self.send(manager.settings());return
            if path=='/api/runs':
                with manager.lock:items=[r.public() for r in manager.runs.values()]
                self.send({'runs':items});return
            match=re.fullmatch(r'/api/runs/([A-Za-z0-9_-]+)(/events)?',path)
            if match:
                run=manager.runs.get(match[1])
                if not run:self.send({'error':'Unknown investigation'},404);return
                if not match[2]:
                    with run.changed:payload={**run.public(),'events':list(run.events)}
                    self.send(payload);return
                try:cursor=max(int(parse_qs(url.query).get('after',['0'])[0]),int(self.headers.get('Last-Event-ID','0')))
                except ValueError:self.send({'error':'Invalid event cursor'},400);return
                self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Cache-Control','no-store');self.end_headers()
                until=time.monotonic()+25
                try:
                    while time.monotonic()<until:
                        with run.changed:
                            available=run.events[cursor:]
                            if not available and not run.closed:run.changed.wait(timeout=2)
                        for event in available:
                            self.wfile.write(('id: '+str(event['seq'])+'\ndata: '+json.dumps(event,ensure_ascii=False)+'\n\n').encode());cursor=event['seq']
                        self.wfile.write(b': heartbeat\n\n');self.wfile.flush()
                        if run.closed and cursor>=len(run.events):return
                except (BrokenPipeError,ConnectionResetError):pass
                return
            files={'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/art.js':('art.js','text/javascript'),'/state.js':('state.js','text/javascript'),'/styles.css':('styles.css','text/css')}
            if path not in files:self.send({'error':'Not found'},404);return
            name,mime=files[path];file=STATIC/name
            if not file.is_file():self.send({'error':'Viewer assets missing'},404);return
            data=file.read_bytes()
            if name=='index.html':data=data.replace(b'__CSRF_TOKEN__',manager.csrf.encode())
            self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8');self.send_header('Cache-Control','no-store')
            self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
        def do_POST(self):
            origin=self.headers.get('Origin');expected='http://'+self.headers.get('Host','')
            if not self.local() or origin not in (None,expected) or not hmac.compare_digest(self.headers.get('X-Mercy-CSRF',''),manager.csrf):self.send({'error':'Request rejected'},403);return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=6000:raise ValueError('Invalid request size')
                data=json.loads(self.rfile.read(size))
                if self.path=='/api/runs':self.send(manager.start(data),202);return
                match=re.fullmatch(r'/api/runs/([a-f0-9]{10})/stop',self.path)
                if match and match[1] in manager.runs:
                    manager.stop(manager.runs[match[1]]);self.send({'stopping':True});return
                self.send({'error':'Not found'},404)
            except (ValueError,TypeError) as exc:self.send({'error':str(exc) if isinstance(exc,ValueError) else 'Invalid run options'},400)
            except Exception:self.send({'error':'Unable to configure this run'},500)
    return Handler


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8787);args=parser.parse_args()
    manager=Manager();server=ThreadingHTTPServer(('127.0.0.1',args.port),handler(manager))
    print('Mercy House story viewer: http://localhost:'+str(args.port),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        for run in manager.runs.values():
            if not run.closed:manager.stop(run)
        server.server_close()


if __name__=='__main__':main()
