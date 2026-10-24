"""Features and notebook built exclusively from received public observations.

No raw names, object IDs, signatures or case answers become trainable features.
The notebook retains acquired text so a separate proposer can reason about it.
"""
from copy import deepcopy
import json


def action_key(action):
    args = action['args']
    target = {k: args[k] for k in ('destination', 'surface', 'pid', 'approach', 'records', 'by', 'supervise') if k in args}
    return json.dumps([action['tool'], target], sort_keys=True)


class Notebook:
    def __init__(self, opening):
        self.opening = deepcopy(opening)
        self.scene = deepcopy(opening.get('now', {}))
        self.people = {}
        self.records = {}
        self.history = []
        self.attempts = {}
        self.failed = set()
        self.secured = set()
        self._records(opening.get('notes', []))

    def _records(self, value):
        if isinstance(value, list):
            for child in value:
                self._records(child)
        elif isinstance(value, dict):
            if isinstance(value.get('record_id'), str):
                rid = value['record_id']
                # A custody acknowledgement reuses the acquisition receipt ID;
                # it must not erase the document it acknowledges.
                self.records[rid] = {**self.records.get(rid, {}), **deepcopy(value)}
            for child in value.values():
                if isinstance(child, (dict, list)):
                    self._records(child)

    def observe(self, action, result):
        self.history.append({'action': deepcopy(action), 'observation': deepcopy(result)})
        key = action_key(action)
        self.attempts[key] = self.attempts.get(key, 0) + 1
        if 'error' in result:
            self.failed.add(key)
        if isinstance(result.get('place'), dict):
            self.scene = deepcopy(result)
        if isinstance(result.get('people'), list):
            self.people[self.scene.get('place', {}).get('id', '')] = deepcopy(result['people'])
        if isinstance(result.get('secured'), str):
            self.secured.add(result['secured'])
        self._records(result)

    def packet(self, steps_left):
        return {'opening': deepcopy(self.opening), 'scene': deepcopy(self.scene),
                'people_seen': deepcopy(self.people), 'acquired_records': list(deepcopy(self.records).values()),
                'investigation_history': deepcopy(self.history), 'steps_left': steps_left}


