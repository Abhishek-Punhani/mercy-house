"""Protected case generator. Never install this module in an agent workspace."""
import random

CHARACTERS = {
    'savitri': {'name': 'Savitri Das', 'background': 'Leena’s mother; former matron. Comforted the detective after Tara’s death.', 'goal': 'Keep her part in the ninth-ward confinement secret.', 'secret': 'Participated in the murder and its concealment; experiences intrusive voices.'},
    'vedant': {'name': 'Professor Vedant Rao', 'background': 'Scholar of acoustics, wheelchair user, designer of Mercy House’s speaking tubes and archive.', 'goal': 'Protect his reputation and preserve his experiments.', 'secret': 'Helped suppress the register and knowingly assisted the murder.'},
    'dev': {'name': 'Dev Malik', 'background': 'Gravedigger and former caretaker; distrusted by the town.', 'goal': 'Clear his name without exposing unauthorized grave openings.', 'secret': 'Returned possessions from unnamed graves; attempted to save Mira.'},
    'kabir': {'name': 'Kabir Rao', 'background': 'Your trusted subordinate; you once saved his life.', 'goal': 'Protect his brother Nalin.', 'secret': 'Removed an envelope after the murder to hide his brother’s illicit delivery.'},
    'leena': {'name': 'Leena Das', 'background': 'Your former partner; Savitri’s daughter.', 'goal': 'Protect her privacy and get Mira’s findings heard.', 'secret': 'Had an affair with Mira and supplied restricted letters.'},
    'raghav': {'name': 'Raghav Sethi', 'background': 'Former director. You blame him for your sister Tara’s death.', 'goal': 'Avoid exposure of institutional confinement.', 'secret': 'Ordered confinement twelve years ago, but did not kill Mira.'},
    'ishan': {'name': 'Ishan Vale', 'background': 'A medium shunned by the town.', 'goal': 'Understand object-bound sensory fragments.', 'secret': 'Perceptions can be genuine but lack identity and temporal context.'},
    'anya': {'name': 'Anya Paul', 'background': 'Junior investigator; questions your preferred theory.', 'goal': 'Preserve originals and distinguish independent sources.', 'secret': 'No concealed wrongdoing.'},
}

# Public claims describe the required reporting vocabulary, not their truth values.
CLAIMS = {
 'savitri_killed_mira': 'Savitri inflicted Mira’s fatal injury.',
 'vedant_killed_mira': 'Vedant inflicted Mira’s fatal injury.',
 'savitri_assisted_murder': 'Savitri knowingly held the corridor door for the fatal assailant; she was not the person who struck Mira.',
 'vedant_assisted_murder': 'Vedant knowingly held the corridor door for the fatal assailant; he was not the person who struck Mira.',
 'vedant_altered_register': 'Vedant altered the death-register copy.',
 'savitri_forged_threat': 'Savitri forged Dev’s supposed threat letter.',
 'savitri_moved_bodies': 'Savitri arranged relocation of bodies into Dev’s garden.',
 'kabir_removed_letter': 'Kabir removed the carrier’s letter to protect Nalin.',
 'leena_mira_affair': 'Leena concealed an affair with Mira.',
 'dev_aided_mira': 'Dev’s bloodstained sleeve resulted from an attempt to aid Mira.',
 'raghav_confined_tara': 'Raghav ordered Tara confined in the ninth ward.',
 'savitri_edited_statement': 'Savitri altered the copy of Tara’s statement.',
 'vedant_killed_guide': 'Vedant arranged guide Harun’s killing to conceal the relocation.',
 'elsie_natural_death': 'Elsie died from her documented illness, not this murder conspiracy.',
 'ghost_influenced_pair': 'An object-bound entity influenced Savitri and Vedant, without eliminating their capacity to choose.',
 'ghost_caused_all_deaths': 'The entity directly caused every death.',
 'dev_killed_mira': 'Dev killed Mira.',
 'raghav_killed_mira': 'Raghav killed Mira.',
 'kabir_killed_mira': 'Kabir killed Mira.',
 'leena_killed_mira': 'Leena killed Mira.',
}

