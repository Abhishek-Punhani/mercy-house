"""Public-only projection for live viewing and recorded replay.

Never read world snapshots or actor audits. Provider reasoning fields and raw
model requests are deliberately absent from the browser event contract.
"""
from copy import deepcopy
import json


def pick(value, keys):
    return {k:deepcopy(value[k]) for k in keys if k in value} if isinstance(value,dict) else {}


def record(value):
    result=pick(value,('record_id','object_id','label','where','found_by','description','person','question','words','compared','observation','summary','notice','surface','by','reported_objects'))
    if isinstance(value.get('recollections'),list):
        result['recollections']=[pick(m,('text','basis')) for m in value['recollections']]
    if isinstance(value.get('hypotheses'),list):
        result['hypotheses']=[pick(m,('statement','status','sources')) for m in value['hypotheses']]
    return result


def observation(value):
    if not isinstance(value,dict):return {'notice':'No readable observation'}
    result=pick(value,('error','notice','immediately_visible','minutes_since_arrival','searched','by','statement','granted','area','words','secured','record_id','submitted','stdout','stderr','exit_code','timed_out','truncated','preview'))
    if isinstance(value.get('place'),dict):
        result['place']=pick(value['place'],('id','name','description'))
        result['exits']=[pick(x,('id','name')) for x in value.get('exits',[])]
        result['searchable_features']=deepcopy(value.get('searchable_features',[]))
    if isinstance(value.get('people'),list):
        result['people']=[pick(p,('id','name','occupation','appearance')) for p in value['people']]
    for key in ('findings','handed_over','records'):
        if isinstance(value.get(key),list):result[key]=[record(r) for r in value[key] if isinstance(r,dict)]
    for key in ('search_log','custody_record'):
        if isinstance(value.get(key),dict):result[key]=record(value[key])
    if value.get('record_id'):result.update(record(value))
    return result


def opening(value):
    return {'your_life':pick(value.get('your_life',{}),('name','age','occupation','recollections')),
            'now':observation(value.get('now',{})),
            'task':pick(value.get('task',{}),('task_id','name','difficulty','scope','success','limits','briefing')),
            'assignment':value.get('assignment',''),
            'notes':[record(r) for r in value.get('notes',[])]}


def verdict(value):
    return pick(value,('score','success','supported_findings','false_findings','unsupported_findings',
         'unresolved_findings','reward_components','material_events_total','limitations'))


def note_from_reply(row):
    raw=row.get('model_output_parsed') or row.get('model_output_raw')
    if isinstance(raw,str):
        try:raw=json.loads(raw)
        except ValueError:return None
    try:
        words=raw['choices'][0]['message'].get('content')
        return words[:1800] if isinstance(words,str) and words.strip() else None
    except (KeyError,TypeError,IndexError):return None


def reply_event(row):
    return {'type':'reply','reply':row.get('step'), 'note':note_from_reply(row),
            'tokens':row.get('tokens'), 'latency_ms':row.get('latency_ms'),
            'errors':row.get('errors',[])}


def action_event(action, result, reply=None, minutes=None):
    return {'type':'action','reply':reply,'action':pick(action,('tool','args')),
            'observation':observation(result),'minutes':minutes}


def replay(initial, rows, summary, kind='model'):
    events=[{'type':'opening','opening':opening(initial)}]
    for row in rows:
        if kind=='model':events.append(reply_event(row))
        for action,result in zip(row.get('parsed_actions',[]),row.get('tool_result',[])):
            events.append(action_event(action,result,row.get('step')))
    if summary:
        events.append({'type':'finished','termination':summary.get('termination_reason',summary.get('reason','failure')),
            'result':verdict(summary.get('result') or {}),'seconds':summary.get('seconds')})
    return [{**event,'seq':i+1} for i,event in enumerate(events)]
