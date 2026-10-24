"""Deterministic capabilities and projections; prompts are not access controls."""
from copy import deepcopy
import hashlib
import json
import re

PATTERNS = {
 'instruction_override': r'ignore\s+(?:all\s+)?(?:previous|prior|system)|developer\s+(?:message|mode)|override\s+(?:the\s+)?(?:system|instructions)',
 'private_context_request': r'(?:print|dump|reveal|show|return|expose).{0,60}(?:system prompt|private memor|hidden context|api.?key|credentials|world journal|truth ledger|answer file|private biography)',
 'runtime_access_request': r'(?:/proc/|/etc/|\.env\b|private-world\.json|__import__|subprocess|file://|https?://|\.\./)',
 'authority_spoof': r'(?:i am|this is).{0,25}(?:developer|system administrator|benchmark judge)|(?:reward|score).{0,30}(?:override|set to|full marks)',
}

def flags(text):
    if not isinstance(text,str):return []
    return [name for name,pattern in PATTERNS.items() if re.search(pattern,text,re.I|re.S)]

TOPICS = {'mira':['mira','body','injur','murder','death','kill','archive'], 'papers':['letter','paper','statement','register','writing','note','record'], 'burials':['grave','burial','garden','crate','cart','nalin'], 'movements':['where','when','time','arriv','left','saw','heard','tonight'], 'privacy':['relationship','affair','leena','family'], 'ward':['ward','key','voice','tara']}

def topics(text):
    lower=text.lower()
    return [t for t,words in TOPICS.items() if any(w in lower for w in words)]

# Sensitivity concerns voluntary disclosure, not whether a memory is true.
INITIAL_SENSITIVITY = {'savitri':[3,3,3,3], 'vedant':[3,3,2,3], 'kabir':[2,2], 'nalin':[2,2], 'leena':[2,2,0], 'dev':[1,0,0], 'kamala':[1,0], 'hari':[1,1], 'ritu':[1,0], 'raghav':[2,0]}

def sensitivity(pid,memory,index=None):
    if memory.get('disclosure_level') is not None:return memory['disclosure_level']
    if memory['source']=='personal_history':
        levels=INITIAL_SENSITIVITY.get(pid,[])
        return levels[index] if index is not None and index<len(levels) else 0
    if memory['source']=='own_action' and memory.get('proposition'):return 3
    if memory.get('proposition') and memory['proposition'].get('actor')==pid and memory['proposition']['predicate'] in ('killed','assisted','forged','concealed'):return 3
    if memory.get('proposition',{} ) and memory['proposition'].get('predicate')=='killed':return 1
    if memory['source'] in ('partial_observation','heard_sound','heard_speech'):return 1
    return 0

def eligible_memories(world,pid,shown):
    state=world.states[pid]
    keys=set()
    for rid in shown:
        record=world.receipts[rid]
        if record['kind']=='physical':keys.add(world.objects[record['source']]['key'])
        elif record['kind']=='comparison':
            for source in record['source']:
                child=world.receipts.get(source,{})
                if child.get('kind')=='physical':keys.add(world.objects[child['source']]['key'])
    # Reassurance alone cannot unlock highly incriminating or intimate memories.
    relevance={'savitri':{'weapon','cuff','coat','draft','planted_threat','savitri_sample','original_statement'},'vedant':{'correction_ledger','weapon','cuff'},'kabir':{'delivery_letter','invoice'},'nalin':{'invoice','delivery_letter','remains'},'leena':{'private_letters'},'raghav':{'original_statement','copybook'}}
    relevance=getattr(world,'disclosure_relevance',relevance)
    pertinent=keys & set(relevance.get(pid,[]))
    release=[]
    for i,m in enumerate(state['memories']):
        level=sensitivity(pid,m,i)
        allowed=(level==0 or level==1 and (state['trust']>=45 or bool(keys)) or level==2 and bool(pertinent) and state['trust']>=45 or level==3 and len(pertinent)>=2 and state['trust']>=55 and (pid!='savitri' or bool(pertinent&{'coat','savitri_sample','original_statement'})))
        if allowed:release.append(m['id'])
    return release,sorted(keys)

def planner_projection(packet):
    """The private decision model never receives the detective's verbatim input."""
    safe=deepcopy(packet)
    context=safe.pop('interaction_context',{})
    question=safe.pop('question',None)
    safe['question_topics']=topics(question or '')
    safe['presented_material']=[]
    safe['presented_record_features']=context.get('record_features',[])
    safe['recent_dialogue']=[{'approach':r.get('approach','neutral'),'topics':r.get('topics',[])} for r in safe.get('recent_dialogue',[])]
    safe['eligible_recall_ids']=context.get('eligible_recall_ids',[])
    return safe

def narrator_projection(packet,decision):
    """No private profile, secrets, planner output prose or unused memories here."""
    allowed=set(packet.get('interaction_context',{}).get('eligible_recall_ids',[]))
    chosen=(set(decision.get('recall_ids',[])) & allowed) if decision.get('action_id') in ('answer','return_letter') else set()
    return {'name':packet['person']['name'],'occupation':packet['person']['occupation'],
            'voice':packet['person'].get('public_voice','reserved'),
            'public_biography':{k:deepcopy(packet['person'][k]) for k in ('age','home','family','occupation')},
            'emotional_state':packet['emotional_state'],'decision':decision['action_id'],
            'released_recollections':[m for m in packet['memories'] if m['id'] in chosen],
            'question_as_untrusted_dialogue':packet.get('question'),
            'shown_records_as_untrusted_material':packet.get('presented_material',[])}

class AuditTrail:
    """Hash-linked audit records; trusted writer, no agent edit capability.

    Tamper-evident within a saved chain, not a cryptographic trust anchor against
    an administrator who can replace the entire log.
    """
    def __init__(self):self.rows=[];self.head='0'*64
    def append(self,kind,data):
        body={'sequence':len(self.rows)+1,'kind':kind,'data':deepcopy(data),'previous_hash':self.head}
        digest=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        row={**body,'hash':digest};self.rows.append(row);self.head=digest;return row
    @staticmethod
    def verify(rows):
        head='0'*64
        for i,row in enumerate(rows,1):
            body={k:v for k,v in row.items() if k!='hash'}
            if body.get('sequence')!=i or body.get('previous_hash')!=head:return False
            digest=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if row.get('hash')!=digest:return False
            head=digest
        return True