def features(notebook, action, steps_left, budget):
    """A whitelist of public, generic progress/candidate features, not truth labels."""
    name, args = action['tool'], action['args']
    records = list(notebook.records.values())
    comparisons = [r for r in records if 'compared' in r]
    # This is an observation of concrete comparison findings, not a verifier flag.
    specific = any(r.get('observation', '') and not r['observation'].startswith('You lay out the records.') for r in comparisons)
    state = {'bias': 1., 'records': min(len(records), 12) / 12.,
             'comparison': float(bool(comparisons)), 'specific_comparison': float(specific),
             'testimony': float(any('recollections' in r for r in records)),
             'remaining': steps_left / max(1, budget), 'last_step': float(steps_left == 1)}
    row = {'tool:' + name: 1.}
    row.update({name + '/' + key: value for key, value in state.items()})
    key = action_key(action)
    row['repeated'] = float(key in notebook.attempts)
    row['repeat_count'] = min(notebook.attempts.get(key, 0), 3) / 3.
    row['previously_denied'] = float(key in notebook.failed)
    if name == 'ask':
        approach = args.get('approach', 'neutral')
        row['approach:' + approach] = 1.
        row['showing_records'] = float(bool(args.get('show')))
        previous = [h for h in notebook.history if h.get('action', {}).get('tool') == 'ask'
                    and h['action']['args'].get('pid') == args.get('pid')]
        row['interviewed_target'] = float(bool(previous))
        row['target_interview_count'] = min(len(previous), 4) / 4.
        people = [p for group in notebook.people.values() for p in group if p['id'] == args.get('pid')]
        row['target_unresponsive'] = float(any('no response' in p.get('appearance', '').lower() for p in people))
        accounts = [r for r in records if r.get('person') == args.get('pid') and 'recollections' in r]
        row['target_has_firsthand_account'] = float(any(m['basis'] in ('direct_observation', 'partial_observation')
                 for r in accounts for m in r['recollections']))
        row['target_has_hearsay'] = float(any('gossip' in m['text'].lower() or m['basis'] == 'hearsay'
                 for r in accounts for m in r['recollections']))
    if name == 'search':
        row['delegated'] = float(args.get('by', 'detective') != 'detective')
        row['supervised'] = float(args.get('supervise', False))
        by = args.get('by', 'detective')
        accounts = [r for r in records if r.get('person') == by and 'recollections' in r]
        row['delegate_disclosed_family_connection'] = float(any('brother' in m['text'].lower()
                  for r in accounts for m in r['recollections']))
        row['delegated_family_unsupervised'] = row['delegate_disclosed_family_connection'] * row['delegated'] * (1. - row['supervised'])
    if name == 'collect':
        row['already_secured'] = float(args.get('oid') in notebook.secured)
    if name == 'go':
        destination = args.get('destination')
        interviewed = {r.get('person') for r in records if 'recollections' in r}
        row['destination_has_interview_contact'] = float(any(p['id'] in interviewed for p in notebook.people.get(destination, [])))
        visited = {h.get('observation', {}).get('place', {}).get('id') for h in notebook.history}
        row['destination_visited'] = float(destination in visited)
    if name == 'submit_report':
        findings = args.get('findings', [])
        sources = [s for finding in findings for s in finding.get('sources', [])]
        row['report_nonempty'] = float(bool(findings))
        row['report_sources'] = min(len(set(sources)), 12) / 12.
        row['report_unacquired_sources'] = float(any(s not in notebook.records for s in sources))
        cited = [notebook.records[s] for s in set(sources) if s in notebook.records]
        row['report_direct_account'] = float(any(m['basis'] == 'direct_observation' for r in cited for m in r.get('recollections', [])))
        row['report_partial_account'] = float(any(m['basis'] == 'partial_observation' for r in cited for m in r.get('recollections', [])))
        row['report_hearsay_account'] = float(any('gossip' in m['text'].lower() or m['basis'] == 'hearsay'
                                               for r in cited for m in r.get('recollections', [])))
        row['report_specific_comparison'] = float(any('compared' in r and not r.get('observation', '').startswith('You lay out the records.') for r in cited))
        here = notebook.scene.get('place', {}).get('id')
        row['report_unsecured_local_objects'] = min(sum('object_id' in r and r.get('where') == here
                    and r['object_id'] not in notebook.secured for r in cited), 4) / 4.
        goal = json.dumps(notebook.opening.get('exercise') or notebook.opening.get('task') or notebook.opening.get('assignment', '')).lower()
        wanted = set()
        if any(w in goal for w in ('fatal assault', 'fatal blow')):wanted.add('killed')
        if any(w in goal for w in ('document', 'signature', 'fabricat')):wanted.add('forged')
        if any(w in goal for w in ('relocation', 'delivery correspondence')):wanted.add('moved')
        if 'physical match' in goal:wanted.add('matched')
        row['report_matches_public_scope'] = sum(f.get('predicate') in wanted for f in findings) / max(1, len(findings)) if wanted else 0.
    # Context comes from the PUBLIC assignment, not a protected task label.
    text = json.dumps(notebook.opening.get('exercise') or notebook.opening.get('task') or notebook.opening.get('assignment', '')).lower()
    contexts = {'documents': any(w in text for w in ('document', 'signature', 'fabricat')),
                'witnesses': any(w in text for w in ('first-hand', 'witness', 'fatal assault')),
                'followup': 'follow up' in text,
                'custody': any(w in text for w in ('custody', 'delegated', 'secure the delivery'))}
    base = dict(row)
    for context, active in contexts.items():
        if active:
            row.update({context + '::' + key: value for key, value in base.items()})
    return row
