"""Private authoring data. Never send this module or its complete output to agents."""
from copy import deepcopy

LOCATIONS = {
 'archive': {'name':'Mercy House archive','description':'Oil lamps illuminate a desk, a cold fireplace and shelves. A service door opens toward the scullery.', 'exits':['hall','scullery'], 'surfaces':['desk','fireplace','floor','shelves']},
 'hall': {'name':'Mercy House entrance hall','description':'Wet coats hang beside a visitors’ book. A narrow passage connects the rooms.', 'exits':['archive','scullery','courtyard','ward'], 'surfaces':['visitors book','coat stand']},
 'scullery': {'name':'Mercy House scullery','description':'A kettle sits on the range. Through a service hatch a strip of the archive desk is visible, but not the whole room.', 'exits':['archive','hall'], 'surfaces':['range','wash basin','service hatch']},
 'courtyard': {'name':'Mercy House courtyard','description':'A lamp lights the gate. The path descends toward the town square.', 'exits':['hall','square','garden'], 'surfaces':['gate','cart tracks']},
 'square': {'name':'Town square','description':'The inn, chapel path, and houses face a small square. Snow is gathering at the forest road.', 'exits':['courtyard','das_house','rao_house','inn','chapel','forest'], 'surfaces':['notice board','horse trough']},
 'garden': {'name':'Dev’s house and winter garden','description':'Dev’s small house stands beside winter beds and a tool shed.', 'exits':['courtyard','cemetery'], 'surfaces':['winter beds','tool shed','kitchen table']},
 'das_house': {'name':'Das household','description':'A narrow home with a parlor, an ash bucket beside the stove, and a locked writing desk.', 'exits':['square'], 'surfaces':['stove','writing desk','parlor table']},
 'rao_house': {'name':'Rao household','description':'A study opens onto an accessible courtyard. Acoustic drawings lie on a broad workbench.', 'exits':['square'], 'surfaces':['workbench','correspondence drawer']},
 'chapel': {'name':'Chapel','description':'A side desk holds the keeper’s register. Candles burn near the inner door.', 'exits':['square','cemetery'], 'surfaces':['register desk','pews']},
 'cemetery': {'name':'Old cemetery','description':'Rows of marked and unmarked graves run toward the fir trees.', 'exits':['garden','chapel','forest'], 'surfaces':['unnamed graves','burial office']},
 'forest': {'name':'Black Fir Forest edge','description':'Beyond the last houses, firs conceal a path to the quarry. Residents avoid it after dark.', 'exits':['square','cemetery','quarry'], 'surfaces':['path','milestone']},
 'quarry': {'name':'Old stone quarry','description':'A steep path ends above abandoned stone cuttings. A broken cart rail and a sheltered survey hut remain.', 'exits':['forest'], 'surfaces':['cart rail','survey hut']},
 'ward': {'name':'Sealed ninth ward','description':'A disused ward beyond a bolted door. An iron key hangs inside a glass-fronted box; its origin is not visible.', 'exits':['hall'], 'surfaces':['key box','bed frames','wall recess']},
 'inn': {'name':'Pine Lantern inn','description':'Travelers share a dining room. A lodging book lies behind the counter.', 'exits':['square'], 'surfaces':['counter','lodging book']},
}

def person(name,age,home,location,occupation,family,history,relationships,goals,temperament,memories):
    return dict(name=name,age=age,home=home,location=location,occupation=occupation,family=family,history=history,relationships=relationships,goals=goals,temperament=temperament,memories=memories)

