"""TRUSTED offline curriculum using actual Town tools and its existing verifier.

This is a narrow fabrication checkpoint, not five tasks or whole-case training.
Fixture actors, a public rule-based proposer, and the same authored case are
explicit experimental limitations. Never copy this module into the actor image.
"""
from copy import deepcopy
import random
import re

from mercy.town.agents import FixtureAgent
from mercy.town.world import Town
from .public import Notebook


def checkpoint(seed):
    world = Town(seed, FixtureAgent())
    world.simulate(4)
    opening = world.arrive()
    tape = []

    def step(tool, args):
        action = {'tool': tool, 'args': args}
        observation = world.step(tool, args)
        if 'error' in observation:
            raise RuntimeError('Curriculum setup action failed')
        tape.append((action, observation))

    step('search', {'surface': 'desk'})
    for destination in ('hall', 'courtyard', 'square', 'das_house'):
        step('go', {'destination': destination})
    step('people_here', {})
    # Different starting progress, constructed through real acquisition actions.
    # The seed/hidden progress selector is never passed to the policy.
    progress = random.Random(seed ^ 0xA17).randrange(4)
    for bit, surface in ((1, 'stove'), (2, 'parlor table')):
        if progress & bit:
            step('search', {'surface': surface})
    snapshot = world.export_private()
    return snapshot, opening, tape, progress


def restore(prepared):
    snapshot, opening, tape, _ = prepared
    world = Town.restore(snapshot, FixtureAgent())
    notebook = Notebook(opening)
    for action, observation in tape:
        notebook.observe(action, observation)
    # The current exercise budget starts at the checkpoint, not the earlier trip.
    return world, notebook


def propose(notebook):
    """Cheap public-information proposals. This is NOT an LLM or learned reasoning.

    The exercise asks about the threatening letter's origin. A simple signature
    heuristic suggests a writer; only the real verifier can decide support.
    All searches/comparisons and premature reports remain candidate choices.
    """
    candidates = [{'tool': 'look', 'args': {}}, {'tool': 'people_here', 'args': {}}]
    for surface in notebook.scene.get('searchable_features', []):
        candidates.append({'tool': 'search', 'args': {'surface': surface}})
    physical = [r for r in notebook.records.values() if 'object_id' in r]
    if len(physical) >= 2:
        candidates.append({'tool': 'compare', 'args': {'records': [r['record_id'] for r in physical[:6]]}})
    signatures = []
    for record in physical:
        signatures.extend(re.findall(r'\b([A-Z])\.\s+([A-Z][a-z]+)\b', record.get('description', '')))
    people = [p for group in notebook.people.values() for p in group]
    possible = {p['id'] for p in people for first, last in signatures
                if p['name'].split()[0].startswith(first) and p['name'].split()[-1] == last}
    findings = []
    if len(possible) == 1:
        findings = [{'actor': next(iter(possible)), 'predicate': 'forged', 'object': 'threat',
                     'sources': list(notebook.records)}]
    candidates.append({'tool': 'submit_report', 'args': {'findings': findings,
                       'narrative': 'A document-origin finding based on the acquired records; other matters remain outside this exercise.'}})
    return candidates


def terminal_reward(world):
    """Post-episode task-scoped reward; leaves Town.submit and its score unchanged."""
    result = deepcopy(world.result or {})
    # No actor name or target list is supplied to the selector/proposer.
    success = any(p['predicate'] == 'forged' and p['object'] == 'threat'
                  for p in result.get('supported_findings', []))
    reward = float(success and not result.get('false_findings') and not result.get('unsupported_findings'))
    return reward, result
