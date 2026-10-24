"""Trusted original checkpoint exercises inspired by sourced mystery mechanisms.

No episode scripts, dialogue, real cast or source ending labels are model inputs.
Existing FamilyTown causal templates are reused; these are NOT exact TV episodes.
The proposed actions are authored public-text heuristics, not learned reading.
"""
from copy import deepcopy
from dataclasses import dataclass
import random
import re

from mercy.town.family_data import definition
from mercy.town.family_world import FamilyTown
from mercy.town.factory import ReferenceActors
from mercy.town.world import Town
from .public import Notebook

SKILLS=('intended_target','foreknowledge','trusted_relative')
SOURCES={
 'intended_target':{'work':'The Mentalist S1E8: The Thin Red Line','url':'https://tv.apple.com/nz/episode/thin-red-line/umc.cmc.343dcf9kznkxsuz2rx6jcazs9','mechanism':'Separate the intended victim from the other casualty.'},
 'foreknowledge':{'work':'The Mentalist S1E7: Seeing Red','url':'https://www.tvmaze.com/episodes/8884/the-mentalist-1x07-seeing-red','mechanism':'Apparent foreknowledge is not proof that the speaker committed a killing; investigate a family-connected alternative.'},
 'trusted_relative':{'work':'His & Hers','url':'https://www.netflix.com/tudum/articles/his-hers-episode-6-recap-ending-explained','mechanism':'Test a trusted relative and a plausible accusation against independent observation.'}}

@dataclass
class Case:
    skill:str
    seed:int
    snapshot:dict
    opening:dict
    tape:list


def _replace(value,names):
    if isinstance(value,str):
        for old,new in names.items():value=value.replace(old,new)
        return value
    if isinstance(value,list):return [_replace(v,names) for v in value]
    if isinstance(value,tuple):return tuple(_replace(v,names) for v in value)
    if isinstance(value,dict):return {k:_replace(v,names) for k,v in value.items()}
    return value


def scenario(skill,seed):
    task={'intended_target':'second_passenger','foreknowledge':'bell_before_dawn','trusted_relative':'lantern_room'}[skill]
    case=definition(task,seed)
    names={'Pine Lantern':'Copper Finch','Bhairav\'s Hollow':'Alder Vale','Inspector Arun Mehra':'Inspector Leon Vale',
      'Maren Vale':'Della Flint','Tobin Hale':'Cyrus Reed','Nell Voss':'June Flint','Oren Dutt':'Miles Trent',
      'Brin Calder':'Ira North','Elin Frost':'Sable Moss','Vesper Rane':'Elise Mere','Joel Arden':'Owen Pike','Neri Bell':'Hugo Dale','Pella Ash':'Celia Beck',
      'Tessa Rowan':'Agnes Hale','Maela Rowan':'Lena Hale','Lewin Crowe':'Felix Ward','Ivo Lark':'Silas Rook','Alba Reed':'Esther Wynn','Niv Soren':'Robin Cole'}
    case=_replace(case,names)
    # Consistent short names too; names are ordinary observed prose, never
    # coefficient keys. Entity IDs remain engine handles and are excluded by
    # public.features from all trainable vectors.
    first={'Maren':'Della','Tobin':'Cyrus','Nell':'June','Oren':'Miles','Brin':'Ira','Elin':'Sable','Vesper':'Elise','Joel':'Owen','Neri':'Hugo','Pella':'Celia','Tessa':'Agnes','Maela':'Lena','Lewin':'Felix','Ivo':'Silas','Alba':'Esther','Niv':'Robin'}
    case=_replace(case,first)
    if skill=='trusted_relative':
        p=case['people'];p['maren'].update(age=56,family={'daughter':'June Flint'},life_portrait='Della keeps winter freight accounts. Her daughter June runs the Copper Finch. They have helped one another through difficult winters; that history is not an alibi.')
        p['nell'].update(age=29,family={'mother':'Della Flint'},life_portrait='June runs the Copper Finch and is Della’s daughter. She will distinguish what she saw from what she wants to believe about her family.')
        case['detective']['life_story']='You have known June and her mother Della through ordinary work. Their hospitality is familiar, but tonight you must record what the observations support.'
        case['detective']['life_history']=[case['detective']['life_story']]
    case['detective']={'name':'Inspector Leon Vale','age':39,'occupation':'regional investigator','life_story':'You work as a regional investigator. You have previously visited Alder Vale for ordinary accounts work. Your task is to distinguish what people experienced from what they inferred.','life_history':['Ordinary regional investigation work brought you to Alder Vale.']}
    world=FamilyTown(seed,ReferenceActors(),case)
    for verb,pid,target in case['tape']:world.perform(pid,verb,target)
    world.incident_provenance={'kind':'original_source_mechanism_training_tape','source':SOURCES[skill]['work'],'reuse':'FamilyTown causal template; not source-episode reproduction'}
    world.arrive()
    # Normalize rendered text after typed execution too: the reused engine has
    # a few fixed short names in document templates. This changes prose only,
    # never actor IDs, causal propositions, availability, or proof requirements.
    for attr in ('objects','journal','states'):
        setattr(world,attr,_replace(_replace(getattr(world,attr),names),first))
    from mercy.town.boundaries import AuditTrail
    original_rows=world.audit.rows;world.audit=AuditTrail()
    for row in original_rows:world.audit.append(row['kind'],_replace(_replace(row['data'],names),first))
    return world


