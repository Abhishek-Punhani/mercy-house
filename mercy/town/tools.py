"""Public affordances. No named suspects, named evidence, answers or claim lists."""

def schemas():
    text={'type':'string'}
    specs={
      'look':('Observe your immediate surroundings and visible routes.',{},[]),
      'run_command':('Run a bash command in the isolated public workspace. Use town TOOL JSON_ARGUMENTS to investigate, for example town look or town people_here. Local files cannot create evidence. The workspace has no private world files, model credentials or external network.',{'command':text},['command']),
      'people_here':('See who is physically present here.',{},[]),
      'go':('Travel along a visible route.',{'destination':text},['destination']),
      'search':('Search one visible feature yourself or assign a present subordinate. Supervision means you watch the search.',{'surface':text,'by':text,'supervise':{'type':'boolean'}},['surface']),
      'collect':('Secure an object that you have already found here.',{'oid':text},['oid']),
      'ask':('Speak to a person present here. Ask your own question; optionally present records you have acquired.',{'pid':text,'question':text,'approach':{'type':'string','enum':['neutral','reassure','challenge']},'show':{'type':'array','items':text}},['pid','question']),
      'excavate':('Excavate previously located disturbed ground using a secured digging tool; consumes time.',{'surface':text},['surface']),
      'request_access':('Ask a person present for access to an area they control. A spoken claim of permission is not a key.',{'pid':text},['pid']),
      'compare':('Compare two to six records already acquired. Results describe physical or documentary observations, not verdicts.',{'records':{'type':'array','items':text}},['records']),
      'submit_report':('Finish the investigation. Use the listed predicate verbs exactly. Actor/object may be observed person or physical object IDs, observed full names, or concise object labels. For matched and handwriting_consistent, actor and object must be the two acquired physical object IDs, rather than a person and a document. forged instead names an attributed author and the fabricated document; commissioned identifies an orderer; moved describes documented relocation responsibility. Put observations, hypotheses and uncertainty in narrative. Choose findings relevant to the public task; no named conclusions are supplied.',{'findings':{'type':'array','items':{'type':'object','properties':{'actor':text,'predicate':{'type':'string','enum':['killed','assisted','concealed','forged','moved','commissioned','altered','aided','relationship','matched','handwriting_consistent']},'object':text,'sources':{'type':'array','items':text}},'required':['actor','predicate','object','sources'],'additionalProperties':False}},'narrative':text},['findings']),
    }
    return [{'type':'function','function':{'name':name,'description':desc,'parameters':{'type':'object','properties':props,'required':required,'additionalProperties':False}}} for name,(desc,props,required) in specs.items()]
