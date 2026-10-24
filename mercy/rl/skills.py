"""Trusted multi-skill curricula; public proposers never receive world objects.

These are checkpoint exercises in the authored town, not claims of general
social reasoning or held-out murder-plot performance. All practice actions go
through the normal world engine and all proof rewards use its verifier.
"""
from copy import deepcopy
from dataclasses import dataclass
import random
import re

from mercy.town.world import Town
from mercy.town.factory import ReferenceActors
from .public import Notebook
from .curriculum import checkpoint as forgery_checkpoint, propose as forgery_proposals

SKILLS = ('forgery', 'witness', 'statement_review', 'navigation', 'delegation')


@dataclass
class Case:
    skill: str
    snapshot: dict
    opening: dict
    tape: list
    seed: int


def checkpoint(skill, seed):
    if skill not in SKILLS:
        raise ValueError('Unknown training skill')
    if skill == 'forgery':
        snapshot, opening, tape, _ = forgery_checkpoint(seed)
        opening = deepcopy(opening)
        opening['exercise'] = {'instruction': 'Investigate the threatening document’s origin. Establish any fabrication with acquired records and physical comparisons. A signature alone does not identify its writer.'}
        return Case(skill, snapshot, opening, tape, seed)
    rng = random.Random(seed)
    world = Town(seed, ReferenceActors())
    if skill in ('witness', 'statement_review'):
        # Counterfactual authored placement BEFORE the incident, so the normal
        # event engine generates this person's actual limited observations.
        witness = rng.choice(['bina', 'padma', 'hari', 'kamala', 'ritu'])
        world.people[witness]['location'] = 'archive'
    world.simulate(4)
    opening = world.arrive()
    tape = []

    def step(tool, args):
        action = {'tool': tool, 'args': args}
        observation = world.step(tool, args)
        if 'error' in observation:
            raise RuntimeError('Illegal skill checkpoint setup')
        tape.append((action, observation))
        return observation

    def go(*places):
        for place in places:
            step('go', {'destination': place})

    if skill in ('witness', 'statement_review'):
        # One real eyewitness among people who arrived AFTER the assault.
        # The selector is never told which role was placed here before it.
        for pid in rng.sample([p for p in ('bina', 'padma', 'hari', 'kamala', 'ritu') if p != witness], 2):
            world.people[pid]['location'] = 'archive'
            world.event('arrival', pid, 'archive', world.people[pid]['name'] + ' arrives after the injury was reported.')
        if skill == 'statement_review':
            world.people['sera']['location'] = 'archive'
            world.event('arrival', 'sera', 'archive', 'Sera joins the inquiry after fetching help.')
        step('search', {'surface': 'floor'})
        step('people_here', {})
        if skill == 'statement_review':
            step('ask', {'pid': 'sera', 'question': 'What have people said about the argument?', 'approach': 'neutral'})
        world.task_id = 'last_witness'
        instruction = 'Establish the fatal assault with a first-hand account and physical traces. Distinguish what someone saw from a rumor; questions and uncertainty are not conclusions.'
    elif skill == 'navigation':
        step('search', {'surface': 'floor'})
        go('hall', 'courtyard')
        step('people_here', {})
        step('ask', {'pid': 'sera', 'question': 'What can be seen through the hatch?', 'approach': 'neutral'})
        go('square', 'das_house')
        step('people_here', {})
        step('search', {'surface': 'parlor table'})
        go('square')
        progress=rng.randrange(3)
        if progress:
            go('courtyard')
            step('people_here',{})
        if progress==2:
            step('ask',{'pid':'sera','question':'What did you personally see through the hatch?','approach':'reassure'})
        instruction = 'Follow up with the person you previously spoke to about the service hatch. Obtain a first-hand account and establish the physical match between acquired garment pieces. Report the match with sources; an unidentified sleeve does not establish who delivered a fatal injury.'
    else:
        go('hall', 'courtyard', 'square', 'rao_house')
        step('people_here', {})
        step('request_access', {'pid': 'vedant'})
        found = step('search', {'surface': 'correspondence drawer'})
        invoice = next(r['record_id'] for r in found['findings'] if r['label'] == 'carbon invoice')
        go('square', 'courtyard', 'hall')
        step('people_here', {})
        for _ in range(2):
            step('ask', {'pid': 'kabir', 'question': 'Do you have any family connection to the carrier named here?',
                         'approach': 'reassure', 'show': [invoice]})
        instruction = 'Find and secure the delivery correspondence and establish the relocation described in independent records. Preserve its custody during any delegated search; do not let a personal connection erase evidence.'
    opening = deepcopy(opening)
    opening['exercise'] = {'instruction': instruction}
    return Case(skill, world.export_private(), opening, tape, seed)


