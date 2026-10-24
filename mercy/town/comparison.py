"""Protected compositional examinations: useful partial observations, no verdicts."""


def compare(world, records):
    if not isinstance(records, list) or not 2 <= len(records) <= 6 or not all(isinstance(r, str) and r in world.receipts for r in records):
        raise ValueError('Compare two to six acquired records')
    world.clock += 4
    selected = [world.receipts[r] for r in records]
    objects = {world.objects[r['source']]['key']: r['source'] for r in selected if r['kind'] == 'physical'}
    keys = set(objects)
    observations, props = [], []
    def link(predicate, first, second):
        actor, obj = sorted((objects[first], objects[second]))
        props.append({'predicate': predicate, 'actor': actor, 'object': obj})
    if {'planted_threat', 'draft'} <= keys:
        observations.append('The threat sheet and unused offcut have matching torn edges; their fibers continue across the join. This links the two pieces of paper, not a writer.')
        link('matched', 'planted_threat', 'draft')
    if {'planted_threat', 'savitri_sample'} <= keys:
        observations.append('Letter strokes on the threat agree with those on the independently signed shopping note, including the overwritten lower-case d. The signature on the threat itself does not establish authorship.')
        link('handwriting_consistent', 'planted_threat', 'savitri_sample')
    if {'planted_threat', 'draft', 'savitri_sample'} <= keys:
        props.append({'predicate': 'forged', 'actor': 'savitri', 'object': 'threat'})
    if {'cuff', 'coat'} <= keys:
        observations.append('The wool scrap’s torn edge fits the missing cuff of the tagged shawl; the weave and old repair stitches continue across the join. There are recent blood marks on the joined edge. This links the garment to the struggle, not by itself the fatal blow.')
        link('matched', 'cuff', 'coat')
    if {'invoice', 'delivery_letter'} <= keys:
        observations.append('The payment amount, carrier name, and destination agree across the two separately retained papers. The payer and the carrier are different people.')
        props.extend([{'predicate': 'moved', 'actor': 'savitri', 'object': 'burials'},
                      {'predicate': 'commissioned', 'actor': 'savitri', 'object': 'burials'},
                      {'predicate': 'moved', 'actor': 'nalin', 'object': 'burials'}])
    if {'original_statement', 'copybook'} <= keys:
        observations.append('The household copy omits the original sentence about the matron refusing release. Comparing the two texts alone does not identify the person who made the change.')
    if {'copybook', 'savitri_sample'} <= keys:
        observations.append('The amended lines in the household copy agree in handwriting with the independently signed shopping note.')
        link('handwriting_consistent', 'copybook', 'savitri_sample')
    if {'original_statement', 'copybook', 'savitri_sample'} <= keys:
        props.append({'predicate': 'altered', 'actor': 'savitri', 'object': 'tara_statement'})
    if {'correction_ledger', 'parish_register'} <= keys:
        observations.append('Nera’s certified parish entry has no counterpart in the replacement death register. The working ledger instructs that entry to be removed; its inside cover is signed V. Rao.')
        props.append({'predicate': 'altered', 'actor': 'vedant', 'object': 'death_register'})
    return world._receipt('comparison', {'compared': records, 'observation': ' '.join(observations) or
        'You lay out the records. Their wording and provenance remain distinct; no specific material correspondence is established by this selection.'}, props, records)