PEOPLE={
 'mira':person('Dr. Mira Sen',41,'inn','archive','physician and archivist',{'sister':'Nandita, living elsewhere'},
 ['Worked at Mercy House as a young physician.','Recorded Tara’s account, but stayed silent when the copy was altered.','Returned to compare original hospital and parish records.'],
 {'leena':'secret romantic partner','savitri':'former matron; named in original record','vedant':'keeper of replacement archive','detective':'recipient of a letter asking them to visit'},
 ['Preserve the original statement.','Persuade the old staff to admit what happened.','Avoid exposing her own earlier silence.'], 'Tired, defensive when challenged about her past.',
 ['I hold Tara’s original statement in my desk.','Leena and I met privately at the chapel yesterday.','Savitri asked to meet me tonight. I told her I will leave on the first coach and release the original statement.']),
 'savitri':person('Savitri Das',62,'das_house','hall','retired matron',{'daughter':'Leena','husband':'Pranab, deceased'},
 ['Kept ward keys during a winter confinement twelve years ago.','Refused Tara’s request to leave.','Copied the statement without the passage naming herself.','Has recurring intrusive experiences since handling an old ward key.'],
 {'leena':'daughter; conceal the old ward history from her','vedant':'old colleague with a shared secret','mira':'threatens to release original records','detective':'comforted them after Tara died','kamala':'housekeeper'},
 ['Stop Mira releasing the original statement.','Protect Leena’s image of her.','Avoid being seen entering or leaving the archive.'], 'Normally composed; frightened of exposure; willing to use violence if cornered.',
 ['Mira has asked me to acknowledge refusing Tara release. She leaves on the first coach with the statement. I came here tonight intending to silence her permanently if she refuses to surrender it.','Vedant has offered to help keep the meeting private.','I recently paid Nalin to move two sealed grave crates into Dev’s winter beds.']),
 'vedant':person('Professor Vedant Rao',65,'rao_house','hall','scholar of acoustics',{'brother':'Mahesh, deceased','niece':'Ritu'},
 ['Designed speaking tubes and accessible passages at Mercy House.','Uses a wheelchair.','Removed Nera’s entry from a replacement register.','Has experienced phrases associated with an old ward object.'],
 {'savitri':'old ally who protected his reputation','mira':'threatens to compare original registers','hari':'household assistant','ritu':'niece and household member'},
 ['Help Savitri prevent disclosure.','Keep the corridor private for their meeting.','Preserve his research and reputation.'], 'Precise, proud, protective of old loyalties.',
 ['I agreed to keep the archive passage clear during Savitri’s meeting. I intend to honor that agreement tonight even if it implicates me.','Savitri has said she may hurt Mira if Mira refuses.','My correction ledger remains in my correspondence drawer.']),
 'dev':person('Dev Malik',48,'garden','courtyard','gravedigger and caretaker',{'wife':'Bina','son':'Arjun, working outside town'},
 ['Maintains the cemetery and Mercy House grounds.','Secretly retrieves possessions for bereaved families from unnamed graves.','Argued with Mira about access to the burial office.'],
 {'bina':'wife','mira':'recent disagreement, no desire to harm her','savitri':'former employer','sera':'knows him through deliveries'},
 ['Finish work and return home.','Help anyone injured.','Keep unauthorized grave openings private.'], 'Wary of officials; practical; ashamed of his grave work.',
 ['I argued with Mira about the burial-office key yesterday.','I left my spade in the tool shed beside the winter beds.','Bina expects me home for supper.']),
 'sera':person('Sera Dutt',29,'inn','scullery','cook',{'mother':'Elsie','younger brother':'Pawan'},
 ['Works evening shifts at Mercy House.','Pays for her mother’s care.','Once lost work after contradicting a wealthy patron.'],
 {'savitri':'former superior whose connections frighten her','dev':'brings firewood','mira':'sometimes helps her mother'},
 ['Keep her employment.','Avoid becoming a target.','Help someone in immediate danger.'], 'Anxious under authority; precise about small practical details, uncertain about motives.',
 ['The service hatch shows only part of the archive.','I heard gossip that Dev threatened Mira, but did not hear Dev say it.']),
 'leena':person('Leena Das',35,'das_house','chapel','schoolteacher',{'mother':'Savitri','father':'Pranab, deceased'},
 ['Grew up at the edge of Mercy House.','Was once the detective’s partner.','Is secretly involved with Mira.'],
 {'mira':'romantic partner','savitri':'mother whom she trusts','detective':'former partner','padma':'friend and chapel keeper'},
 ['Protect Mira.','Keep private letters out of public gossip.','Understand why Mira fears the old staff.'], 'Guarded about intimacy; caring toward people she trusts.',
 ['I gave Mira copies of old household letters.','I met Mira privately yesterday.','I am spending the evening with Padma.']),
 'kabir':person('Kabir Mehta',32,'inn','square','constable',{'brother':'Nalin'},
 ['Has worked alongside the detective for six years.','Was pulled from a flooded cellar by the detective.','Has repeatedly covered for Nalin’s debts.'],
 {'detective':'trusted senior and personal friend','nalin':'younger brother','anya':'junior colleague'},
 ['Assist the detective.','Keep Nalin out of prison.','Conceal documents exposing Nalin if he finds them unobserved.'], 'Helpful and loyal until family is threatened.',
 ['My younger brother Nalin has been delivering sealed crates for Savitri.','I promised to keep his name out of trouble.']),
 'anya':person('Anya Paul',24,'inn','courtyard','junior constable',{'father':'Prakash, postal clerk','mother':'Meera'},
 ['Recently joined the constabulary.','Keeps careful inventories.','Dislikes making an accusation before comparing accounts.'],
 {'kabir':'senior colleague','detective':'senior investigator'},
 ['Record discoveries accurately.','Protect original documents.','Learn through practical investigation.'], 'Reserved but willing to question an assumption.',
 ['I have not entered the archive tonight.']),
 'nalin':person('Nalin Mehta',27,'inn','square','carrier',{'brother':'Kabir'},
 ['Owes money to an inn supplier.','Takes poorly documented delivery work.'],
 {'kabir':'older brother','savitri':'customer','hari':'helped load crates'},
 ['Get paid.','Avoid questions about the grave crates.','Reach the inn before snow deepens.'], 'Restless, evasive about his work.',
 ['Savitri paid me to move two grave crates into Dev’s winter beds.','I wrote Kabir an appeal and left it in the entrance-hall visitors’ book for him.']),
 'kamala':person('Kamala Roy',54,'das_house','das_house','housekeeper',{'daughter':'Lata, seamstress in another town'},
 ['Has worked in the Das household for twenty years.','Recognizes Savitri’s stationery and household routines.'],
 {'savitri':'employer','leena':'helped raise her'},
 ['Keep the household running.','Protect Leena from gossip.'], 'Discreet, observant, dislikes police searching drawers.',
 ['Savitri took a sheet from the household paper block before leaving. I kept the torn offcut by the stove.','A signed shopping note remains with the household accounts.']),
 'hari':person('Hari Bose',39,'rao_house','rao_house','household assistant',{'wife':'Mala','daughter':'Tuli'},
 ['Maintains Vedant’s equipment and keeps receipts.','Helped load two heavy crates without knowing their contents.'],
 {'vedant':'employer','nalin':'carrier','ritu':'household member'},
 ['Keep his job.','Account for household deliveries accurately if pressed.'], 'Courteous, reluctant to implicate an employer.',
 ['I helped Nalin load two sealed crates at Savitri’s request.','A duplicate invoice is in the correspondence drawer.','I countersigned Vedant’s ordinary speaking-tube maintenance receipt when its payment was filed. It is in the correspondence drawer.']),
 'ritu':person('Ritu Rao',21,'rao_house','rao_house','student and copyist',{'uncle':'Vedant'},
 ['Copies diagrams for her uncle.','Hopes to study outside the town.'],
 {'vedant':'uncle','hari':'household assistant'},
 ['Finish copying drawings.','Avoid household conflict.'], 'Impatient with town gossip, curious about mechanisms.',
 ['I have seen corrections to the death register in my uncle’s ledger.','I do not know why those corrections were made.']),
 'bina':person('Bina Malik',46,'garden','garden','gardener and laundress',{'husband':'Dev','son':'Arjun'},
 ['Keeps winter beds beside the house.','Takes laundry from several households.'],
 {'dev':'husband','nalin':'seen delivering near the beds'},
 ['Protect her family.','Find why the garden soil was disturbed.'], 'Direct, suspicious of officials who blame Dev.',
 ['The bulbs were planted last month.','I saw a carrier’s cart near the beds two nights ago but could not see what was unloaded.']),
 'padma':person('Padma Jain',57,'chapel','chapel','chapel keeper',{'spouse':'Reva'},
 ['Maintains the chapel register.','Hosts people who need quiet and privacy.'],
 {'leena':'friend','mira':'visitor'},
 ['Protect visitors’ privacy.','Give accurate times when necessary.'], 'Calm, careful about separating observation from rumour.',
 ['Leena arrived at the chapel before dusk and has remained with me.']),
 'raghav':person('Raghav Sethi',68,'inn','inn','former Mercy House director',{'wife':'Asha','son':'Kunal'},
 ['Ordered Tara confined twelve winters earlier.','Publicly defended the institution.'],
 {'detective':'knows the detective has sought answers about Tara','savitri':'former matron','mira':'former physician'},
 ['Avoid exposure of confinement orders.','Remain at the inn tonight.'], 'Defensive, accustomed to authority.',
 ['My old confinement order had a hospital duplicate.','I have not visited Mercy House this evening.']),
 'ishan':person('Ishan Vale',44,'inn','forest','medium and itinerant repairer',{'sister':'Noor, deceased'},
 ['Sometimes experiences brief sensory fragments when touching ward objects.','Cannot reliably identify who is speaking in a fragment.'],
 {'vedant':'has asked about the fragments','dev':'repairs his tools'},
 ['Understand the fragments.','Avoid being blamed for another unexplained event.'], 'Distracted, earnest, sometimes mistaken about meaning.',
 ['The forest frightens me, but I have not seen anyone killed tonight.']),
}

