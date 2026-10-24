"""Bounded transfer smoke: frozen selector, real API proposals and optional NPCs.

This never updates weights. It is not a paired performance comparison or a
compliant full-episode competition run. Output records both task reward and
the broader world score so a successful subtask cannot be called a solved case.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import time

from mercy.run import config
from mercy.town.agents import ModelAgent
from mercy.town.io import append_log, write_json
from .policy import Selector
from .public import features
from .skills import SKILLS, checkpoint, restore, reward
from .live import api_proposals
from .affordances import augment


class RequestBudget:
    def __init__(self, maximum):
        self.maximum = maximum
        self.used = 0
        self.last = 0.

    def take(self):
        if self.used >= self.maximum:
            raise RuntimeError('Live smoke request budget exhausted')
        delay = 1.05 - (time.monotonic() - self.last)
        if delay > 0:
            time.sleep(delay)
        self.last = time.monotonic()
        self.used += 1


def main():
    config()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint', type=Path, default=Path('models/action-selector-v2.json'))
    p.add_argument('--skills', nargs='+', choices=SKILLS, default=['forgery', 'witness', 'navigation'])
    p.add_argument('--steps', type=int, default=10)
    p.add_argument('--request-cap', type=int, default=70)
    p.add_argument('--npc-backend', choices=['llm', 'fixture'], default='llm')
    p.add_argument('--seed', type=int, default=341000)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    if not 1 <= args.steps <= 40 or not 1 <= args.request_cap <= 200:
        p.error('steps must be 1–40 and request-cap 1–200')
    folder = args.output or Path('logs') / ('selector-live-' + str(time.time_ns()))
    if folder.exists() and any(folder.iterdir()):
        p.error('Use a new or empty output directory')
    folder.mkdir(parents=True, exist_ok=True)
    policy = Selector.load(args.checkpoint)
    frozen = dict(policy.weights)
    requests = RequestBudget(args.request_cap)
    class LimitedActor(ModelAgent):
        def _call(self, messages):
            requests.take()
            return super()._call(messages)
    rows = []
    for index, skill in enumerate(args.skills):
        run = folder / skill
        case = checkpoint(skill, args.seed + index)
        actors = LimitedActor(audit=lambda row: append_log(run / 'private-actors.jsonl', row)) if args.npc_backend == 'llm' else None
        world, book = restore(case, actors)
        rng = random.Random(args.seed + index)
        beginning = time.monotonic()
        write_json(run / 'opening.json', book.packet(args.steps))
        termination = 'step_cap'
        for step in range(args.steps):
            try:
                requests.take()
                candidates, metadata = api_proposals(book.packet(args.steps - step))
                candidates = augment(book, candidates)
                rng.shuffle(candidates)
                vectors = [features(book, a, args.steps - step, args.steps) for a in candidates]
                chosen, probabilities = policy.choose(vectors, rng, greedy=True)
                action = candidates[chosen]
                result = world.step(action['tool'], action['args'])
                book.observe(action, result)
                append_log(run / 'episode.jsonl', {'timestamp': time.time(), 'step': step + 1,
                    'seed': case.seed, **metadata, 'candidates': candidates, 'selection_probabilities': probabilities,
                    'selected_index': chosen, 'parsed_actions': [action], 'tool_result': [result],
                    'errors': [result['error']] if 'error' in result else [], 'state': world.state_hash(),
                    'reward': world.result if world.ended else {'pending_terminal_verification': True}})
                print(json.dumps({'skill': skill, 'step': step + 1, 'action': action['tool'], 'ended': world.ended,
                                  'requests_used': requests.used}), flush=True)
                if world.ended:
                    termination = 'submitted'
                    break
            except Exception as exc:
                append_log(run / 'episode.jsonl', {'step': step + 1, 'error': type(exc).__name__})
                book.history.append({'proposal_error': 'No action executed. Use the supplied tool schemas and exact report predicate enum; propose legal alternatives.'})
                if requests.used >= requests.maximum:
                    termination = 'request_cap'
                    break
        if not world.ended:
            world.step('submit_report', {'findings': [], 'narrative': 'No report before the smoke-test budget expired.'})
        value, verifier = reward(skill, world)
        row = {'skill': skill, 'seed': case.seed, 'exercise_reward': value, 'town_report_score': verifier.get('score'),
               'verifier': verifier, 'termination': termination, 'seconds': round(time.monotonic() - beginning, 3)}
        rows.append(row)
        write_json(run / 'summary.json', row)
    if policy.weights != frozen:
        raise RuntimeError('Evaluation changed frozen weights')
    summary = {'checkpoint': str(args.checkpoint), 'checkpoint_sha256': hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
               'requests_used': requests.used, 'request_cap': args.request_cap, 'npc_backend': args.npc_backend,
               'rows': rows, 'limitations': ['Small transfer smoke with stochastic LLM behavior; no generalization or superiority claim.',
                                            'These begin from skill checkpoints, not a complete untouched crime scene.']}
    write_json(folder / 'summary.json', summary)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
