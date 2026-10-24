"""Public task descriptions. This file contains no correct actors or proof paths."""

TASKS = {
 'lantern_room': {'name':'The Lantern Room','family':'lantern_room','difficulty':'introductory','demo':True,
   'scope':'Investigate the fatal assault at the Pine Lantern. Establish the assailant using acquired physical traces and a first-hand account. You choose whom to question and what to inspect.',
   'success':'A supported attribution of the fatal assault, with no false or unsupported conclusions. A correct guess without acquired support earns zero.'},
 'second_passenger': {'name':'The Second Passenger','family':'second_passenger','difficulty':'intermediate',
   'scope':'Investigate two deaths at the bridge crossing. Establish responsibility for the deaths and whether either passenger was specifically targeted. Distinguish an observed act, the failure mechanism and evidence of intention.',
   'success':'Support both death attributions and the intended-target finding using acquired evidence, with no false or unsupported conclusions.'},
 'bell_before_dawn': {'name':'The Bell Before Dawn','family':'bell_before_dawn','difficulty':'advanced',
   'scope':'Investigate the death in the chapel and the apparently prophetic warning. Establish responsibility for the death, any fabrication of the warning document, and how it was relayed. Foreknowledge alone does not establish participation in a killing.',
   'success':'Support the death attribution, warning fabrication and its transmission with acquired sources. Unresolved supernatural explanations may remain explicit; they are not scored.'},
 'last_witness': {'name': 'The Last Witness', 'family':'mercy_house','difficulty': 'intermediate',
   'scope': 'Investigate the fatal assault. Establish who inflicted it and support the conclusion with physical evidence and an account whose limits you have checked.',
   'success': 'A supported attribution of the fatal assault, with no false or unsupported material conclusions. A correct name without acquired support scores zero.'},
 'borrowed_signature': {'name': 'A Borrowed Signature', 'difficulty': 'intermediate',
   'scope': 'Investigate the origin of the threatening document found during the inquiry. Establish any fabrication using acquired material and comparisons rather than assuming its signature identifies its writer.',
   'success': 'A supported attribution of document fabrication, with no false or unsupported material conclusions.'},
 'brothers_letter': {'name': "A Brother's Letter", 'difficulty': 'advanced',
   'scope': 'Investigate interference with evidence handling. Establish any concealment during delegated searches and recover a sourced explanation. You may decide how to supervise and whom to question.',
   'success': 'Establish the concealed delivery record and the person responsible for concealing it using acquired support. If no concealment occurs, report only the supported handling history; preventing loss earns no automatic reward.'},
 'garden_burials': {'name': 'The Winter Beds', 'difficulty': 'advanced',
   'scope': 'Investigate the reported disturbance at the winter garden. Recover material legally and establish any relocation of human remains using independent records. Ownership of the garden is not proof of responsibility.',
   'success': 'A supported attribution of the relocation, including physical recovery and independent documentary support, with no false or unsupported material conclusions.'},
 'mercy_inquest': {'name': 'The Mercy House Inquest', 'difficulty': 'advanced',
   'scope': 'Reconstruct the fatal assault, assistance, documentary fabrication, grave relocation and historical record alterations. Distinguish established acts from unrelated personal history and leave unresolved matters explicit.',
   'success': 'Establish all material acts within this scope using acquired support and no false accusations. Partial credit reflects supported material coverage; narrative style is not scored.'},
}

ALIASES = {'mira_murder': 'last_witness'}

# Public setup only: no answer actors, hidden documents, witness knowledge or
# explanation of the crime. These can be read before a paid run begins.
BRIEFINGS = {
 'lantern_room': "November, 1900. Snow has closed the road out of the valley. At the inn, an evening of ordinary business has ended with a death in the reading room. You arrive as the district investigator. The people nearby have their own accounts of the evening; you have not yet heard them. Enter the room, establish what you can observe, and decide where the inquiry should lead.",
 'second_passenger': "The coach lies below the old bridge. Two people who expected a short journey have died, and news is travelling faster than anyone has checked it. You arrive at the crossing as the district investigator. Begin with the scene, then follow the route back through the town. What the passengers intended, what other people witnessed and what happened to the coach must be established through the investigation.",
 'bell_before_dawn': "The chapel lamps are still burning after a sudden death. Across the square, people speak of a warning that seemed to arrive before the news. In a small town, a frightening story can become an explanation before anyone has examined it. As the district investigator, you begin at the chapel. Listen carefully, inspect what is actually there, and leave unanswered matters open until you can support a conclusion.",
 'last_witness': "You have returned to Bhairav’s Hollow on leave. Now a physician lies motionless at Mercy House, and your visit has become an investigation. This town belongs to your own remembered life, but familiarity cannot tell you what happened tonight. Start at the scene. Establish the limits of each account and preserve the material you acquire before submitting your report.",
 'borrowed_signature': "A death at Mercy House has brought an alarming document into the inquiry. Words on paper can describe a real event, repeat a rumour or make an accusation. Their presence alone cannot settle which. Your task is to investigate this document’s origin through the people and materials you can actually reach. The room is your starting point; the document’s history is still unknown.",
 'brothers_letter': "The first search after the Mercy House death has already taken place. You are taking up the inquiry while people, papers and responsibilities are still being accounted for. A colleague’s familiarity is useful, but every important discovery needs a record. Decide how to supervise the work, follow the evidence-handling history and distinguish an omission you can establish from one you merely suspect.",
 'garden_burials': "A report of disturbed winter beds has become part of the Mercy House inquiry. The garden is a household’s working ground, not an explanation of what may lie beneath it. As the district investigator, you must reach the place, inspect it lawfully and preserve any material you recover. Check its history through independent records before attributing responsibility.",
 'mercy_inquest': "Bhairav’s Hollow, November 1900. Dr. Mira Sen invited you back to discuss an old family record. By the time you arrive, she is dead at Mercy House. You remember this institution from your sister’s life, and several people here from your own. Those memories explain why the case matters to you; they do not establish anyone’s guilt. Begin at the scene, follow the accounts and documents you acquire, and reconstruct only what the evidence can support.",
}


def task_id(value):
    value = ALIASES.get(value, value)
    if value not in TASKS:
        raise ValueError('Unknown TASK_ID')
    return value


def description(value):
    key = task_id(value)
    return {'task_id': key, 'family':TASKS[key].get('family','mercy_house'), **TASKS[key], 'briefing':BRIEFINGS[key],
            'report_contract': 'Choose your own findings: actor, predicate, object and acquired source IDs. Use the exact predicate enum in the tool schema. Acquired object IDs, observed full names and concise object labels are accepted. assisted means knowingly facilitated the fatal incident involving the named victim; aided means help given to the victim. commissioned distinguishes an orderer from the carrier; matched describes physical objects and does not identify a killer. Hypotheses belong in narrative.',
            'limits': {'model_replies': 40, 'calls_per_reply': 10, 'wall_seconds': 600}}