TASKS = {
 'mira_murder': {'level': 'introductory', 'claims': ['savitri_killed_mira','vedant_killed_mira','savitri_assisted_murder','vedant_assisted_murder','dev_aided_mira','savitri_forged_threat'], 'budget': 90},
 'garden_burials': {'level': 'intermediate', 'claims': ['savitri_moved_bodies','dev_aided_mira','vedant_killed_guide'], 'budget': 90},
 'broken_loyalties': {'level': 'intermediate', 'claims': ['kabir_removed_letter','leena_mira_affair','raghav_confined_tara','savitri_edited_statement'], 'budget': 90},
 'ninth_ward': {'level': 'advanced', 'claims': ['ghost_influenced_pair','ghost_caused_all_deaths','vedant_altered_register','elsie_natural_death'], 'budget': 110},
 'full_inquest': {'level': 'advanced', 'claims': list(CLAIMS), 'budget': 150},
}


def build_case(seed):
    rng = random.Random(seed)
    killer = 'Savitri' if seed % 2 else 'Vedant'
    assistant = 'Vedant' if seed % 2 else 'Savitri'
    # Every item has an explicit creation/revelation cause and truthful or unreliable content.
    rows = [
 ('room', 'Room examination', 'examine', 'Mira died shortly after 21:10. There is a triangular impression in sealing wax by the door. A bloody sleeve thread lies beneath her hand.', 'The detective records the preserved room.'),
 ('medical', 'Mira’s medical examination', 'authenticate', 'The fatal injury occurred at 21:12, before the clock stopped at 21:30. Dev’s sleeve carried pressure-transfer stains consistent with aid, not proof of an attack.', 'The physician examines the body and compares the cloth.'),
 ('witness', 'Kitchen witness’s signed observation', 'examine', f'From the open service hatch I saw {killer} strike Mira at 21:12. {assistant} held the door. I recognized their faces by the lit table. I hid until Dev came in.', 'Cook Sera witnessed the act and wrote a statement before gossip circulated.'),
 ('opportunity', 'Independent crossing record', 'authenticate', f'The night porter and cook separately recorded {killer} and {assistant} entering the archive corridor at 21:08. The originals predate the public accusation. A seal fragment at the door matches {killer}’s personal seal.', 'Independent contemporaneous records and seal comparison establish presence.'),
 ('agreement', 'Recovered planning letter', 'authenticate', f'{assistant} wrote to {killer}: “I know you intend to kill Mira if she refuses. I will keep the corridor clear.” Original paper, seal and retained draft agree.', 'The assistant retained a draft; the recipient hid the original.'),
 ('threat', 'Supposed threat from Dev', 'examine', '“I will silence you before the ninth bell.” Signed Dev. The town constable calls this decisive.', 'Savitri wrote and planted a threat under Dev’s name.'),
 ('threat_test', 'Threat-letter examination', 'authenticate', 'The threat uses Savitri’s distinctive corrected letterform and her household stationery. A discarded draft survives in her ash bucket; Dev’s verified writing differs.', 'Paper and handwriting comparisons expose the forgery.'),
 ('draft', 'Ash-bucket fragments', 'examine', 'A recoverable draft of the threat is on the reverse of Savitri’s household account. Her instruction to deliver it under Dev’s name is legible.', 'Savitri incompletely burned a draft.'),
 ('garden', 'Garden excavation notes', 'examine', 'Two skeletons lie above, not beneath, last month’s planted bulbs. They died years ago. Grave cloth carries the ninth-ward laundry mark.', 'A gardener uncovers recently relocated old remains.'),
 ('cart', 'Carrier’s retained invoice', 'authenticate', 'Savitri paid Nalin to move two sealed grave crates from the old cemetery to Dev’s winter beds. Nalin’s signature and the stable’s duplicate match.', 'The carrier and stable retain independent payment records.'),
 ('soil', 'Soil and grave comparison', 'authenticate', 'Empty cemetery graves match the two sets of remains. Fresh cart tracks connect the cemetery gate to Dev’s garden. A delivery token matches Savitri’s invoice.', 'A survey compares burial sites and delivery records.'),
 ('kabir', 'Kabir’s first account', 'interview', 'I touched nothing after the scene was secured. Dev is our man. You know you can trust me.', 'Kabir conceals removal of the carrier’s letter.'),
 ('custody', 'Scene custody ledger', 'authenticate', 'Anya’s signed inventory lists envelope C before Kabir’s watch and records it missing afterward. A clerk independently saw Kabir pocket it.', 'Two observers document custody before and after removal.'),
 ('carrier_letter', 'Recovered carrier’s letter', 'examine', 'Kabir, please hide this. I delivered the crates for Savitri and did not ask what was inside. Your brother, Nalin. The envelope was recovered from Kabir’s satchel under witnessed inventory.', 'A witnessed recovery exposes the removal motive.'),
 ('affair', 'Leena and Mira’s correspondence', 'examine', 'Intimate letters describe their affair and agree to meet at the chapel at 20:00. They also discuss protecting the original ninth-ward statement.', 'The correspondents preserve private letters.'),
 ('chapel', 'Chapel meeting corroboration', 'authenticate', 'The chapel keeper’s original entry and separate letters confirm Leena and Mira’s intimate relationship. Leena was with the keeper from 21:00 to 21:25.', 'Independent records corroborate the relationship and relevant alibi.'),
 ('old_order', 'Original confinement order', 'authenticate', 'Raghav signed Tara’s ninth-ward confinement order twelve years ago. The hospital duplicate agrees. This does not establish involvement in Mira’s murder.', 'An institutional duplicate preserves the order.'),
 ('tara_copy', 'Tara’s circulated statement', 'examine', '“Raghav alone ... the door ... I asked mother ...” Sections are crossed out. The circulated text suggests only Raghav was responsible.', 'Savitri selectively copied Tara’s statement.'),
 ('tara_original', 'Tara’s original statement and copybook', 'authenticate', 'Tara described Raghav ordering confinement and Savitri refusing release. Savitri’s copybook contains instructions to omit the latter passage. Independent ink layers confirm the later omission.', 'Original and working copy reveal the edit.'),
 ('register', 'Death-register comparison', 'authenticate', 'Vedant’s replacement register omits patient Nera. An earlier parish duplicate and his correction ledger establish that he deliberately removed the entry.', 'A surviving duplicate exposes alteration.'),
 ('harun', 'Guide Harun’s recovered packet', 'examine', 'Harun recorded seeing the grave crates. He retained a threat from Vedant directing him to the quarry, with a matching appointment token.', 'The guide preserves material before his death.'),
 ('quarry', 'Quarry inquest and retained payment', 'authenticate', 'The inquest establishes Harun was killed, not lost in a fall. Vedant’s signed payment to the confessed attacker specifies silencing Harun over the crates; the attacker’s account matches nonpublic scene details.', 'Medical findings and independent financial material corroborate the guide’s killing.'),
 ('elsie', 'Elsie’s death examination', 'authenticate', 'Elsie died of the same progressive illness described in months of physician notes. Examination finds no injury or administered poison; the household’s timed observations support the illness course.', 'The physician compares the death with earlier medical records.'),
 ('elsie_notes', 'Elsie’s earlier medical notes', 'examine', 'Dated entries document severe deterioration before Mira’s death. The hospice copy independently matches the physician’s notes.', 'Two institutions preserve the prior illness record.'),
 ('ward', 'Ninth-ward controlled observation', 'authenticate', 'In repeated witnessed trials, the sealed ward object produces the same previously concealed phrase without physical contact. Swapping it for an inert replica stops the effect. Savitri and Vedant accurately describe the phrase separately. Neither trial identifies a killer.', 'An in-world repeatable supernatural rule manifests under controlled conditions.'),
 ('choices', 'Savitri and Vedant’s private exchange', 'examine', '“The voice returns when we handle the ward key. It cannot move our hands. We can refuse; yesterday we did. Tonight we will act.” Separate dated diaries record the same bounded experiences.', 'The pair document influence and retained choice before the murder.'),
 ('medium', 'Ishan’s object impression', 'interview', 'Blood on a sleeve. “Stay with me.” I cannot see a face or know whether this happened before or after the injury.', 'A genuine but context-poor perception reflects Dev rendering aid.'),
 ('gossip', 'Three town accusations', 'interview', 'Three witnesses repeat: “Dev threatened her before the ninth bell.” Each admits hearing it from the constable, who read the supposed threat.', 'One forged source produces several dependent reports.'),
 ('flight', 'Departure letter', 'examine', 'A resident left to escape a blackmailer over an affair. A road-keeper’s dated receipt places departure before Mira’s murder.', 'An unrelated secret explains apparent flight.'),
 ('raghav_alibi', 'Raghav’s independent alibi', 'authenticate', 'Two separate tollhouse records and the keeper place Raghav beyond the closed bridge throughout 21:00–21:30. He could not reach Mercy House during the fatal interval.', 'Independent route records exclude direct participation.'),
 ('kabir_alibi', 'Kabir’s arrival register', 'authenticate', 'The gatekeeper and Anya place Kabir’s first arrival at 21:40, after Mira’s death. The custody breach occurred later.', 'Independent observers distinguish concealment from murder.'),
 ('dev_statement', 'Dev’s account and treatment cloth', 'authenticate', 'Dev arrived at 21:16 and pressed his sleeve to Mira’s wound. The cook witnessed his arrival after the attack. The cloth pattern agrees with the physician’s findings.', 'Witness and physical comparison corroborate aid.'),
 ]
    numbers = rng.sample(range(100, 999), len(rows))
    evidence = {}
    ids = {}
    for n, (key, title, action, content, cause) in zip(numbers, rows):
        eid = f'E{n}'
        ids[key] = eid
        evidence[eid] = dict(id=eid, key=key, title=title, action=action, content=content, cause=cause)
    proofs = {
      'savitri_killed_mira': ['witness','opportunity'],
      'vedant_killed_mira': ['witness','opportunity'],
      'savitri_assisted_murder': ['agreement','witness','opportunity'],
      'vedant_assisted_murder': ['agreement','witness','opportunity'],
      'vedant_altered_register': ['register'],
      'savitri_forged_threat': ['threat_test','draft'],
      'savitri_moved_bodies': ['garden','cart','soil'],
      'kabir_removed_letter': ['custody','carrier_letter'],
      'leena_mira_affair': ['affair','chapel'],
      'dev_aided_mira': ['medical','dev_statement'],
      'raghav_confined_tara': ['old_order'],
      'savitri_edited_statement': ['tara_copy','tara_original'],
      'vedant_killed_guide': ['harun','quarry'],
      'elsie_natural_death': ['elsie','elsie_notes'],
      'ghost_influenced_pair': ['ward','choices'],
      'ghost_caused_all_deaths': ['ward','choices','medical','elsie'],
      'dev_killed_mira': ['medical','dev_statement','witness'],
      'raghav_killed_mira': ['medical','raghav_alibi'],
      'kabir_killed_mira': ['medical','kabir_alibi'],
      'leena_killed_mira': ['medical','chapel'],
    }
    # To refute a door-holder attribution, direct observation plus independent presence suffices.
    proofs['savitri_assisted_murder' if killer == 'Savitri' else 'vedant_assisted_murder'] = ['witness','opportunity']
    false_claims = {'ghost_caused_all_deaths','dev_killed_mira','raghav_killed_mira','kabir_killed_mira','leena_killed_mira'}
    false_claims.add('vedant_killed_mira' if killer == 'Savitri' else 'savitri_killed_mira')
    false_claims.add('savitri_assisted_murder' if killer == 'Savitri' else 'vedant_assisted_murder')
    alternatives = {c: [[ids[k] for k in keys]] for c, keys in proofs.items()}
    # Independent corroboration may establish a refutation without the same bundle
    # used to establish guilt. These alternatives follow evidence semantics.
    for cid in ('savitri_killed_mira','vedant_killed_mira','savitri_assisted_murder','vedant_assisted_murder'):
        if cid in false_claims:
            alternatives[cid].append([ids['witness'],ids['agreement']])
            alternatives[cid].append([ids['witness'],ids['medical']])
    for cid, alibi in [('raghav_killed_mira','raghav_alibi'),('kabir_killed_mira','kabir_alibi'),('leena_killed_mira','chapel')]:
        alternatives[cid].append([ids[alibi],ids['witness']])
    # This authenticated examination already includes prior records and timed
    # observations. One independently natural death refutes the universal claim.
    alternatives['ghost_caused_all_deaths'].append([ids['elsie']])
    return dict(seed=seed, killer=killer, evidence=evidence, characters=CHARACTERS, proof_bundles=alternatives,
                truth={c: c not in false_claims for c in CLAIMS},
                proofs={c: [ids[k] for k in keys] for c, keys in proofs.items()})
