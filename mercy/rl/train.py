"""Train/evaluate the CPU selector; makes zero API calls and uses no GPU."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import statistics
import time

from mercy.town.io import write_json, append_log
from .curriculum import checkpoint, restore, propose, terminal_reward
from .policy import Selector
from .public import features


def rollout(policy, prepared, rng, budget=6, greedy=False, trace=False, noop=False):
    world, notebook = restore(prepared)
    trajectory, rows = [], []
    for step in range(budget):
        candidates = propose(notebook)
        rng.shuffle(candidates)
        vectors = [features(notebook, a, budget - step, budget) for a in candidates]
        if noop:
            chosen = next(i for i, a in enumerate(candidates) if a['tool'] == 'submit_report')
            action = {'tool': 'submit_report', 'args': {'findings': []}}
            probabilities = [1. / len(candidates)] * len(candidates)
        else:
            chosen, probabilities = policy.choose(vectors, rng, greedy)
            action = candidates[chosen]
        observation = world.step(action['tool'], action['args'])
        trajectory.append((vectors, chosen, probabilities))
        if trace:
            rows.append({'step': step + 1, 'candidates': candidates,
                         'probabilities': probabilities, 'selected_index': chosen,
                         'executed_action': action, 'observation': observation})
        notebook.observe(action, observation)
        if world.ended:
            break
    forced = not world.ended
    if forced:
        # No automatic solution after the budget. The policy must choose its
        # own report; otherwise a stalled search policy could exploit the harness.
        report = {'tool': 'submit_report', 'args': {'findings': [], 'narrative': 'No report submitted within the exercise budget.'}}
        observation = world.step(report['tool'], report['args'])
        if trace:
            rows.append({'step': 'finalize', 'executed_action': report, 'observation': observation})
    reward, result = terminal_reward(world)
    return trajectory, reward, {'success': bool(reward), 'steps': len(trajectory),
                               'termination': 'step_cap' if forced else 'submitted',
                               'town_report_score': result.get('score', 0), 'verifier': result,
                               'public_trace': rows}


def evaluate(policy, cases, seed, repeats=2, budget=6, greedy=False, noop=False, keep_traces=0):
    rows, traces = [], []
    for index, prepared in enumerate(cases):
        for repeat in range(repeats):
            # Independent per-case RNG: an earlier termination cannot shift later cases.
            rng = random.Random((seed + index * 1009) * 17 + repeat)
            _, reward, info = rollout(policy, prepared, rng, budget, greedy,
                                      trace=len(traces) < keep_traces, noop=noop)
            row = {'case_index': index, 'case_seed': prepared[0]['seed'], 'repeat': repeat,
                   'starting_hash': prepared[0]['state_hash'], 'starting_progress': prepared[3],
                   'reward': reward, **{k: info[k] for k in ('steps', 'termination', 'town_report_score')}}
            rows.append(row)
            if info['public_trace']:
                traces.append({**row, **info})
    rewards = [r['reward'] for r in rows]
    by_progress = {}
    for progress in range(4):
        subset = [r['reward'] for r in rows if r['starting_progress'] == progress]
        by_progress[str(progress)] = {'episodes': len(subset), 'mean_reward': statistics.mean(subset) if subset else None}
    return {'episodes': len(rows), 'mean_reward': statistics.mean(rewards),
            'success_rate': statistics.mean(rewards), 'mean_steps': statistics.mean(r['steps'] for r in rows),
            'by_starting_progress': by_progress, 'rows': rows}, traces


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episodes', type=int, default=2048)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--train-cases', type=int, default=24)
    parser.add_argument('--eval-cases', type=int, default=32)
    parser.add_argument('--eval-repeats', type=int, default=2)
    parser.add_argument('--budget', type=int, default=6)
    parser.add_argument('--learning-rate', type=float, default=.15)
    parser.add_argument('--seed', type=int, default=141)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if any(value < 1 for value in (args.episodes, args.batch_size, args.train_cases, args.eval_cases, args.eval_repeats, args.budget)) or not 0 < args.learning_rate <= 1:
        parser.error('Counts must be positive; learning-rate must be in (0, 1]')
    folder = args.output or Path('logs') / ('selector-' + str(time.time_ns()))
    if folder.exists() and any(folder.iterdir()):
        parser.error('Output directory must be new or empty; previous experiments are retained')
    folder.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    # Disjoint IDs fixed in advance; held-out evaluation is run only after training.
    train_seeds = [args.seed * 1000 + i for i in range(args.train_cases)]
    eval_seeds = [args.seed * 1000 + 100000 + i for i in range(args.eval_cases)]
    if set(train_seeds) & set(eval_seeds):
        raise ValueError('Training and evaluation overlap')
    cases = [checkpoint(seed) for seed in train_seeds]
    manifest = {'scope': 'same-case document-fabrication checkpoints; not unseen murder plots',
                'npc_backend': 'deterministic_fixture', 'proposer': 'public_rule_based',
                'train_seeds': train_seeds, 'eval_seeds': eval_seeds,
                'train_starting_hashes': [c[0]['state_hash'] for c in cases],
                'config': {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}}
    write_json(folder / 'experiment.json', manifest)
    policy = Selector()
    policy.save(folder / 'initial.json', {'training_episodes': 0})
    rng = random.Random(args.seed)
    baseline = 0.
    completed = 0
    while completed < args.episodes:
        episodes, counts, steps = [], Counter(), []
        for _ in range(min(args.batch_size, args.episodes - completed)):
            trajectory, reward, info = rollout(policy, rng.choice(cases), rng, args.budget)
            episodes.append((trajectory, reward))
            counts['successes'] += int(reward == 1)
            steps.append(info['steps'])
        gradient_norm = policy.update(episodes, baseline, args.learning_rate)
        mean_reward = statistics.mean(reward for _, reward in episodes)
        # A batch-level baseline from PRIOR batches only; not an expert target.
        baseline = .9 * baseline + .1 * mean_reward
        completed += len(episodes)
        row = {'episodes': completed, 'batch_reward': mean_reward, 'baseline_next': baseline,
               'gradient_norm': gradient_norm, 'mean_steps': statistics.mean(steps),
               'seconds': round(time.monotonic() - start, 3)}
        append_log(folder / 'learning.jsonl', row)
        if completed % (args.batch_size * 8) == 0 or completed == args.episodes:
            print(json.dumps(row), flush=True)
    policy.save(folder / 'policy.json', {'training_episodes': completed,
                'training_seed': args.seed, 'scope': manifest['scope'],
                'training_manifest_sha256': hashlib.sha256((folder / 'experiment.json').read_bytes()).hexdigest()})
    # No weight changes/checkpoint selection are allowed after this line.
    frozen = dict(policy.weights)
    heldout = [checkpoint(seed) for seed in eval_seeds]
    initial, initial_traces = evaluate(Selector(), heldout, 30017, args.eval_repeats, args.budget, keep_traces=2)
    trained, trained_traces = evaluate(policy, heldout, 30017, args.eval_repeats, args.budget, keep_traces=4)
    greedy, greedy_traces = evaluate(policy, heldout, 30017, args.eval_repeats, args.budget, greedy=True, keep_traces=2)
    noop, _ = evaluate(Selector(), heldout, 30017, 1, args.budget, noop=True)
    if frozen != policy.weights:
        raise RuntimeError('Evaluation mutated policy')
    # Public-tool reference for this focused exercise, not the PS whole-case oracle.
    reference_rewards = []
    for prepared in heldout:
        world, notebook = restore(prepared)
        for surface in ('stove', 'parlor table'):
            action = {'tool': 'search', 'args': {'surface': surface}}
            notebook.observe(action, world.step(action['tool'], action['args']))
        for tool in ('compare', 'submit_report'):
            action = next(a for a in propose(notebook) if a['tool'] == tool)
            notebook.observe(action, world.step(action['tool'], action['args']))
        reference_rewards.append(terminal_reward(world)[0])
    summary = {'scope': manifest['scope'], 'hardware': 'CPU; Python standard library; no API calls',
               'training_episodes': completed, 'budget': args.budget,
               'untrained_stochastic': initial, 'trained_stochastic': trained,
               'trained_greedy': greedy, 'noop': noop,
               'focused_reference_success': statistics.mean(reference_rewards),
               'paired_mean_reward_difference': trained['mean_reward'] - initial['mean_reward'],
               'eval_starting_hashes': [c[0]['state_hash'] for c in heldout],
               'seconds_total': round(time.monotonic() - start, 3),
               'limitations': ['Same authored incident; held-out seeds vary object IDs and prior acquisition progress, not the killer or causal plot.',
                               'Offline fixture characters and public rule-based proposals, not live LLM reasoning.',
                               'Exercise reward is supported forgery (0/1); original full-case score is separately recorded.',
                               'Frozen deployment selector is unvalidated on live LLM proposals.',
                               'This does not complete hackathon task/reference/no-op requirements.']}
    write_json(folder / 'evaluation.json', summary)
    write_json(folder / 'public-trajectories.json', {'untrained': initial_traces, 'trained': trained_traces, 'greedy': greedy_traces})
    print(json.dumps({'output': str(folder), 'training_episodes': completed,
                      'untrained_success': initial['success_rate'], 'trained_success': trained['success_rate'],
                      'greedy_success': greedy['success_rate'], 'seconds': summary['seconds_total']}), flush=True)


if __name__ == '__main__':
    main()
