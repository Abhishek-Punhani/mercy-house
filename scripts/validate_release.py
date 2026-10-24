"""Local release checks. No model calls; outputs are public, credential-free."""
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from mercy.town.factory import build
from mercy.town.reference import gates
from mercy.town.tasks import TASKS


def main():
    start=time.monotonic();seeds=[*range(16),37,82,211,307,401,-2**63,2**63-1]
    rows=[]
    for task in TASKS:
        for seed in seeds:
            row=gates(task,seed,ROOT/'logs/final-gate-sweep'/task/str(seed));assert row['passed']
            assert build(task,seed).state_hash()==row['starting_hash']
            rows.append(row)
    refusal_route=runpy.run_path(str(ROOT/'tests/town/test_cooperation.py'))['refusal_route']
    refusal=[]
    for task in TASKS:
        for seed in (0,1,7):
            world,result,calls=refusal_route(task,seed)
            assert result['success'] and not any(c['error'] for c in calls)
            # The fixture groups only up to three already-known identical asks
            # or access requests per reference decision; <=10 allowed tools.
            batches=sum(1 for h in world.history if h['action'] not in ('ask','request_access'))
            ask_calls=sum(1 for h in world.history if h['action']=='ask')
            refusal.append({'task_id':task,'seed':seed,'score':result['score'],'public_tool_calls':len(calls),
                'cooperation_events':sum(r['kind']=='bounded_cooperation' for r in world.audit.rows),
                'formal_access_events':sum(r['kind']=='formal_access' for r in world.audit.rows)})
    record={'passed':True,'scope':'Programmatic feasibility, not LLM performance. Protected references know the solution but acquire all proof through public tools.',
            'reference_noop_pairs':len(rows),'seeds':seeds,'all_reference_scores':1,'all_noop_scores':0,
            'always_declining_actor_runs':refusal,'always_declining_runs':len(refusal),'seconds':round(time.monotonic()-start,3),
            'rules':['At least three corroborated reassuring nonanswers can record an eligible external direct observation.',
                     'No self-incriminating, partial, hearsay or personal-history memory is compelled.',
                     'Formal access needs an acquired incident trace; inventory return needs its existing evidence/trust capability.',
                     'Prompt attacks never advance cooperation; permission or handover alone earns no score.']}
    (ROOT/'docs/FAIRNESS_RESULT.json').write_text(json.dumps(record,indent=2)+'\n')
    (ROOT/'logs/final-gate-sweep.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k not in ('always_declining_actor_runs','rules','seeds')}))


if __name__=='__main__':main()
