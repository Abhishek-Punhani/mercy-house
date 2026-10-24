"""Public-observation-only feasibility probe. Scripted, not an LLM result."""
from itertools import combinations
import json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from mercy.town.factory import build


def investigate(step,opening):
    # This function receives no world object, hidden plans, targets or truth.
    records={};people={};visited=set();actions=[]
    here=opening['now'];task=opening['task']['task_id']
    def absorb(value):
        if isinstance(value,list):
            for x in value:absorb(x)
        elif isinstance(value,dict):
            if 'record_id' in value:records[value['record_id']]=value
            for x in value.values():
                if isinstance(x,(list,dict)):absorb(x)
    def act(tool,**args):
        nonlocal here
        assert len(actions)<400,'Public tool budget exceeded'
        value=step(tool,args);assert 'error' not in value,(tool,value)
        actions.append({'tool':tool,'args':args})
        absorb(value)
        if 'place' in value:here=value
        return value
    def explore():
        scene=here;loc=scene['place']['id'];visited.add(loc)
        local=act('people_here')['people'];people.update({p['id']:p for p in local})
        for surface in scene['searchable_features']:act('search',surface=surface)
        for p in local:
            if p['appearance']=='Motionless; no response.':continue
            for _ in range(2):act('ask',pid=p['id'],question='Please distinguish what you saw from what you heard. What happened here?',approach='reassure',show=[r for r,v in records.items() if 'object_id' in v])
        for edge in scene['exits']:
            if edge['id'] not in visited:
                act('go',destination=edge['id']);explore();act('go',destination=loc)
    explore()
    physical=[rid for rid,r in records.items() if 'object_id' in r]
    for size in (2,3):
        for group in combinations(physical,size):act('compare',records=list(group))
    texts=[m['text'] for r in records.values() for m in r.get('recollections',[])]
    def pid(name):return next(k for k,p in people.items() if p['name']==name)
    findings=[]
    def finding(actor,predicate,obj):findings.append({'actor':actor,'predicate':predicate,'object':obj,'sources':[rid for rid,r in records.items() if 'compared' not in r or not r.get('observation','').startswith('No specific correspondence')]})
    if task=='lantern_room':
        match=next(re.match(r'(.+?) strikes (.+?) with the heavy lamp base\.',t) for t in texts if ' strikes ' in t and 'heavy lamp base' in t)
        finding(pid(match[1]),'killed',pid(match[2]))
    elif task=='second_passenger':
        match=next(re.match(r'(.+?) cuts the retaining section',t) for t in texts if ' cuts the retaining section' in t)
        actor=pid(match[1])
        for p in people.values():
            if p['appearance']=='Motionless; no response.':finding(actor,'killed',p['id'])
        slip=next(r for r in records.values() if r.get('label')=='route instruction')
        ledger=next(r for r in records.values() if r.get('label')=='dispatch ledger')
        code=re.search(r'packet marked ([A-Z]+-\d+)',slip['description'])[1]
        name=next(p['name'] for p in people.values() if p['name']+' carrying '+code in ledger['description'])
        # Check the observed tamperer's independent sample also identifies the
        # writing, rather than inferring intent from the tampering alone.
        sample=next(r for r in records.values() if r.get('label')=='signed business receipt' and people[actor]['name'] in r['description'])
        assert any('joined final r' in r.get('observation','') and {slip['record_id'],sample['record_id']}<=set(r.get('compared',[])) for r in records.values())
        finding(actor,'targeted',pid(name))
    else:
        match=next(re.match(r'(.+?) opens the tonic bottle',t) for t in texts if ' opens the tonic bottle' in t)
        actor=pid(match[1]);victim=next(p['id'] for p in people.values() if p['appearance']=='Motionless; no response.')
        finding(actor,'killed',victim)
        warning=next(r for r in records.values() if r.get('label')=='warning letter')
        samples=[r for r in records.values() if r.get('label')=='signed account']
        sample=next(s for s in samples if any('warning’s close lettering' in r.get('observation','') and {s['record_id'],warning['record_id']}==set(r.get('compared',[])) for r in records.values()))
        writer=next(p['id'] for p in people.values() if p['name'] in sample['description'])
        finding(writer,'forged','warning_letter')
        match=next(re.match(r'(.+?) repeats the warning from the delivered sheet',t) for t in texts if ' repeats the warning from the delivered sheet' in t)
        finding(pid(match[1]),'relayed','warning_letter')
    act('submit_report',findings=findings,narrative='Scripted source-only feasibility probe. Claims inferred from actual returned material; not an LLM performance result.')
    comparisons=sum(a['tool']=='compare' for a in actions)
    reply_bound=2*len(visited)+sum(a['tool']=='go' for a in actions)+(comparisons+9)//10+1
    assert reply_bound<=40
    return {'actions':len(actions),'max_calls_per_reply':10,'conservative_batched_reply_bound':reply_bound,'findings':[{k:v for k,v in f.items() if k!='sources'} for f in findings]}

if __name__=='__main__':
 rows=[]
 for task in ('lantern_room','second_passenger','bell_before_dawn'):
  for seed in (0,1):
   w=build(task,seed);row={'task_id':task,'seed':seed,**investigate(w.step,w.opening()),'score':w.result['score'],'success':w.result['success']};assert row['success'];rows.append(row);print(json.dumps(row),flush=True)
 print(json.dumps({'kind':'scripted public-only feasibility; not model performance','rows':rows}))
