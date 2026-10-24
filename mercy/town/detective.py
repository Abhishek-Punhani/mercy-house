import json
import os
import time
import urllib.request
from .tools import schemas
from .io import append_log, write_json, trim

def run_detective(world,folder,steps=40,selector_checkpoint=None):
    selector_checkpoint=selector_checkpoint or os.getenv('SELECTOR_CHECKPOINT')
    if selector_checkpoint:
        from mercy.rl.live import run_selected_detective
        return run_selected_detective(world,folder,selector_checkpoint,steps)
    initial=world.opening()
    system='You are Inspector Arun Mehra in November 1900. Act through the available tools. You can observe, travel, question people, delegate searches and keep records. Your personal history is your own remembered life, not proof about present events. You have at most 40 replies. Submit your account when ready.'
    messages=[{'role':'system','content':system},{'role':'user','content':json.dumps(initial,ensure_ascii=False)}]
    model=os.getenv('MODEL','gpt-6-luna');key=os.getenv('API_KEY','');base=os.getenv('BASE_URL','').rstrip('/')
    url=base+('/chat/completions' if base.endswith('/v1') else '/v1/chat/completions')
    start=time.monotonic();reason='step_cap'
    for step in range(1,steps+1):
        if time.monotonic()-start>600:reason='time_cap';break
        trim(messages);sent=json.loads(json.dumps(messages))
        req=urllib.request.Request(url,data=json.dumps({'model':model,'messages':messages,'tools':schemas(),'max_tokens':3500}).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=min(60,600-(time.monotonic()-start))) as response:raw=json.load(response)
            reply=raw['choices'][0]['message'];calls=reply.get('tool_calls') or []
            clean=[{'id':c['id'],'type':'function','function':c['function']} for c in calls]
            messages.append({'role':'assistant','content':reply.get('content'),**({'tool_calls':clean} if clean else {})})
            results=[];actions=[]
            if not calls:messages.append({'role':'user','content':'No world action was taken. Use a tool when ready.'})
            for i,call in enumerate(calls):
                try:
                    args=json.loads(call['function']['arguments']);name=call['function']['name']
                    actions.append({'tool':name,'args':args})
                    result=world.step(name,args) if i<10 else {'error':'At most ten calls per reply'}
                except (ValueError,TypeError,KeyError):result={'error':'Malformed tool call'}
                results.append(result)
                messages.append({'role':'tool','tool_call_id':call['id'],'content':json.dumps(result,ensure_ascii=False)})
            # The public trace records only what the detective actually received.
            append_log(folder/'detective.jsonl',{'step':step,'model_input':sent,'model_output':{'role':'assistant','content':reply.get('content'),'tool_calls':clean},'actions':actions,'results':results,'usage':raw.get('usage'),'state_hash':world.state_hash()})
            if hasattr(world,'export_private'):write_json(folder/'private-world.json',world.export_private())
            print(json.dumps({'detective_step':step,'actions':[a['tool'] for a in actions],'finished':world.ended}),flush=True)
            if world.ended:reason='submitted';break
        except Exception as exc:
            reason='crash';append_log(folder/'detective.jsonl',{'step':step,'error':type(exc).__name__});break
    summary={'reason':reason,'result':world.result,'minutes':world.clock,'seconds':round(time.monotonic()-start,2)}
    write_json(folder/'summary.json',summary)
    return summary

