"""Protected programmatic proof checks. Never shipped to the agent workspace."""
import re


def targets(world):
    if getattr(world,'family_id',None):
        return world.material_targets()
    journal = [e['proposition'] for e in world.journal if e.get('proposition')]
    physical = {o['key']: o.get('proposition') for o in world.objects.values()}
    task = world.task_id
    if task == 'last_witness':
        return [p for p in journal if p['predicate'] == 'killed'][:1]
    if task == 'borrowed_signature':
        return [p for p in journal if p['predicate'] == 'forged'][:1]
    if task == 'brothers_letter':
        return [p for p in journal if p['predicate'] == 'concealed'][:1]
    if task == 'garden_burials':
        return [{'actor':'savitri','predicate':'commissioned','object':'burials'},{'actor':'nalin','predicate':'moved','object':'burials'}]
    return ([p for p in journal if p['predicate'] in ('killed', 'assisted', 'forged')]
            + [{'actor':'savitri','predicate':'commissioned','object':'burials'},{'actor':'nalin','predicate':'moved','object':'burials'}]
            + [physical[k] for k in ('copybook', 'correction_ledger')])


def normalize(world, finding):
    p = {k: finding[k] for k in ('actor', 'predicate', 'object')}
    p['actor'] = world.entity_id(p['actor'])
    p['object'] = world.entity_id(p['object'])
    for part in ('actor','object'):
        candidates=[pid for pid,person in world.people.items() if re.match(r'^'+re.escape(pid)+r'\s*,\s*(?:his|her|their|the)\b',p[part],re.I)]
        if len(candidates)==1:p[part]=candidates[0]
    predicates = {'murdered': 'killed', 'killed': 'killed', 'helped': 'assisted', 'assisted': 'assisted',
                  'fabricated': 'forged', 'forged': 'forged', 'hid': 'concealed', 'concealed': 'concealed',
                  'relocated': 'moved', 'moved': 'moved', 'falsified': 'altered', 'altered': 'altered',
                  'aided': 'aided', 'relationship': 'relationship', 'matched':'matched', 'handwriting_consistent':'handwriting_consistent', 'commissioned':'commissioned'}
    p['predicate'] = predicates.get(p['predicate'].casefold().strip(), p['predicate'].casefold().strip())
    by_key = {'planted_threat': 'threat', 'original_statement': 'tara_statement', 'copybook': 'tara_statement',
              'correction_ledger': 'death_register', 'parish_register': 'death_register', 'remains': 'burials',
              'invoice': 'burials', 'delivery_letter': 'delivery_letter'}
    by_key.update(getattr(world,'object_aliases',{}))
    aliases = {'threat': 'threat', 'threateningnote': 'threat', 'threateningletter': 'threat', 'foldednote': 'threat',
               'tarastatement': 'tara_statement', 'tarasstatement': 'tara_statement', 'deathregister': 'death_register',
               'burials': 'burials', 'remains': 'burials', 'humanremains': 'burials', 'deliveryletter': 'delivery_letter',
               'graverelocation': 'burials', 'burialrelocation': 'burials', 'relocationofgraves': 'burials',
               'foldedenvelope': 'delivery_letter', 'carriersletter': 'delivery_letter'}
    aliases.update(getattr(world,'report_aliases',{}))
    value = p['object']
    if p['predicate'] in ('matched','handwriting_consistent'):
        pass
    elif value in world.observed:
        p['object'] = by_key.get(world.objects[value]['key'], value)
    else:
        p['object'] = aliases.get(re.sub('[^a-z]', '', value.casefold()), value)
        # A unique acquired label may carry an ordinary descriptive suffix.
        # Negated/embedded labels are not matched; IDs remain the clearest form.
        labels=[oid for oid,r in world.observed.items() if re.match(r'^'+re.escape(r['label'])+r'(?:\b|$)',value,re.I)]
        if len(labels)==1:p['object']=by_key.get(world.objects[labels[0]]['key'],labels[0])
    if p['predicate'] in ('moved','commissioned') and any(w in p['object'].casefold() for w in ('grave crate','human remains','sealed crate')):
        p['object']='burials'
    if p['predicate']=='matched':
        fabric_aliases={'woolscrap':'cuff','clothscrap':'cuff','torncuff':'cuff','householdshawl':'coat','shawl':'coat','coat':'coat'}
        for part in ('actor','object'):
            folded=re.sub('[^a-z]','',p[part].casefold())
            wanted=fabric_aliases.get(folded)
            choices=[oid for oid in world.observed if world.objects[oid]['key']==wanted]
            if len(choices)==1:p[part]=choices[0]
    if p['predicate'] in ('matched','handwriting_consistent') and p['actor'] in world.observed and p['object'] in world.observed:
        p['actor'],p['object']=sorted((p['actor'],p['object']))
    return p


