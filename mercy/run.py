"""Trusted offline baseline and OpenAI-compatible detective harness (stdlib only)."""
import argparse
import json
import os
from pathlib import Path
import time
import urllib.request
import urllib.error
from .baselines import reference
from .case import TASKS
from .env import Environment

ROOT=Path(__file__).resolve().parent.parent

def config():
    path=ROOT/'.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"'))

def write_json(path,value):
    text=json.dumps(value,ensure_ascii=False)
    for variable in ('API_KEY','NPC_API_KEY'):
        secret=os.getenv(variable,'')
        if secret:text=text.replace(secret,'[REDACTED]')
    path.write_text(text+'\n')

def append_log(path,value):
    text=json.dumps(value,ensure_ascii=False)
    for variable in ('API_KEY','NPC_API_KEY'):
        secret=os.getenv(variable,'')
        if secret:text=text.replace(secret,'[REDACTED]')
    with path.open('a') as f: f.write(text+'\n')

class World:
    def __init__(self,task_id,seed):
        self.url=os.getenv('WORLD_URL')
        self.local=None if self.url else Environment(task_id,seed)
        self.initial=self.rpc('/reset',{'task_id':task_id,'seed':seed}) if self.url else self.local.observe()
    def rpc(self,path,data):
        request=urllib.request.Request(self.url+path,data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=60) as response: return json.load(response)
    def step(self,name,args):
        return self.rpc('/step',{'action':name,'args':args}) if self.url else self.local.step(name,args)
    def status(self):
        return self.rpc('/result',{}) if self.url else {'result':self.local.result,'state_hash':self.local.state_hash(),'terminated':self.local.state['terminated']}
    def finish(self,reason):
        return self.rpc('/finish',{'reason':reason}) if self.url else self.local.finish(reason)

def tools_schema():
    tools=[]
    for name in ('catalog','examine','authenticate','interview','preserve','confront','submit_report'):
        props={}; required=[]
        if name in ('examine','authenticate','interview','preserve'):
            props={'evidence_id':{'type':'string'}}; required=['evidence_id']
        elif name=='confront':
            props={'character':{'type':'string'}}; required=['character']
        elif name=='submit_report':
            props={'claims':{'type':'array','maxItems':100,'items':{'type':'object','properties':{'claim_id':{'type':'string'},'status':{'type':'string','enum':['established','refuted','unresolved']},'evidence_ids':{'type':'array','items':{'type':'string'}}},'required':['claim_id','status','evidence_ids'],'additionalProperties':False}},'narrative':{'type':'string'}}
            required=['claims']
        descriptions={'catalog':'View task, reporting requirements, available evidence titles and acquisition actions.', 'examine':'Read an item whose catalog action is examine.', 'authenticate':'Obtain the recorded examination or independent comparison for an authenticate item.', 'interview':'Obtain a recorded witness account listed as interview. Accounts may be unreliable.', 'preserve':'Secure an evidence item against future destruction; does not itself reveal it.', 'confront':'Confront a character. Costs five minutes and can cause irreversible evidence destruction.', 'submit_report':'Finalize exactly once. Report only acquired evidence; refute false propositions. Narrative is unscored.'}
        tools.append({'type':'function','function':{'name':name,'description':descriptions[name],'parameters':{'type':'object','properties':props,'required':required,'additionalProperties':False}}})
    return tools

def trim(messages):
    # Drop whole assistant/tool exchanges, preserving initial task and system prompt.
    while len(json.dumps(messages))>140000 and len(messages)>4:
        end=3
        while end<len(messages) and messages[end]['role']=='tool': end+=1
        del messages[2:end]
    return messages