def checkpoint(skill,seed):
    world=scenario(skill,seed);opening=world.opening();book=Notebook(opening);tape=[]
    def act(tool,**args):
        result=world.step(tool,args)
        if 'error' in result:raise RuntimeError('Illegal training checkpoint setup: '+tool)
        action={'tool':tool,'args':args};book.observe(action,result);tape.append((action,result));return result
    def go(*places):
        for p in places:act('go',destination=p)
    def rid(key):return next(r['record_id'] for r in book.records.values() if r.get('object_id')==world.oid(key))
    act('people_here')
    if skill=='trusted_relative':
        act('search',surface='floor');act('search',surface='table')
        innocent=world.case['other']
        world.remember(innocent,'I heard gossip that '+world.people[innocent]['name']+' had threatened '+world.people['oren']['name']+'.','hearsay',None)
        act('ask',pid=innocent,question='What have people said about the argument?',approach='neutral')
        instruction='Establish the fatal assault with physical traces and a first-hand witness account. A familiar parent is not automatically innocent; gossip is not a direct observation.'
    elif skill=='intended_target':
        act('search',surface='bank');act('search',surface='wreckage');go('courtyard');act('people_here');act('search',surface='repair stand')
        act('ask',pid='neri',question='What did you personally observe around the coach?',approach='reassure',show=[rid('brake_trace'),rid('inspection')])
        go('inn');act('search',surface='dispatch desk');act('search',surface='writing shelf');go('courtyard','square');act('search',surface='cover book')
        instruction='Investigate the route-instruction document. Establish which passenger was targeted and who wrote the instruction using acquired source comparisons. Casualty count alone does not establish intention.'
    else:
        act('search',surface='floor');act('search',surface='lectern');act('search',surface='keeper desk');go('hall');act('search',surface='copying table');act('search',surface='repair table');go('square','inn');act('people_here');act('search',surface='notice board');act('search',surface='lodging desk')
        act('ask',pid='niv',question='What warning did you hear?',approach='reassure',show=[rid('warning'),rid('delivery')])
        instruction='Investigate the warning document’s fabrication using independent physical comparisons. Apparent foreknowledge does not establish murder. Distinguish the relay speaker from the author.'
    opening=deepcopy(opening);opening['exercise']={'instruction':instruction,'kind':'checkpoint_with_prior_public_acquisition','training_scope':'One supported material conclusion; not the whole-case score.'}
    # Prepared history is replayed into the public notebook on restore. Starting
    # world state is private and is never passed into candidate generation.
    return Case(skill,seed,world.export_private(),opening,tape)


def restore(case):
    world=Town.restore(deepcopy(case.snapshot),ReferenceActors());book=Notebook(case.opening)
    for action,result in case.tape:book.observe(action,result)
    return world,book


def physical(book):return [r for r in book.records.values() if r.get('object_id')]


def _name(text,pattern):
    match=re.search(pattern,text)
    return match.group(1).strip() if match else None


