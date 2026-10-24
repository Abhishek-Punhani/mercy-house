"""Authoritative state transitions and programmatic final verification."""
import hashlib
import json
from .case import build_case, CLAIMS, TASKS

class Environment:
    def __init__(self, task_id='mira_murder', seed=7):
        if task_id not in TASKS:
            raise ValueError('Unknown task_id')
        if type(seed) is not int:
            raise ValueError('Seed must be an integer')
        self.case = build_case(seed)
        self.task_id = task_id
        self.task = TASKS[task_id]
        self.state = dict(seed=seed, task_id=task_id, elapsed=0, acquired=[], preserved=[], destroyed=[], history=[], terminated=False)
        self.result = None

    def state_hash(self):
        return hashlib.sha256(json.dumps(self.state, sort_keys=True).encode()).hexdigest()

    def observe(self):
        return dict(setting='Bhairav’s Hollow, November 1900. Murder at Mercy House. No phones, cameras or internet. You are Tara’s sibling; Raghav is your personal enemy, Kabir your trusted subordinate, Leena your former partner. These relationships are not evidence.',
                    task_id=self.task_id, difficulty=self.task['level'], required_claims={c: CLAIMS[c] for c in self.task['claims']},
                    budget=self.task['budget'], elapsed=self.state['elapsed'], acquired=self.state['acquired'],
                    characters={k: {'name':v['name'],'background':v['background']} for k,v in self.case['characters'].items()},
                    catalog=[{k:e[k] for k in ('id','title','action')} for e in self.case['evidence'].values()],
                    report_contract='Submit claims: [{claim_id, status: established|refuted|unresolved, evidence_ids: [...]}]. Cite acquired evidence. Refuted means the proposition is false. Hypotheses get no resolution credit. Only one final submission. Preserve ash-bucket material before confronting Savitri. Full task credit requires all listed propositions supported, including refutations. Narrative is retained but not semantically scored.',
                    state_hash=self.state_hash())

    def step(self, action, args):
        if self.state['terminated']:
            return {'error':'Episode already ended'}
        if not isinstance(args, dict):
            return {'error':'Arguments must be an object'}
        before = self.state_hash()
        try:
            output = self._apply(action, args)
        except (KeyError, TypeError, ValueError) as exc:
            output = {'error':str(exc)[:300]}
        self.state['history'].append({'action':action, 'args':args, 'output':output, 'before':before})
        if self.state['elapsed'] >= self.task['budget'] and not self.state['terminated']:
            self.finish('time_cap')
        return output

    def _apply(self, action, args):
        if action == 'catalog':
            if args:
                raise ValueError('catalog takes no arguments')
            return self.observe()
        if action in ('examine','authenticate','interview','preserve'):
            if set(args) != {'evidence_id'}:
                raise ValueError('Expected only evidence_id')
            eid = args['evidence_id']
            if not isinstance(eid,str) or eid not in self.case['evidence']:
                raise ValueError('Unknown evidence ID; paths and file access are not supported')
            item = self.case['evidence'][eid]
            if eid in self.state['destroyed']:
                return {'error':'This material was destroyed; no observation available'}
            if action == 'preserve':
                if eid not in self.state['preserved']:
                    self.state['preserved'].append(eid)
                    self.state['elapsed'] += 1
                return {'preserved':eid}
            if action != item['action']:
                raise ValueError(f'Use {item["action"]} for this item')
            if eid not in self.state['acquired']:
                self.state['elapsed'] += 3 if action == 'authenticate' else 2
                self.state['acquired'].append(eid)
            return {k:item[k] for k in ('id','title','content')}
        if action == 'confront':
            if set(args) != {'character'} or args['character'] not in self.case['characters']:
                raise ValueError('Expected a known character')
            self.state['elapsed'] += 5
            if args['character'] == 'savitri':
                for eid,item in self.case['evidence'].items():
                    if item['key'] == 'draft' and eid not in self.state['preserved'] and eid not in self.state['acquired']:
                        self.state['destroyed'].append(eid)
                return {'statement':'I will not discuss my household papers.', 'event':'Savitri burns unpreserved ash-bucket fragments. Previously recorded observations remain available.'}
            return {'statement':'My first account is not the whole story. Check original records before accusing anyone.'}
        if action == 'submit_report':
            if set(args) - {'claims','narrative'} or 'claims' not in args:
                raise ValueError('Expected claims and optional narrative')
            self.result = self.verify(args)
            self.state['terminated'] = True
            return {'submitted':True, 'termination_reason':'success' if self.result['score'] >= .95 else 'failure'}
        raise ValueError('Unknown tool; only catalog, examine, authenticate, interview, preserve, confront and submit_report are available')

    def verify(self, report):
        entries = report.get('claims')
        if not isinstance(entries,list) or len(entries)>100:
            raise ValueError('claims must be an array of at most 100 entries')
        seen, supported, errors = set(), [], []
        acquired = set(self.state['acquired'])
        for entry in entries:
            if not isinstance(entry,dict) or set(entry) != {'claim_id','status','evidence_ids'}:
                errors.append('Malformed claim'); continue
            cid, status, refs = entry['claim_id'],entry['status'],entry['evidence_ids']
            if not isinstance(cid,str) or cid not in CLAIMS or cid in seen:
                errors.append('Unknown or duplicate claim'); continue
            seen.add(cid)
            if status not in ('established','refuted','unresolved') or not isinstance(refs,list) or not all(isinstance(x,str) for x in refs):
                errors.append(f'{cid}: malformed status or citations'); continue
            if status == 'unresolved':
                continue
            if (status == 'established') != self.case['truth'][cid]:
                errors.append(f'{cid}: incorrect attribution'); continue
            if not set(refs).issubset(acquired):
                errors.append(f'{cid}: unacquired or invented evidence'); continue
            if not any(set(bundle).issubset(refs) for bundle in self.case['proof_bundles'][cid]):
                errors.append(f'{cid}: missing required evidentiary dependencies'); continue
            supported.append(cid)
        required=set(self.task['claims'])
        coverage=len(required.intersection(supported))/len(required)
        penalty=min(1.0, .12*len(errors))
        return dict(score=round(max(0.0,coverage-penalty),6), components={'supported_required_fraction':coverage,'unsupported_claim_penalty':penalty},
                    supported_claims=supported, missing_claims=sorted(required-set(supported)), errors=errors,
                    limitations='Scores enumerated factual claims and evidence dependencies, not prose, hidden emotions or legal culpability. Evidence alternatives are not yet exhaustive.')

    def finish(self, reason):
        if not self.state['terminated']:
            self.state['terminated']=True
            self.result=dict(score=0.0,components={'supported_required_fraction':0.0,'unsupported_claim_penalty':0.0},supported_claims=[],missing_claims=self.task['claims'],errors=[],termination_reason=reason)
        return self.result
