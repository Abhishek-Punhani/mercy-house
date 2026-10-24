"""Small predeclared paired policy calibration on original case families.

Both arms use ranked API proposals, the same candidate contract and a fixed
grounded character-response bank with normal disclosure gates. This controls NPC
response randomness; it is NOT live-NPC evaluation or a PS competition run.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import time

from mercy.run import config
from mercy.town.factory import build, ReferenceActors
from mercy.town.reference import gates
from mercy.town.io import write_json, append_log
from . import live
from .policy import Selector
from .public import Notebook, features


class FixedResponseBank(ReferenceActors):
    """One frozen voice per memory, shared across both arms' legal disclosures."""
    def __init__(self,bank):self.bank=bank
    def decide(self,pid,packet):
        answer=super().decide(pid,packet)
        if answer['action_id']=='answer':
            allowed=set(packet.get('interaction_context',{}).get('eligible_recall_ids',[]))
            ids=[mid for mid in answer['recall_ids'] if mid in allowed]
            answer['speech']=' '.join(self.bank[pid].get(mid,'') for mid in ids)[:1400] or 'Please give me a moment or show me the material you mean.'
        return answer


def main():
    config();parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,default=Path('models/action-selector-final.json'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--steps',type=int,default=24);parser.add_argument('--request-cap',type=int,default=150)
    parser.add_argument('--case',action='append',help='Predeclared task_id:seed; repeat for matched evaluation cases')
    args=parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):parser.error('Use a new output directory')
    args.output.mkdir(parents=True,exist_ok=True)
    if not 1<=args.steps<=40 or not 1<=args.request_cap<=200:parser.error('Invalid experiment budget')
    cases=[('lantern_room',211),('second_passenger',307),('bell_before_dawn',401)]
    if args.case:
        from mercy.town.tasks import task_id
        try:cases=[(task_id(value.rsplit(':',1)[0]),int(value.rsplit(':',1)[1])) for value in args.case]
        except (ValueError,IndexError):parser.error('Each case must be a registered task_id:integer_seed')
        if len(cases)!=len(set(cases)) or len(cases)>8:parser.error('Use at most eight distinct cases')
    policy=Selector.load(args.checkpoint);frozen=dict(policy.weights)
    manifest={'cases':[{'task_id':t,'seed':s} for t,s in cases],'arms':['llm_ranked','rl_selected'],
      'steps':args.steps,'request_cap':args.request_cap,'checkpoint_sha256':hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
      'frozen_source':os.getenv('EXPERIMENT_FROZEN_SOURCE'),'npc_condition':'fixed grounded per-memory response bank; same disclosure gates in both arms; NOT live NPCs',
      'candidate_condition':'same ranked API proposal contract, two to six actions; no extra candidates for the selector',
      'limitations':[f'Only {len(cases)} matched cases; not statistical evidence of superiority.','Equal-state API proposals cached, but proposals after branch divergence can differ.','Not the default native-tool detective or a whole-competition comparison.']}
    write_json(args.output/'experiment.json',manifest)
    live.PROPOSER_SYSTEM+=' Rank candidates from most to least preferred: the first candidate is your best next action. This ranking is used by the baseline. Do not see or infer another selector’s output.'
    cache={};used=0;last=0.;results=[];start=time.monotonic()
    for task,seed in cases:
        gate=gates(task,seed,args.output/'gates'/task)
        if not gate['passed']:raise RuntimeError('Gate failed')
        original=build(task,seed)
        bank={pid:{m['id']:m['text'] for m in state['memories']} for pid,state in original.states.items()}
        write_json(args.output/task/'private-response-bank.json',bank)
        snapshot=original.export_private()
        for arm in ('llm_ranked','rl_selected'):
            world=type(original).restore(deepcopy(snapshot),FixedResponseBank(bank));book=Notebook(world.opening());rng=random.Random(seed)
            folder=args.output/task/arm;reason='step_cap';calls_before=used
            for step in range(1,args.steps+1):
                if time.monotonic()-start>1800 or used>=args.request_cap:reason='request_cap';break
                packet=book.packet(args.steps-step+1);key=hashlib.sha256(json.dumps(packet,sort_keys=True).encode()).hexdigest()
                tick=time.monotonic()
                try:
                    hit=key in cache
                    if hit:candidates,metadata=deepcopy(cache[key])
                    else:
                        delay=1.05-(time.monotonic()-last)
                        if delay>0:time.sleep(delay)
                        last=time.monotonic();used+=1
                        candidates,metadata=live.api_proposals(packet);cache[key]=deepcopy((candidates,metadata))
                    vectors=[features(book,a,args.steps-step+1,args.steps) for a in candidates]
                    selected,probabilities=policy.choose(vectors,rng,greedy=True) if arm=='rl_selected' else (0,[])
                    action=candidates[selected];observation=world.step(action['tool'],action['args']);book.observe(action,observation)
                    append_log(folder/'episode.jsonl',{'timestamp':time.time(),'step':step,'seed':seed,**metadata,
                        'candidates':candidates,'selected_index':selected,'selection_probabilities':probabilities,
                        'parsed_actions':[action],'tool_result':[observation],'proposal_cache_hit':hit,
                        'errors':[observation['error']] if 'error' in observation else [],'state':world.state_hash(),
                        'reward':world.result or {'pending_terminal_verification':True},'latency_ms':round((time.monotonic()-tick)*1000,3)})
                    print(json.dumps({'task':task,'arm':arm,'step':step,'action':action['tool'],'ended':world.ended,'api_requests':used}),flush=True)
                    if world.ended:reason='success' if world.result['success'] else 'failure';break
                except Exception as exc:
                    append_log(folder/'episode.jsonl',{'step':step,'error':type(exc).__name__})
                    book.history.append({'proposal_error':'No action executed. Return schema-valid candidates.'})
            if not world.ended:world.step('submit_report',{'findings':[],'narrative':'No supported report within the experiment budget.'})
            row={'task_id':task,'seed':seed,'arm':arm,'termination':reason,'result':world.result,'api_requests':used-calls_before}
            write_json(folder/'summary.json',row);results.append(row)
    if policy.weights!=frozen:raise RuntimeError('Evaluation changed weights')
    summary={'experiment':manifest,'rows':results,'requests_used':used,'seconds':round(time.monotonic()-start,3),
             'successes':{arm:sum(r['result']['success'] for r in results if r['arm']==arm) for arm in ('llm_ranked','rl_selected')}}
    write_json(args.output/'summary.json',summary);print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
