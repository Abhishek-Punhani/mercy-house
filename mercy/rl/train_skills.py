"""CPU REINFORCE over five real-world checkpoint skills; no model API calls."""
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import time

from mercy.town.io import write_json, append_log
from .policy import Selector
from .public import features
from .skills import SKILLS, checkpoint, restore, propose, reward, reference
from .affordances import augment


def rollout(policy, case, rng, budget=10, greedy=False, trace=False, noop=False):
    world, book = restore(case)
    trajectory, rows = [], []
    for step in range(budget):
        candidates = augment(book, propose(case.skill, book))
        rng.shuffle(candidates)
        vectors = [features(book, a, budget - step, budget) for a in candidates]
        chosen, probabilities = policy.choose(vectors, rng, greedy)
        action = {'tool': 'submit_report', 'args': {'findings': []}} if noop else candidates[chosen]
        observation = world.step(action['tool'], action['args'])
        trajectory.append((vectors, chosen, probabilities))
        book.observe(action, observation)
        if trace:
            rows.append({'step': step + 1, 'candidates': candidates, 'probabilities': probabilities,
                         'selected_index': chosen, 'executed_action': action, 'observation': observation})
        if world.ended:
            break
    termination = 'submitted'
    if not world.ended:
        termination = 'step_cap'
        world.step('submit_report', {'findings': [], 'narrative': 'No report within the exercise budget.'})
    value, verifier = reward(case.skill, world)
    return trajectory, value, {'skill': case.skill, 'seed': case.seed, 'reward': value,
                  'steps': len(trajectory), 'termination': termination,
                  'town_report_score': verifier.get('score', 0.), 'verifier': verifier, 'trace': rows}


