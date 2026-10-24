"""Train fresh CPU selector on original source-mechanism checkpoints, not elites."""
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import time

from mercy.town.io import append_log,write_json
from .policy import Selector
from .public import features
from .source_curriculum import SKILLS,SOURCES,checkpoint,restore,propose,reward,reference


def rollout(policy,case,rng,budget=8,greedy=False,trace=False,noop=False):
    world,book=restore(case);trajectory=[];rows=[]
    for step in range(budget):
        candidates=propose(case.skill,book);rng.shuffle(candidates)
        vectors=[features(book,a,budget-step,budget) for a in candidates]
        chosen,probabilities=policy.choose(vectors,rng,greedy)
        action={'tool':'submit_report','args':{'findings':[]}} if noop else candidates[chosen]
        obs=world.step(action['tool'],action['args']);book.observe(action,obs)
        trajectory.append((vectors,chosen,probabilities))
        if trace:rows.append({'step':step+1,'candidates':candidates,'probabilities':probabilities,'selected_index':chosen,'executed_action':action,'observation':obs})
        if world.ended:break
    reason='submitted' if world.ended else 'step_cap'
    if not world.ended:world.step('submit_report',{'findings':[]})
    score,verification=reward(case.skill,world)
    return trajectory,score,{'skill':case.skill,'seed':case.seed,'exercise_reward':score,'town_report_score':verification['score'],'steps':len(trajectory),'termination':reason,'verifier':verification,'trace':rows}


def evaluate(policy,cases,budget,greedy=False,noop=False):
    rows=[];traces=[]
    for i,case in enumerate(cases):
        for rep in range(1 if noop else 2):
            _,value,info=rollout(policy,case,random.Random(77201+i*97+rep),budget,greedy,trace=rep==0,noop=noop)
            rows.append({k:v for k,v in info.items() if k not in ('verifier','trace')})
            if rep==0:traces.append(info)
    return {'episodes':len(rows),'successes':sum(r['exercise_reward']==1 for r in rows),'mean_reward':statistics.mean(r['exercise_reward'] for r in rows),'per_skill':{s:{'episodes':len([r for r in rows if r['skill']==s]),'successes':sum(r['exercise_reward']==1 for r in rows if r['skill']==s)} for s in SKILLS},'rows':rows},traces


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--episodes',type=int,default=6000);p.add_argument('--seed',type=int,default=526);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()):p.error('Use a new output directory')
    if not 1<=a.episodes<=20000:p.error('Bounded episode count required')
    a.output.mkdir(parents=True,exist_ok=True);start=time.monotonic();budget=8;batch_size=32
    train=[checkpoint(s,920000+i) for s in SKILLS for i in range(16)]
    heldout=[checkpoint(s,930000+i) for s in SKILLS for i in range(16)]
    assert not {(c.skill,c.seed) for c in train}&{(c.skill,c.seed) for c in heldout}
    manifest={'algorithm':'episodic_REINFORCE_linear_softmax','initialization':'all-zero fresh Selector; no historical Mercy House weights','episodes':a.episodes,'seed':a.seed,'budget':budget,'batch_size':batch_size,'learning_rate':.15,'initial_entropy':.02,'train_cases':len(train),'heldout_cases':len(heldout),'sources':SOURCES,'frozen_source':os.getenv('EXPERIMENT_FROZEN_SOURCE'),
      'train':[{'skill':c.skill,'seed':c.seed,'hash':c.snapshot['state_hash']} for c in train],'heldout':[{'skill':c.skill,'seed':c.seed,'hash':c.snapshot['state_hash']} for c in heldout],
      'reward':'Binary terminal exercise reward: requested supported proposition with acquired provenance and no false/unsupported findings. Whole-case Town coverage score is recorded separately.',
      'proposer':'Authored rules read only acquired public descriptions and comparisons; not learned reading or source-episode understanding.',
      'npc_condition':'cooperative deterministic fixture with normal disclosure gates; zero API calls',
      'split':'No canonical Mercy House snapshot or elite trajectory in new training; reused FamilyTown causal templates and seed-heldout checkpoints, not unseen-template evaluation.',
      'limitations':['Original mechanism-inspired exercises, not exact source episodes or copied scripts.','Prior legal acquisitions are prepared at checkpoints.','No emotional state, hatred or ego is measured.','False accusations and unsupported source claims receive no exercise success; no bonuses for dialogue count.','This is selector training, not fine-tuning an API LLM.']}
    write_json(a.output/'experiment.json',manifest)
    gate=[]
    for c in heldout:
        ref=reference(c);_,no,_=rollout(Selector(),c,random.Random(0),budget,noop=True);gate.append({'skill':c.skill,'seed':c.seed,'reference':ref,'noop':no,'passed':ref>=.95 and no<=.05})
    write_json(a.output/'exercise-gates.json',gate)
    if not all(r['passed'] for r in gate):raise RuntimeError('Exercise feasibility/no-op gate failed')
    policy=Selector();policy.save(a.output/'initial.json',{'episodes':0});rng=random.Random(a.seed);baseline=defaultdict(float);completed=0
    by_skill={s:[c for c in train if c.skill==s] for s in SKILLS}
    while completed<a.episodes:
        batch=[]
        for _ in range(min(batch_size,a.episodes-completed)):
            skill=rng.choice(SKILLS);case=rng.choice(by_skill[skill]);trajectory,value,info=rollout(policy,case,rng,budget)
            batch.append((skill,trajectory,value))
        centered=[(traj,value-baseline[skill]) for skill,traj,value in batch]
        norm=policy.update(centered,0.,.15,.02*max(.1,1-completed/a.episodes))
        for skill in SKILLS:
            values=[v for s,t,v in batch if s==skill]
            if values:baseline[skill]=.9*baseline[skill]+.1*statistics.mean(values)
        completed+=len(batch)
        row={'episodes':completed,'batch_reward':statistics.mean(v for s,t,v in batch),'gradient_norm':norm,'seconds':round(time.monotonic()-start,3)}
        append_log(a.output/'learning.jsonl',row)
        if completed%512==0 or completed==a.episodes:print(json.dumps(row),flush=True)
    policy.save(a.output/'policy.json',{'training_episodes':completed,'sources':list(SKILLS),'scope':'Original source-mechanism checkpoints; no elite Mercy House training','training_manifest_sha256':hashlib.sha256((a.output/'experiment.json').read_bytes()).hexdigest()})
    frozen=dict(policy.weights);evaluations={}
    for name,candidate,greedy,noop in [('untrained',Selector(),False,False),('trained_sampling',policy,False,False),('trained_greedy',policy,True,False),('noop',Selector(),False,True)]:
        data,traces=evaluate(candidate,heldout,budget,greedy,noop);evaluations[name]=data;write_json(a.output/(name+'-trajectories.json'),traces)
    assert policy.weights==frozen
    result={'training_episodes':completed,'seconds':round(time.monotonic()-start,3),'coefficients':len(policy.weights),'checkpoint_sha256':hashlib.sha256((a.output/'policy.json').read_bytes()).hexdigest(),'hardware':'CPU; standard library; zero training API calls','experiment':manifest,'evaluations':evaluations,'limitations':manifest['limitations']}
    write_json(a.output/'evaluation.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('experiment','evaluations')}),flush=True)

if __name__=='__main__':main()