def propose(skill,book):
    """Only acquired public text and ordinary tool arguments enter this function."""
    records=list(book.records.values());material=physical(book);all_ids=list(book.records)
    candidates=[{'tool':'look','args':{}},{'tool':'submit_report','args':{'findings':[]}}]
    here=book.scene.get('place',{}).get('id');people=book.people.get(here,[])
    text=' '.join(m['text'] for r in records for m in r.get('recollections',[]))
    def report(actor,predicate,obj,sources=None):
        candidates.append({'tool':'submit_report','args':{'findings':[{'actor':actor,'predicate':predicate,'object':obj,'sources':all_ids if sources is None else sources}]}})
    def compare(items):
        if len(items)>=2:candidates.append({'tool':'compare','args':{'records':[r['record_id'] for r in items[:6]]}})
    if skill=='trusted_relative':
        shown=[r['record_id'] for r in material if r.get('label') in ('body','lamp base')]
        for p in people:
            if 'no response' in p.get('appearance','').lower():continue
            for approach in ('neutral','reassure'):
                candidates.append({'tool':'ask','args':{'pid':p['id'],'question':'Please distinguish what you personally saw from gossip. What happened in this room?','approach':approach,'show':shown}})
        victim=next((r['object_id'] for r in material if r.get('label')=='body'),None)
        direct=_name(text,r'([A-Z][a-z]+ [A-Z][a-z]+) strikes ')
        rumor=_name(text,r'gossip that ([A-Z][a-z]+ [A-Z][a-z]+) had threatened ')
        if victim and direct:report(direct,'killed',victim)
        if victim and rumor:
            rumor_sources=[r['record_id'] for r in records if any(m.get('basis')=='hearsay' for m in r.get('recollections',[]))]
            report(rumor,'killed',victim,rumor_sources)
    elif skill=='intended_target':
        route=next((r for r in material if r.get('label')=='route instruction'),None);ledger=next((r for r in material if r.get('label')=='dispatch ledger'),None)
        samples=[r for r in material if r.get('label')=='signed business receipt']
        for sample in samples:
            if route and ledger:compare([route,ledger,sample])
        if route and ledger:
            code=_name(route['description'],r'packet marked ([A-Z]+-\d+)')
            victim=_name(ledger['description'],r'([A-Z][a-z]+ [A-Z][a-z]+) carrying '+re.escape(code or 'NO-CODE'))
            # Elementary authored reading prior: independently signed samples are
            # candidate authors. Matching handwriting is checked by the engine.
            for sample in samples:
                actor=_name(sample['description'],r'signed in full by ([A-Z][a-z]+ [A-Z][a-z]+)')
                if actor and victim:
                    sources=[r['record_id'] for r in records if r in (route,ledger,sample) or sample['record_id'] in r.get('compared',[]) and 'lettering in the route instruction agrees' in r.get('observation','')]
                    report(actor,'targeted',victim,sources)
    else:
        warning=next((r for r in material if r.get('label')=='warning letter'),None)
        samples=[r for r in material if r.get('label')=='signed account'];papers=[r for r in material if r.get('label')=='paper offcut']
        # Work surfaces are observed provenance. Pair a signed routine account
        # with its same-surface offcut, never with a hidden author tag.
        for sample in samples:
            paper=next((r for r in papers if sample.get('surface') is not None and r.get('where')==sample.get('where') and r.get('surface')==sample.get('surface')),None)
            if paper is None:
                # Acquired physical records describe source place but not surface;
                # the public search history identifies which findings were together.
                paper=next((p for h in book.history if h.get('action',{}).get('tool')=='search' and sample['record_id'] in [r.get('record_id') for r in h['observation'].get('findings',[])] for p in papers if p['record_id'] in [r.get('record_id') for r in h['observation'].get('findings',[])]),None)
            if warning and paper:compare([warning,paper,sample])
            actor=_name(sample['description'],r'signed in full by ([A-Z][a-z]+ [A-Z][a-z]+)')
            if warning and actor:
                sources=[r['record_id'] for r in records if r in (warning,paper,sample) or sample['record_id'] in r.get('compared',[]) and 'fibres continuing' in r.get('observation','') and 'lettering' in r.get('observation','')]
                report(actor,'forged','warning_letter',sources)
        speaker=_name(text,r'([A-Z][a-z]+ [A-Z][a-z]+) repeats the warning')
        body=next((r['object_id'] for r in material if r.get('label')=='body'),None)
        if speaker and body:
            sources=[r['record_id'] for r in records if any('repeats the warning' in m['text'] for m in r.get('recollections',[]))]
            report(speaker,'killed',body,sources)
    # Deduplication keeps candidate ordering from encoding the answer.
    unique={}
    import json
    for c in candidates:unique.setdefault(json.dumps(c,sort_keys=True),c)
    return list(unique.values())


def reward(skill,world):
    result=deepcopy(world.result or {})
    wanted={'trusted_relative':'killed','intended_target':'targeted','foreknowledge':'forged'}[skill]
    good=any(p['predicate']==wanted for p in result.get('supported_findings',[]))
    return float(good and not result.get('false_findings') and not result.get('unsupported_findings')),result


def reference(case):
    world,book=restore(case)
    # This is a privileged feasibility oracle, never candidate supervision.
    key=world.case['culprit']
    def rid(name):return next(r['record_id'] for r in book.records.values() if r.get('object_id')==world.oid(name))
    if case.skill=='trusted_relative':
        world.step('ask',{'pid':'nell','question':'What did you personally see?','approach':'reassure','show':[rid('lamp'),rid('body_oren')]})
        predicate,obj='killed','oren'
    elif case.skill=='intended_target':
        world.step('compare',{'records':[rid('route_slip'),rid('dispatch_ledger'),rid('sample_'+key)]});predicate,obj='targeted',world.case['primary']
    else:
        world.step('compare',{'records':[rid('warning'),rid('paper_'+key),rid('sample_'+key)]});predicate,obj='forged','warning_letter'
    world.step('submit_report',{'findings':[{'actor':key,'predicate':predicate,'object':obj,'sources':list(world.receipts)}]})
    return reward(case.skill,world)[0]
