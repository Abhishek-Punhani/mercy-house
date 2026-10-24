"""Programmatic proof rules for the original case families. Protected code."""
from .family_world import prop


def compare(world,records):
    if not isinstance(records,list) or not 2<=len(records)<=6 or any(r not in world.receipts for r in records):raise ValueError('Compare two to six acquired records')
    world.clock+=4
    material={world.objects[world.receipts[r]['source']]['key']:world.receipts[r]['source'] for r in records if world.receipts[r]['kind']=='physical'}
    keys=set(material);observations=[];props=[]
    def link(kind,a,b):
        first,second=sorted((material[a],material[b]));props.append(prop(kind,first,second))
    if world.family_id=='second_passenger':
        if {'brake_trace','inspection'}<=keys:
            observations.append('The fresh cut passes through the retaining section shown intact on the pre-departure inspection card. With that section severed the pawl cannot hold under load. The damage is a disabling cut, not ordinary wear; this identifies a failure mechanism, not the person who caused it.')
            props.append(prop('mechanism','coach_brake','disabled_retainer'))
        if {'route_slip','dispatch_ledger'}<=keys:
            name=world.people[world.case['primary']]['name']
            observations.append('The dispatch code in the instruction resolves in the countersigned departure ledger to '+name+'. The other passenger has a different dispatch code. This identifies the addressed packet, not the note’s author.')
            props.append(prop('addressed','route_slip',world.case['primary']))
        author=world.mechanism['route_author'];sample='sample_'+author if author else ''
        if {'route_slip',sample}<=keys:
            observations.append('The lettering in the route instruction agrees with the independently signed business receipt, including the joined final r.')
            link('handwriting_consistent','route_slip',sample)
        if {'route_slip','dispatch_ledger',sample}<=keys:props.append(prop('targeted',author,world.case['primary']))
    if world.family_id=='bell_before_dawn':
        if {'tonic','reference_vial','dispensary'}<=keys:
            observations.append('The retained-paper assay described in the dispensing record distinguishes the bottle residue from the sealed ordinary cordial. In this fictional dispensary it matches ironleaf preparation, a harmful adulterant. This establishes adulteration, not who added it; no real-world toxicology or dosage claim is made.')
            props.append(prop('adulterated','tonic','ironleaf'))
        author=world.mechanism['warning_author'];paper='paper_'+author if author else '';sample='sample_'+author if author else ''
        if {'warning',paper}<=keys:
            observations.append('The warning sheet and unused offcut have matching toothed tears, with fibres continuing across the join. Paper ownership alone does not establish authorship.')
            link('matched','warning',paper)
        if {'warning',sample}<=keys:
            observations.append('The warning’s close lettering and doubled final strokes agree with the independently signed account.')
            link('handwriting_consistent','warning',sample)
        if {'warning',paper,sample}<=keys:props.append(prop('forged',author,'warning_letter'))
        if {'warning','delivery'}<=keys:
            observations.append('The docket places delivery of the sheet at the inn before the chapel visit. Its wording matches the warning pinned beside the counter. Timing alone does not establish murder participation.')
    return world._receipt('comparison',{'compared':records,'observation':' '.join(observations) or 'No specific correspondence is established by these records. Their wording and provenance remain distinct.'},props,records)


def supports(world,p,records):
    # A comparison receipt preserves its own acquired provenance. Citing that
    # receipt can therefore cite its physical dependencies without repeating IDs.
    expanded=list(records);seen={id(r) for r in records}
    for r in expanded:
        if r['kind']=='comparison':
            for rid in r.get('source',[]):
                child=world.receipts.get(rid)
                if child is not None and id(child) not in seen:expanded.append(child);seen.add(id(child))
    keys={world.objects[r['source']]['key'] for r in expanded if r['kind']=='physical'}
    def has(value,kind=None):return any((kind is None or r['kind']==kind) and value in r['propositions'] for r in expanded)
    def edge(kind,a,b):
        return any(r['kind']=='comparison' and any(e['predicate']==kind and {world.objects.get(e['actor'],{}).get('key'),world.objects.get(e['object'],{}).get('key')}=={a,b} for e in r['propositions']) for r in expanded)
    if p['predicate']=='killed':
        body='body_'+p['object']
        if body not in keys:return False
        if world.family_id=='lantern_room':return 'lamp' in keys and has(p,'testimony')
        if world.family_id=='second_passenger':
            return {'brake_trace','inspection'}<=keys and has(prop('mechanism','coach_brake','disabled_retainer'),'comparison') and has(prop('tampered',p['actor'],'coach_brake'),'testimony')
        return {'tonic','reference_vial','dispensary'}<=keys and has(prop('adulterated','tonic','ironleaf'),'comparison') and (has(prop('administered',p['actor'],'tonic'),'testimony') or has(p,'testimony'))
    if p['predicate']=='targeted':
        return has(p,'comparison') or has(prop('addressed','route_slip',p['object']),'comparison') and edge('handwriting_consistent','route_slip','sample_'+p['actor'])
    if p['predicate']=='forged':return edge('matched','warning','paper_'+p['actor']) and edge('handwriting_consistent','warning','sample_'+p['actor'])
    if p['predicate']=='relayed':return {'warning','delivery'}<=keys and has(p,'testimony')
    return has(p,'testimony') or has(p,'comparison')