def restore(case, agents=None):
    world = Town.restore(case.snapshot, agents or ReferenceActors())
    notebook = Notebook(case.opening)
    for action, observation in case.tape:
        notebook.observe(action, observation)
    return world, notebook


def _physical(book):
    return [r for r in book.records.values() if 'object_id' in r]


def _murder_reports(book):
    physical = _physical(book)
    traces = [r['record_id'] for r in physical if r.get('label') in ('body', 'brass seal', 'torn cuff')]
    accounts = [r for r in book.records.values() if 'recollections' in r]
    reports = []
    for account in accounts:
        text = ' '.join(m['text'] for m in account['recollections'])
        match = re.search(r'\b([A-Z][a-z]+) strikes ([A-Z][a-z]+)\b', text)
        if match:
            reports.append({'tool': 'submit_report', 'args': {'findings': [
                {'actor': match[1].lower(), 'predicate': 'killed', 'object': match[2].lower(),
                 'sources': traces + [account['record_id']]}]}})
        if 'gossip that Dev threatened Mira' in text:
            reports.append({'tool': 'submit_report', 'args': {'findings': [
                {'actor': 'dev', 'predicate': 'killed', 'object': 'mira', 'sources': traces + [account['record_id']]}]}})
    # A partial view names nobody. A hypothesis can be proposed only after an
    # acquired tagged garment supplies identity; the verifier still needs a join.
    if any(any(m['basis'] == 'partial_observation' for m in r['recollections']) for r in accounts):
        garment = next((r for r in physical if r.get('label') == 'household shawl'), None)
        if garment:
            initial = re.search(r'\b([A-Z])\.\s+([A-Z][a-z]+)', garment['description'])
            people = [p for group in book.people.values() for p in group]
            owner = next((p['id'] for p in people if initial and p['name'].startswith(initial[1]) and p['name'].endswith(initial[2])), None)
            if owner:
                reports.append({'tool': 'submit_report', 'args': {'findings': [
                    {'actor': owner, 'predicate': 'killed', 'object': 'mira', 'sources': list(book.records)}]}})
    return reports or [{'tool': 'submit_report', 'args': {'findings': []}}]


def propose(skill, book):
    if skill == 'forgery':
        return forgery_proposals(book)
    candidates = [{'tool': 'look', 'args': {}}, {'tool': 'people_here', 'args': {}}]
    here = book.scene.get('place', {}).get('id', '')
    if skill in ('witness', 'statement_review', 'navigation'):
        for person in book.people.get(here, []):
            if person['id'] in ('kabir', 'anya') and skill == 'navigation':
                continue
            for approach in ('neutral', 'reassure', 'challenge'):
                candidates.append({'tool': 'ask', 'args': {'pid': person['id'],
                    'question': 'Take your time. What did you personally see, and what did you only hear from somebody else?', 'approach': approach}})
        if skill == 'navigation':
            for destination in book.scene.get('exits', []):
                candidates.append({'tool': 'go', 'args': {'destination': destination['id']}})
            physical = _physical(book)
            cuff = next((r for r in physical if r['label'] == 'torn cuff'), None)
            coat = next((r for r in physical if r['label'] == 'household shawl'), None)
            if cuff and coat:
                candidates.append({'tool': 'compare', 'args': {'records': [cuff['record_id'], coat['record_id']]}})
            findings = [{'actor': coat['object_id'], 'predicate': 'matched', 'object': cuff['object_id'], 'sources': list(book.records)}] if cuff and coat else []
            candidates.append({'tool': 'submit_report', 'args': {'findings': findings}})
        else:
            candidates.extend(_murder_reports(book))
            aid = next((r for r in book.records.values() if r.get('label') == 'bloodied sleeve'), None)
            if aid:
                candidates.append({'tool': 'submit_report', 'args': {'findings': [{'actor': 'dev', 'predicate': 'aided', 'object': 'mira', 'sources': [aid['record_id']]}]}})
    else:
        for surface in book.scene.get('searchable_features', []):
            candidates.append({'tool': 'search', 'args': {'surface': surface}})
            for by, supervised in (('kabir', False), ('kabir', True), ('anya', False)):
                candidates.append({'tool': 'search', 'args': {'surface': surface, 'by': by, 'supervise': supervised}})
        physical = _physical(book)
        letter = next((r for r in physical if r['label'] == 'folded envelope'), None)
        invoice = next((r for r in physical if r['label'] == 'carbon invoice'), None)
        if letter:
            candidates.append({'tool': 'collect', 'args': {'oid': letter['object_id']}})
        findings = []
        if letter and invoice:
            # This is the same explicitly documented public parsing prior as the
            # forgery proposer; names never become selector coefficients.
            # The named payer commissioned the journey; the letter's signed
            # carrier performed it. Never turn payment into physical carrying.
            who = re.search(r'([A-Z][a-z]+)\.[”"]\s+A second fold', letter['description'])
            if who:
                findings = [{'actor': who[1].lower(), 'predicate': 'moved', 'object': 'burials',
                             'sources': [letter['record_id'], invoice['record_id']]}]
        candidates.append({'tool': 'submit_report', 'args': {'findings': findings}})
    return candidates


