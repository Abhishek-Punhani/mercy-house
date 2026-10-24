"""Generic candidate coverage from public observations; contains no case answers.

An LLM shortlist can omit the useful question or visible feature entirely. This
enumerates ordinary visible actions, never hidden locations, people or evidence.
Reports still come from the proposer, not an answer file or private proof graph.
"""
import json


def augment(book, proposals):
    candidates = list(proposals)
    here = book.scene.get('place', {}).get('id', '')
    people = book.people.get(here, [])
    candidates.extend([{'tool': 'look', 'args': {}}, {'tool': 'people_here', 'args': {}}])
    for route in book.scene.get('exits', []):
        candidates.append({'tool': 'go', 'args': {'destination': route['id']}})
    for surface in book.scene.get('searchable_features', []):
        candidates.append({'tool': 'search', 'args': {'surface': surface}})
        for person in people:
            if 'constable' in person.get('occupation', ''):
                for supervised in (False, True):
                    candidates.append({'tool': 'search', 'args': {'surface': surface, 'by': person['id'], 'supervise': supervised}})
    for person in people:
        for approach in ('neutral', 'reassure', 'challenge'):
            candidates.append({'tool': 'ask', 'args': {'pid': person['id'], 'approach': approach,
                'question': 'Please take your time. What did you personally see, what did you hear, and what are you uncertain about?'}})
    physical = [r for r in book.records.values() if 'object_id' in r]
    for record in physical:
        if record.get('where') == here and record['object_id'] not in book.secured:
            candidates.append({'tool': 'collect', 'args': {'oid': record['object_id']}})
    if len(physical) >= 2:
        candidates.append({'tool': 'compare', 'args': {'records': [r['record_id'] for r in physical[:6]]}})
        documents = [r for r in physical if any(w in (r.get('label', '') + ' ' + r.get('description', '')).lower()
                                              for w in ('paper', 'letter', 'note', 'register', 'copybook', 'writing'))]
        if len(documents) >= 2:
            candidates.append({'tool': 'compare', 'args': {'records': [r['record_id'] for r in documents[:6]]}})
        fabrics = [r for r in physical if any(w in r.get('description', '').lower() for w in ('wool', 'cloth', 'cuff', 'weave'))]
        if len(fabrics) >= 2:
            candidates.append({'tool': 'compare', 'args': {'records': [r['record_id'] for r in fabrics[:6]]}})
    result, seen = [], set()
    for action in candidates:
        key = json.dumps(action, sort_keys=True)
        if key not in seen:
            result.append(action);seen.add(key)
    return result