DETECTIVE = {
 'name':'Inspector Arun Mehra', 'age':38, 'occupation':'district investigator',
 'life_history':['Grew up on Mill Lane in Bhairav’s Hollow with younger sister Tara; your father repaired coach wheels and your mother kept the household accounts.','Tara died at Mercy House twelve winters ago. The official letter called it a winter fever; you have never seen her original statement.','Spent later years trying to obtain original records.','Worked with Constable Kabir Mehta for six years; pulled him from a flooded cellar.','Lived with Leena Das for three years before they separated.','Received a letter from Dr. Mira Sen asking you to visit Mercy House about an old family record. You traveled here on leave, before any death was reported.'],
 'ordinary_life':['Keep a room in the district headquarters, a day’s coach journey away.','Remember the chapel path and the market square from childhood; several Mercy House rooms have since changed.','Still write occasionally to Leena, usually about practical matters.'],
 'remembered_people':{'kabir':'colleague of six years','leena':'former partner','savitri':'Leena’s mother; served tea after Tara’s funeral','raghav':'signed letters refusing requests for Tara’s records'},
}

PRESSURES = {
 'ordinary': {'description':'The original open-ended meeting; the participants may postpone it.', 'savitri':[], 'vedant':[]},
 'urgent': {'description':'A last meeting before a scheduled dawn departure. No killing is forced.',
   'savitri':['Tonight is the last private opportunity to stop publication: Mira has booked the dawn coach and the original will leave town. You resolved before arriving to confront her now, despite the risk.'],
   'vedant':['You promised to keep this evening’s meeting private before Mira takes the dawn coach. Abandoning the passage would expose your agreement to Savitri.']},
}

def setting(pressure='urgent'):
    if pressure not in PRESSURES:raise ValueError('Unknown scenario pressure')
    locations,people,detective=deepcopy(LOCATIONS),deepcopy(PEOPLE),deepcopy(DETECTIVE)
    for pid in ('savitri','vedant'):people[pid]['memories'].extend(PRESSURES[pressure][pid])
    for pid,p in people.items():
        p['public_voice']={'savitri':'measured, brief','vedant':'formal, precise','sera':'hesitant, concrete','kabir':'familiar, practical','anya':'careful, concise'}.get(pid,'conversational, restrained')
        p['daily_routine']={'home':p['home'],'work':p['occupation'],'evening':'finish ordinary duties before snowfall'}
    from .prose import enrich
    enrich(locations,people,detective)
    return locations,people,detective
