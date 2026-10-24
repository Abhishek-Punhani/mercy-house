"""Trusted reference policy. Never exposed to the evaluated agent."""
from .case import TASKS
from .env import Environment

def reference(task_id,seed):
    env=Environment(task_id,seed)
    required=env.task['claims']
    needed=set(e for c in required for e in env.case['proofs'][c])
    for eid in sorted(needed):
        env.step(env.case['evidence'][eid]['action'],{'evidence_id':eid})
    report={'claims':[{'claim_id':c,'status':'established' if env.case['truth'][c] else 'refuted','evidence_ids':env.case['proofs'][c]} for c in required]}
    env.step('submit_report',report)
    return env

def gates(seeds=(7,8)):
    results=[]
    for seed in seeds:
        for task_id in TASKS:
            oracle=reference(task_id,seed)
            noop=Environment(task_id,seed); noop.step('submit_report',{'claims':[]})
            row=dict(task_id=task_id,seed=seed,reference=oracle.result['score'],noop=noop.result['score'],reference_elapsed=oracle.state['elapsed'])
            row['passed']=row['reference']>=.95 and row['noop']<=.05
            results.append(row)
    return results
