"""Protected deterministic reconstruction of recorded character action tapes."""
import json
from pathlib import Path
from .world import Town
from .agents import FixtureAgent
from .tasks import task_id


class ReferenceActors(FixtureAgent):
    """Deterministic cooperative policy for reference/gates, not an LLM result."""
    def decide(self, person_id, packet):
        allowed = {a['action_id'] for a in packet['available_actions']}
        eligible = packet.get('interaction_context', {}).get('eligible_recall_ids', [])
        if 'return_letter' in allowed:
            return {'action_id': 'return_letter', 'speech': 'I kept the envelope in my coat. It names my brother. Here it is.', 'recall_ids': eligible}
        if 'grant_access' in allowed:
            return {'action_id': 'grant_access', 'speech': 'You may examine the room. Please leave a record of what you take.', 'recall_ids': []}
        if 'answer' in allowed:
            return {'action_id': 'answer', 'speech': 'I can describe what I remember. Please distinguish it from anything I only heard.', 'recall_ids': eligible}
        return super().decide(person_id, packet)


def build(task, seed=7, agents=None):
    key = task_id(task)
    if type(seed) is not int or not -(2**63) <= seed < 2**63:
        raise ValueError('SEED must fit a signed 64-bit integer')
    if key in ('lantern_room','second_passenger','bell_before_dawn'):
        from .family_world import build_family
        return build_family(key,seed,agents)
    world = Town(seed, ReferenceActors())
    tape_file = Path(__file__).with_name('data') / 'incident-planted.json'
    tape = json.loads(tape_file.read_text())
    for turn in tape['turns']:
        world.tick = turn['tick']
        pid = turn['person']
        allowed = world.prelude_actions(pid)
        if turn['action'] not in {a['action_id'] for a in allowed}:
            raise RuntimeError('Recorded incident no longer matches the engine')
        world.commit(pid, {'action_id': turn['action'], 'speech': '', 'recall_ids': []}, allowed)
    world.arrive()
    # A separately scoped checkpoint: a recorded first search has already happened.
    if key == 'brothers_letter':
        world.step('go', {'destination': 'hall'})
        world.step('search', {'surface': 'visitors book', 'by': 'kabir'})
        world.step('go', {'destination': 'archive'})
    world.task_id = key
    world.incident_provenance = tape['provenance']
    world.agents = agents or ReferenceActors()
    return world