def reward(skill, world):
    result = deepcopy(world.result or {})
    wanted = 'forged' if skill == 'forgery' else 'moved' if skill == 'delegation' else 'matched' if skill == 'navigation' else 'killed'
    good = any(p['predicate'] == wanted for p in result.get('supported_findings', []))
    if skill == 'delegation':
        good = good and any(o['key'] == 'delivery_letter' and o['collected'] for o in world.objects.values())
        good = good and not any(e['kind'] == 'concealment' for e in world.journal)
    if skill == 'navigation':
        # The public follow-up objective requires the actual limited account,
        # not just an already available garment comparison.
        good = good and any(r['kind'] == 'testimony' and any(m['basis'] == 'partial_observation' for m in r['content'].get('recollections', []))
                            for r in world.receipts.values())
    return float(good and not result.get('false_findings') and not result.get('unsupported_findings')), result


def reference(case, budget=12):
    """Public-tool reference for feasibility checks, not a training supervisor."""
    world, book = restore(case)
    def act(tool, args):
        action = {'tool': tool, 'args': args}
        result = world.step(tool, args)
        book.observe(action, result)
        return result
    if case.skill == 'forgery':
        for surface in ('stove', 'parlor table'):
            act('search', {'surface': surface})
        action = next(a for a in propose(case.skill, book) if a['tool'] == 'compare')
        act(action['tool'], action['args'])
    elif case.skill in ('witness', 'statement_review'):
        for person in list(book.people.get(book.scene['place']['id'], [])):
            if 'no response' in person['appearance'].lower():
                continue
            act('ask', {'pid': person['id'], 'question': 'What did you personally see?', 'approach': 'reassure'})
            reports = _murder_reports(book)
            if any(any(m['basis'] == 'direct_observation' and 'strikes' in m['text'] for m in r.get('recollections', [])) for r in book.records.values()):
                break
    elif case.skill == 'navigation':
        act('go', {'destination': 'courtyard'})
        act('people_here', {})
        act('ask', {'pid': 'sera', 'question': 'What did you personally see through the hatch?', 'approach': 'reassure'})
        action = next(a for a in propose(case.skill, book) if a['tool'] == 'compare')
        act(action['tool'], action['args'])
    else:
        act('search', {'surface': 'visitors book', 'by': 'anya'})
        action = next(a for a in propose(case.skill, book) if a['tool'] == 'collect')
        act(action['tool'], action['args'])
    reports = [a for a in propose(case.skill, book) if a['tool'] == 'submit_report']
    # Choose a public direct account over a rumor-based candidate in the oracle.
    report = next((a for a in reports if a['args']['findings'] and a['args']['findings'][0]['actor'] != 'dev'), reports[0])
    act('submit_report', report['args'])
    return reward(case.skill, world)