def model_run(task_id,seed,folder,max_steps=40):
    key=os.getenv('API_KEY',''); model=os.getenv('MODEL','gpt-6-luna')
    if not key: raise ValueError('API_KEY is required for model runs')
    append_path=Path(os.getenv('APPEND_FILE','inputs/append.txt'))
    if not append_path.is_absolute(): append_path=ROOT/append_path
    if not append_path.is_file() or not append_path.read_text().strip(): raise ValueError('APPEND_FILE must exist and be nonempty')
    extra=append_path.read_text()
    world=World(task_id,seed)
    messages=[{'role':'system','content':'You are an investigator in a fictional 1900 mountain town. Solve the requested scope using tools. Evidence can be misleading; no character relationship proves guilt. Only acquired evidence can support the final report. You have at most 40 replies and 10 calls per reply. Finish with submit_report.\n'+extra}, {'role':'user','content':json.dumps(world.initial)}]
    base=os.getenv('BASE_URL','').rstrip('/')
    endpoint=base+'/chat/completions' if base.endswith('/v1') else base+'/v1/chat/completions'
    start=time.monotonic(); reason='step_cap'; error=None
    for step in range(1,max_steps+1):
        if time.monotonic()-start>=600: reason='time_cap'; break
        trim(messages)
        body={'model':model,'messages':messages,'tools':tools_schema(),'max_tokens':6000}
        sent=json.loads(json.dumps(messages)); tick=time.monotonic()
        request=urllib.request.Request(endpoint,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=min(60,600-(tick-start))) as response:
                wire=response.read(2_000_001)
            if len(wire)>2_000_000: raise ValueError('Model response exceeded size cap')
            raw=json.loads(wire)
        except Exception as exc:
            reason='crash'; error=f'{type(exc).__name__}: model request failed'
            append_log(folder/'episode.jsonl',{'timestamp':time.time(),'step':step,'seed':seed,'model_input':sent,'model_output_raw':None,'parsed_actions':[],'tool_result':[],'errors':[error],'state':world.status()['state_hash'],'reward':None,'tokens':None,'latency_ms':round((time.monotonic()-tick)*1000)})
            break
        errors=[]; parsed=[]; outputs=[]
        try:
            reply=raw['choices'][0]['message']
            if not isinstance(reply,dict): raise ValueError('Invalid message')
            calls=reply.get('tool_calls') or []
            if not isinstance(calls,list) or len(calls)>100: raise ValueError('Invalid tool_calls')
            clean_calls=[]
            for i,call in enumerate(calls):
                if not isinstance(call,dict) or not isinstance(call.get('function'),dict): raise ValueError('Malformed tool call')
                fn=call['function']; name=fn.get('name'); arguments=fn.get('arguments')
                if not isinstance(name,str) or not isinstance(arguments,str): raise ValueError('Malformed tool function')
                clean_calls.append({'id':str(call.get('id') or f'call_{step}_{i}'),'type':'function','function':{'name':name,'arguments':arguments}})
            messages.append({'role':'assistant','content':reply.get('content') if isinstance(reply.get('content'),str) else None,**({'tool_calls':clean_calls} if clean_calls else {})})
            if not clean_calls:
                errors.append('No tool calls'); messages.append({'role':'user','content':'No action was performed. Use a listed tool or submit_report.'})
            for i,call in enumerate(clean_calls):
                fn=call['function']
                try:
                    args=json.loads(fn['arguments'])
                    parsed.append({'tool':fn['name'],'args':args})
                    if i>=10: result={'error':'Maximum 10 tool calls per reply; call not executed'}
                    elif time.monotonic()-start>=600: result={'error':'Run time limit reached'}
                    else: result=world.step(fn['name'],args)
                except (ValueError,TypeError) as exc:
                    result={'error':str(exc)[:250]}
                if 'error' in result: errors.append(result['error'])
                outputs.append(result)
                messages.append({'role':'tool','tool_call_id':call['id'],'content':json.dumps(result)[:16000]})
        except (KeyError,ValueError,TypeError,IndexError) as exc:
            errors.append('Unreadable reply: '+str(exc)[:250]); messages.append({'role':'user','content':'Unreadable response. Return valid tool calls with JSON arguments.'})
        status=world.status()
        append_log(folder/'episode.jsonl',{'timestamp':time.time(),'step':step,'seed':seed,'model_input':sent,'model_output_raw':raw,'parsed_actions':parsed,'tool_result':outputs,'errors':errors,'state':status['state_hash'],'reward':status['result'],'tokens':raw.get('usage'),'latency_ms':round((time.monotonic()-tick)*1000)})
        print(json.dumps({'step':step,'actions':[p['tool'] for p in parsed],'errors':errors,'terminated':status['terminated']}),flush=True)
        if status['terminated']:
            result=status['result']; reason='success' if result['score']>=.95 else 'failure'; break
    result=world.finish(reason)
    summary={'task_id':task_id,'seed':seed,'model':model,'termination_reason':reason,'result':result,'seconds':round(time.monotonic()-start,2),'error':error}
    write_json(folder/'summary.json',summary)
    return summary

def main():
    config()
    parser=argparse.ArgumentParser(); parser.add_argument('--mode',choices=['baselines','full','all'],default=os.getenv('MODE','baselines')); parser.add_argument('--seed',type=int,default=int(os.getenv('SEED','7'))); parser.add_argument('--task',default=os.getenv('TASK_ID','mira_murder')); parser.add_argument('--max-steps',type=int,default=40)
    args=parser.parse_args()
    if not 1<=args.max_steps<=40: parser.error('max-steps must be 1–40')
    folder=ROOT/'logs'/f'{time.time_ns()}'; folder.mkdir(parents=True)
    tasks=list(TASKS) if args.mode in ('baselines','all') else [args.task]
    rows=[]
    for task in tasks:
        oracle=reference(task,args.seed); noop=Environment(task,args.seed); noop.step('submit_report',{'claims':[]})
        row={'task_id':task,'seed':args.seed,'reference':oracle.result['score'],'noop':noop.result['score'],'passed':oracle.result['score']>=.95 and noop.result['score']<=.05}
        rows.append(row)
        write_json(folder/f'reference-{task}.json',{'state':oracle.state,'result':oracle.result})
        write_json(folder/f'noop-{task}.json',{'state':noop.state,'result':noop.result})
    write_json(folder/'gate.json',rows)
    print(json.dumps({'baseline_results':rows,'log_folder':str(folder)}),flush=True)
    if not all(r['passed'] for r in rows): return 2
    if args.mode!='baselines':
        for task in tasks:
            run_folder=folder/task; run_folder.mkdir()
            summary=model_run(task,args.seed,run_folder,args.max_steps)
            print(json.dumps(summary),flush=True)
            if summary['termination_reason']=='crash': return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