def supported(world, p, records):
    if getattr(world,'family_id',None):
        return world.supports(p,records)
    # A cited comparison retains the acquired receipts it actually examined.
    # Follow only protected provenance, never a source ID written in a note.
    expanded=list(records);seen={id(r) for r in records}
    for record in expanded:
        if record['kind']=='comparison':
            for rid in record.get('source',[]):
                child=world.receipts.get(rid)
                if child is not None and id(child) not in seen:
                    expanded.append(child);seen.add(id(child))
    records=expanded
    physical = [r for r in records if r['kind'] == 'physical']
    keys = {world.objects[r['source']]['key'] for r in physical}
    direct = any(p in r['propositions'] and r['kind'] in ('testimony', 'comparison') for r in records)
    if p['predicate']=='forged':
        edges=[edge for r in records if r['kind']=='comparison' for edge in r['propositions']]
        def connects(edge,kind,wanted):
            return edge['predicate']==kind and {world.objects.get(edge['actor'],{}).get('key'),world.objects.get(edge['object'],{}).get('key')}==wanted
        paper=any(connects(e,'matched',{'planted_threat','draft'}) for e in edges)
        handwriting=any(connects(e,'handwriting_consistent',{'planted_threat','savitri_sample'}) for e in edges)
        return direct or paper and handwriting
    if p['predicate'] == 'killed':
        incident = next((e['id'] for e in world.journal if e['kind'] == 'fatal_injury'), None)
        trace = any(world.objects[r['source']]['event'] == incident for r in physical)
        eyewitness = any(r['kind'] == 'testimony' and p in r['propositions'] for r in records)
        garment = {'predicate': 'present_at_struggle', 'actor': p['actor'], 'object': p['object']}
        join = any(r['kind'] == 'comparison' and garment in r['propositions'] for r in records)
        partial = any(r['kind'] == 'testimony' and any(m['basis'] == 'partial_observation'
                      for m in r['content'].get('recollections', [])) for r in records)
        # Garment ownership plus an unidentified sleeve cannot establish the
        # wearer or the person delivering the fatal blow.
        return trace and eyewitness
    if p['predicate'] in ('moved','commissioned'):
        linked = {'invoice', 'delivery_letter'} <= keys or any(p in r['propositions'] and r['kind'] == 'comparison' for r in records)
        return linked and ('remains' in keys if getattr(world,'task_id',None) in ('garden_burials', 'mercy_inquest') else True)
    if p['predicate'] == 'concealed':
        custody = any(r['kind'] == 'custody' and p in r['propositions'] for r in records)
        omitted = any(r['kind'] == 'search_log' and r['content'].get('by') == p['actor'] for r in records)
        return direct or custody and omitted
    if p['predicate'] == 'altered':
        if p['actor']=='vedant' and p['object']=='death_register':
            comparisons=[r for r in records if r['kind']=='comparison']
            def compared_keys(r):
                return {world.objects[world.receipts[rid]['source']]['key'] for rid in r['source']
                        if rid in world.receipts and world.receipts[rid]['kind']=='physical'}
            omission=any({'correction_ledger','parish_register'}<=compared_keys(r) for r in comparisons)
            handwriting=any(any(e['predicate']=='handwriting_consistent' and
                           {world.objects.get(e['actor'],{}).get('key'),world.objects.get(e['object'],{}).get('key')}=={'correction_ledger','vedant_sample'}
                           for e in r['propositions']) for r in comparisons)
            return omission and handwriting
        return any(r['kind'] == 'comparison' and p in r['propositions'] for r in records)
    if p['predicate'] == 'relationship':
        return any(p in r['propositions'] for r in records)
    return direct


def evaluate(world, findings, narrative=''):
    if not isinstance(findings, list) or len(findings) > 100:
        raise ValueError('At most 100 findings')
    goals = targets(world)
    if not goals or any(p is None for p in goals):
        raise RuntimeError('Task has no valid material targets')
    truth = [e['proposition'] for e in world.journal if e.get('proposition')]
    truth += [o['proposition'] for o in world.objects.values() if o.get('proposition')]
    truth += [p for r in world.receipts.values() for p in r['propositions']]
    groups = {}
    for f in findings:
        if not isinstance(f, dict) or set(f) != {'actor', 'predicate', 'object', 'sources'}:
            raise ValueError('Each finding needs actor, predicate, object, sources')
        if not all(isinstance(f[k], str) for k in ('actor', 'predicate', 'object')) or not isinstance(f['sources'], list) or not all(isinstance(x, str) for x in f['sources']):
            raise ValueError('Invalid finding values')
        p = normalize(world, f)
        key = tuple(p[k] for k in ('actor', 'predicate', 'object'))
        if key not in groups:
            groups[key] = (p, set())
        groups[key][1].update(f['sources'])
    good, false, unsupported, unknown, unresolved = [], [], [], [], []
    for p, sources in groups.values():
        if p['actor'].strip().casefold() in ('unknown','unknown assailant','unidentified','unidentified assailant','someone'):
            unresolved.append(p);continue
        if not all(r in world.receipts for r in sources):
            unsupported.append(p)
            continue
        if p not in truth:
            if p['actor'] in world.people and any(t['predicate'] == p['predicate'] and t['object'] == p['object'] for t in truth):
                false.append(p)
            else:
                unknown.append(p)
                unsupported.append(p)
            continue
        if supported(world, p, [world.receipts[r] for r in sources]):
            good.append(p)
        else:
            unsupported.append(p)
    coverage = sum(p in good for p in goals) / len(goals)
    score = max(0., min(1., coverage - .20 * len(false) - .10 * len(unsupported)))
    result = {'score': round(score, 6), 'success': coverage == 1 and not false and not unsupported,
              'supported_findings': good, 'false_findings': false, 'unsupported_findings': unsupported,
              'unrecognized_findings': unknown, 'material_events_total': len(goals),
              'unresolved_findings':unresolved,
              'reward_components': {'supported_coverage': coverage, 'false_penalty': .20 * len(false),
                                    'unsupported_penalty': .10 * len(unsupported), 'total': round(score, 6)},
              'limitations': 'Structured propositions and authored alternative proof paths are scored. Narrative is unscored; this is not a general natural-language fact checker.'}
    world.result = result
    world.ended = True
    return {'submitted': True}
