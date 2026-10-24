"""Protected reference investigators. They act through public tools, not snapshots.

The scripts know the authored solution but must acquire its admissible support.
They establish feasibility; they are not presented as learned or LLM policies.
"""
import json
from pathlib import Path
import time

from .factory import build
from .io import append_log, write_json
from .tasks import TASKS
from mercy.rl.public import Notebook


class Investigator:
    def __init__(self, world, folder=None, kind='reference'):
        self.world = world
        self.book = Notebook(world.opening())
        self.folder = Path(folder) if folder else None
        self.kind = kind
        self.step = 0

    def act(self, tool, **args):
        self.step += 1
        start = time.monotonic()
        action = {'tool': tool, 'args': args}
        observation = self.world.step(tool, args)
        self.book.observe(action, observation)
        if self.folder:
            append_log(self.folder / 'episode.jsonl', {
                'timestamp': time.time(), 'step': self.step, 'seed': self.world.seed,
                'model_input': None, 'model_output_raw': {'script': self.kind, 'action': action},
                'parsed_actions': [action], 'tool_result': [observation],
                'errors': [observation['error']] if 'error' in observation else [],
                'state': self.world.state_hash(),
                'reward': self.world.result or {'total': 0, 'pending_terminal_verification': True},
                'tokens': None, 'latency_ms': round((time.monotonic() - start) * 1000, 3)})
        if 'error' in observation:
            raise RuntimeError('Reference action denied: ' + tool)
        return observation

    def go(self, *destinations):
        for destination in destinations:
            self.act('go', destination=destination)

    def rid(self, label):
        return next(r['record_id'] for r in self.book.records.values() if r.get('label') == label)

    def compare(self, *labels):
        return self.act('compare', records=[self.rid(label) for label in labels])

    def finish(self, assertions):
        sources = list(self.book.records)
        findings = [dict(actor=actor, predicate=predicate, object=obj, sources=sources)
                    for actor, predicate, obj in assertions]
        self.act('submit_report', findings=findings,
                 narrative='Reference reconstruction using acquired records. Hypotheses outside the selected scope remain unresolved.')
        return self.world.result


def solve(world, folder=None):
    task = world.task_id
    a = Investigator(world, folder)
    a.act('people_here')
    a.act('search', surface='floor')
    a.act('search', surface='desk')
    a.act('request_access', pid='savitri')
    a.go('hall')
    a.act('people_here')
    a.act('request_access', pid='vedant')
    for _ in range(2):
        a.act('ask', pid='vedant', question='Please distinguish what you personally saw from what you heard. What happened at the archive door?',
              approach='reassure', show=[a.rid('brass seal'), a.rid('torn cuff')])
    if task == 'last_witness':
        return a.finish([('savitri', 'killed', 'mira')])
    a.act('search', surface='visitors book')
    a.go('courtyard', 'square', 'das_house')
    a.act('people_here')
    a.act('search', surface='parlor table')
    a.act('search', surface='stove')
    a.act('search', surface='writing desk')
    a.compare('folded note', 'household paper', 'signed shopping note')
    a.compare('folded sheet', 'copybook', 'signed shopping note')
    if task == 'borrowed_signature':
        return a.finish([('savitri', 'forged', 'threat')])
    a.go('square', 'rao_house')
    a.act('search', surface='correspondence drawer')
    if task == 'brothers_letter':
        a.go('square', 'courtyard', 'hall')
        for _ in range(2):
            a.act('ask', pid='kabir', question='This independent invoice names the carrier. Please explain any unreported correspondence and return what you retained.',
                  approach='reassure', show=[a.rid('carbon invoice')])
        return a.finish([('kabir', 'concealed', 'delivery_letter')])
    a.go('square', 'courtyard', 'garden')
    a.act('search', surface='winter beds')
    found = a.act('search', surface='tool shed')
    spade = next(r for r in found['findings'] if r['label'] == 'spade')
    a.act('collect', oid=spade['object_id'])
    a.act('excavate', surface='winter beds')
    a.compare('carbon invoice', 'folded envelope')
    if task == 'garden_burials':
        return a.finish([('savitri', 'commissioned', 'burials'),('nalin','moved','burials')])
    a.go('cemetery', 'chapel')
    a.act('search', surface='register desk')
    a.compare('ink-stained ledger', 'parish register')
    return a.finish([('savitri', 'killed', 'mira'), ('vedant', 'assisted', 'mira'),
                     ('savitri', 'forged', 'threat'), ('savitri', 'commissioned', 'burials'),('nalin','moved','burials'),
                     ('savitri', 'altered', 'tara_statement'), ('vedant', 'altered', 'death_register')])


def gates(task, seed, folder):
    folder = Path(folder)
    start = time.monotonic()
    reference = build(task, seed)
    noop = build(task, seed)
    starting_hash = reference.state_hash()
    if starting_hash != noop.state_hash():
        raise RuntimeError('Reset determinism failed')
    oracle = solve(reference, folder / 'reference')
    giveup = Investigator(noop, folder / 'noop', 'noop')
    giveup.act('submit_report', findings=[])
    seconds = time.monotonic() - start
    result = {'task_id': task, 'seed': seed, 'starting_hash': starting_hash,
              'reference': oracle['score'], 'noop': noop.result['score'], 'seconds': round(seconds, 3),
              'passed': oracle['score'] >= .95 and noop.result['score'] <= .05 and seconds <= 120}
    for name, w in [('reference', reference), ('noop', noop)]:
        write_json(folder / name / 'summary.json', {'task_id': task, 'seed': seed,
            'termination_reason': 'success' if w.result.get('success') else 'failure', 'result': w.result})
    write_json(folder / 'gate.json', result)
    if not result['passed']:
        raise RuntimeError('Baseline gate failed before the evaluated model')
    return result


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--seed', type=int, default=7)
    p.add_argument('--output', type=Path, default=Path('baseline-results'))
    args = p.parse_args()
    results = [gates(task, args.seed, args.output / task) for task in TASKS]
    write_json(args.output / 'gate.json', results)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
