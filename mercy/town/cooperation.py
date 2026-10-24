"""Bounded cooperation for legal inquiry actions, never a truth/grading shortcut.

The LLM may withhold initially. Repeated corroborated requests can record only
already-eligible external observations or recover a specifically authorized item.
Self-incriminating recollections and partial/hearsay accounts are never forced.
"""
from .boundaries import topics

COOPERATION_RULE = (
    'Repeated evidence-backed, reassuring questions can obtain a formal account of '
    'a witness’s eligible first-hand observations. Formal access and authorized '
    'custody requests also resolve after repeated legitimate attempts. These '
    'procedures do not create memories or compel confessions.'
)
LIMIT = 3


def supported_request(world, records):
    return any(world.receipts[r]['kind'] in ('physical', 'comparison') for r in records)


def interview(world, pid, question, approach, shown, eligible, decision, allowed):
    if approach != 'reassure' or not supported_request(world, shown):
        return decision
    if not set(topics(question)) & {'mira', 'movements', 'timeline', 'source_of_account', 'clarification', 'vantage_point', 'papers', 'burials'}:
        return decision
    state = world.states[pid]
    counts = state.setdefault('corroborated_refusals', {})
    selected = set(decision.get('recall_ids', [])) if decision['action_id'] in ('answer', 'return_letter') else set()
    forced = []
    for memory in state['memories']:
        p = memory.get('proposition')
        if (memory['id'] not in eligible or memory['source'] != 'direct_observation'
                or not p or p['actor'] == pid or memory.get('event') is None):
            continue
        mid = memory['id']
        if mid in selected:
            counts[mid] = 0
        else:
            counts[mid] = counts.get(mid, 0) + 1
            if counts[mid] >= LIMIT:
                forced.append(mid)
    handover = False
    if 'return_letter' in allowed and decision['action_id'] != 'return_letter':
        state['inventory_refusals'] = state.get('inventory_refusals', 0) + 1
        handover = state['inventory_refusals'] >= LIMIT
    if not forced and not handover:
        return decision
    selected.update(forced)
    decision = dict(decision, action_id='return_letter' if handover else 'answer', recall_ids=sorted(selected))
    texts = [m['text'] for m in state['memories'] if m['id'] in selected]
    decision['speech'] = ('A formal account is recorded: ' + ' '.join(texts)) if texts else 'After a formal inventory request, I am handing over the unreported envelope.'
    world.audit.append('bounded_cooperation', {'person': pid, 'memory_ids': forced, 'authorized_handover': handover})
    return decision


def access(world, pid, granted):
    if granted:
        return True, False
    state = world.states[pid]
    # An actual acquired incident trace is necessary; a self-written note cannot
    # establish inquiry authority. Presence and ownership were checked by caller.
    trace = any(r['kind'] == 'physical' and world.objects[r['source']].get('event')
                for r in world.receipts.values())
    if not trace:
        return False, False
    state['formal_access_refusals'] = state.get('formal_access_refusals', 0) + 1
    formal = state['formal_access_refusals'] >= LIMIT
    if formal:
        world.audit.append('formal_access', {'person': pid, 'authority': 'fictional district inquiry procedure'})
    return formal, formal