def evaluate(policy, cases, budget, repeats=2, greedy=False, noop=False):
    rows, traces = [], []
    for index, case in enumerate(cases):
        for repeat in range(repeats):
            _, value, info = rollout(policy, case, random.Random(30017 + index * 1009 + repeat),
                                      budget, greedy, trace=repeat == 0, noop=noop)
            rows.append({k: v for k, v in info.items() if k not in ('trace', 'verifier')})
            if repeat == 0:
                traces.append(info)
    per_skill = {}
    for skill in SKILLS:
        subset = [r for r in rows if r['skill'] == skill]
        per_skill[skill] = {'episodes': len(subset), 'successes': sum(r['reward'] == 1 for r in subset),
                            'success_rate': statistics.mean(r['reward'] for r in subset),
                            'mean_steps': statistics.mean(r['steps'] for r in subset)}
    return {'episodes': len(rows), 'mean_reward': statistics.mean(r['reward'] for r in rows),
             'per_skill': per_skill, 'rows': rows}, traces


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episodes', type=int, default=16000)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--train-cases', type=int, default=16, help='Cases per skill')
    parser.add_argument('--eval-cases', type=int, default=16, help='Held-out cases per skill')
    parser.add_argument('--budget', type=int, default=10)
    parser.add_argument('--seed', type=int, default=141)
    parser.add_argument('--learning-rate', type=float, default=.15)
    parser.add_argument('--entropy',type=float,default=.02,help='Initial entropy regularization, annealed to one tenth')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if any(x < 1 for x in (args.episodes, args.batch_size, args.train_cases, args.eval_cases, args.budget)) or not 0 < args.learning_rate <= 1:
        parser.error('Counts must be positive; learning rate must be in (0, 1]')
    folder = args.output or Path('logs') / ('selector-skills-' + str(time.time_ns()))
    if folder.exists() and any(folder.iterdir()):
        parser.error('Use a new or empty output directory')
    folder.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    train = [checkpoint(skill, args.seed * 1000 + index) for skill in SKILLS for index in range(args.train_cases)]
    heldout = [checkpoint(skill, args.seed * 1000 + 100000 + index) for skill in SKILLS for index in range(args.eval_cases)]
    if {(c.skill, c.seed) for c in train} & {(c.skill, c.seed) for c in heldout}:
        raise RuntimeError('Overlapping train/test cases')
    source_files = ['mercy/rl/policy.py', 'mercy/rl/public.py', 'mercy/rl/affordances.py', 'mercy/rl/skills.py', 'mercy/rl/train_skills.py',
                    'mercy/town/world.py', 'mercy/town/agents.py', 'mercy/town/boundaries.py', 'mercy/town/setting.py', 'mercy/town/prose.py']
    source_root=Path(os.getenv('EXPERIMENT_FROZEN_SOURCE',Path(__file__).resolve().parents[2]))
    manifest = {'scope': 'five checkpoint skills within authored Mercy House incidents, not unseen complete plots',
                'config': {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
                'source_sha256': {f: hashlib.sha256((source_root/f).read_bytes()).hexdigest() for f in source_files},
                'frozen_source':str(source_root),
                'train': [{'skill': c.skill, 'seed': c.seed, 'hash': c.snapshot['state_hash']} for c in train],
                'heldout': [{'skill': c.skill, 'seed': c.seed, 'hash': c.snapshot['state_hash']} for c in heldout],
                'proposer': 'public rules; independent of hidden state; not trained language reasoning',
                'npc_policy': 'deterministic cooperative fixture with normal knowledge/disclosure/custody gates'}
    write_json(folder / 'experiment.json', manifest)
    gates = []
    for case in heldout:
        score, _ = reference(case)
        _, noop, _ = rollout(Selector(), case, random.Random(0), args.budget, noop=True)
        gates.append({'skill': case.skill, 'seed': case.seed, 'reference': score, 'noop': noop,
                      'passed': score >= .95 and noop <= .05})
    write_json(folder / 'exercise-gates.json', gates)
    if not all(row['passed'] for row in gates):
        raise RuntimeError('A skill exercise failed its feasibility/no-op gate; training aborted')
    policy = Selector()
    policy.save(folder / 'initial.json', {'training_episodes': 0})
    rng = random.Random(args.seed)
    by_skill = {skill: [c for c in train if c.skill == skill] for skill in SKILLS}
    baselines = defaultdict(float)
    completed = 0
    warmup = (args.episodes // 2 // len(SKILLS) // args.batch_size) * args.batch_size
    while completed < args.episodes:
        selected_skill = SKILLS[min(completed // max(1, warmup), len(SKILLS) - 1)] if completed < warmup * len(SKILLS) else None
        batch = []
        for _ in range(min(args.batch_size, args.episodes - completed)):
            skill = selected_skill or rng.choice(SKILLS)
            case = rng.choice(by_skill[skill])
            trajectory, value, info = rollout(policy, case, rng, args.budget)
            batch.append((skill, trajectory, value, info['steps']))
        # All episodes are on-policy for this frozen batch. Skill baselines are
        # from prior batches and do not depend on this episode's sampled actions.
        centered = [(trajectory, value - baselines[skill]) for skill, trajectory, value, _ in batch]
        entropy=args.entropy*max(.1,1-completed/args.episodes)
        gradient = policy.update(centered, baseline=0., learning_rate=args.learning_rate,entropy_coefficient=entropy)
        per_skill = {}
        for skill in SKILLS:
            values = [value for kind, _, value, _ in batch if kind == skill]
            if values:
                per_skill[skill] = statistics.mean(values)
                baselines[skill] = .9 * baselines[skill] + .1 * per_skill[skill]
        completed += len(batch)
        row = {'episodes': completed, 'phase': selected_skill or 'mixed',
               'batch_reward': statistics.mean(value for _, _, value, _ in batch),
               'per_skill': per_skill, 'gradient_norm': gradient,'entropy_coefficient':entropy,
               'seconds': round(time.monotonic() - started, 3)}
        append_log(folder / 'learning.jsonl', row)
        if completed % (args.batch_size * 16) == 0 or completed == args.episodes:
            print(json.dumps(row), flush=True)
    policy.save(folder / 'policy.json', {'training_episodes': completed, 'scope': manifest['scope'],
                                        'algorithm': 'episodic_REINFORCE', 'skills': list(SKILLS),
                                        'training_manifest_sha256': hashlib.sha256((folder / 'experiment.json').read_bytes()).hexdigest()})
    frozen = dict(policy.weights)
    summary = {'scope': manifest['scope'], 'training_episodes': completed, 'budget': args.budget,
               'hardware': 'CPU; Python standard library; zero model API calls', 'evaluations': {}}
    for name, candidate, greedy, noop in [('untrained', Selector(), False, False), ('trained_sampling', policy, False, False),
                                         ('trained_greedy', policy, True, False), ('noop', Selector(), False, True)]:
        result, traces = evaluate(candidate, heldout, args.budget, repeats=1 if noop else 2, greedy=greedy, noop=noop)
        summary['evaluations'][name] = result
        write_json(folder / (name + '-trajectories.json'), traces)
    if policy.weights != frozen:
        raise RuntimeError('Evaluation changed model weights')
    summary['seconds_total'] = round(time.monotonic() - started, 3)
    summary['limitations'] = ['Held-out seeds, witness roles, identities and initial progress within authored checkpoint families; not unseen murder plots.',
                              'Public heuristic proposers supply arguments and elementary report parsing. This language reasoning is not learned by the selector.',
                              'Fixture characters during RL. Live model proposal and NPC transfer must be measured separately.',
                              'This experiment is not completion of the hackathon five-task harness contract.']
    write_json(folder / 'evaluation.json', summary)
    print(json.dumps({'folder': str(folder), 'episodes': completed, 'seconds': summary['seconds_total'],
                     'results': {k: v['per_skill'] for k, v in summary['evaluations'].items()}}), flush=True)


if __name__ == '__main__':
    main()
