"""Private original case authoring. Not copied into the detective image.

These are authored seeded scenarios with executed action tapes, not claims of
new autonomous LLM-generated murders or uniqueness against all published fiction.
"""
from copy import deepcopy
import random


def person(name,age,job,place,life,appearance,memories=(),family=None,goals=None):
    return {'name':name,'age':age,'occupation':job,'home':place,'location':place,
      'family':family or {},'history':[life],'life_portrait':life,'appearance':appearance,
      'relationships':{},'goals':goals or ['Continue your work.','Give an accurate account of what you actually observed.'],
      'temperament':'Ordinary concerns and mixed loyalties; distinguish an observation from an interpretation.',
      'memories':list(memories),'public_voice':'conversational, concrete, occasionally hesitant',
      'daily_routine':{'home':place,'work':job,'evening':'finish work before the snow closes the road'}}


def place(name,text,exits,surfaces):
    return {'name':name,'description':text,'exits':exits,'surfaces':surfaces}


def biography(connection):
    text=("The district coat still carries the smell of the coach. Before the uniform there was Mill Lane: your father's wheel plane, your mother's account book, and Tara asking you to wait at the chapel turn. Twelve winters after her death, the institutional letter remains in your desk. You remember its careful wording.\n\n"
          +connection+"\n\nYou came back to Bhairav's Hollow on ordinary leave. The road is under snow, the lamps are lit, and people are still finishing the day's work.")
    return {'name':'Inspector Arun Mehra','age':38,'occupation':'district investigator','life_story':text,'life_history':[text]}


def lantern(seed):
    rng=random.Random(seed);culprit=rng.choice(['maren','tobin']);other=next(p for p in ('maren','tobin') if p!=culprit)
    locations={
      'inn':place('Pine Lantern reading room',"The reading room holds the last warmth of the kitchen. A green-shaded lamp lights a large table, and an ashless hearth has been swept for the night. Beyond the door is a small hall; the courtyard can be reached from there. On the table the inn's ordinary accounts wait beneath a bowl of apples. The room is quiet enough to hear a cup being set down.",['hall'],['floor','table','hearth']),
      'hall':place('Pine Lantern side hall',"A narrow bench stands beneath hooks for wet coats. The reading-room door is close enough that an ordinary voice can carry through it, but the room itself cannot be seen from the bench. The courtyard door closes unevenly against the snow. A shelf holds the day's parcels.",['inn','courtyard'],['bench','parcel shelf']),
      'courtyard':place('Pine Lantern courtyard',"Wheel ruts end beside a covered woodpile. The gate has been fastened against the wind, leaving a single lantern above the snow. The inn's side hall is the way back into the warm rooms. Ordinary errands have left tracks crossing one another without a readable chronology.",['hall'],['woodpile','gate'])}
    people={
      'oren':person('Oren Dutt',51,'lamplighter and accounts keeper','inn',"Oren kept the lamps and the inn's smaller debts in the same ruled book. He disliked both a dark stair and an unexplained subtraction. Lately he had begun copying disputed charges onto separate sheets, a habit that made his evenings longer and his conversations less comfortable.",'A man in a wool waistcoat has left his spectacles beside the accounts.',family={'spouse':'Mina, a weaver'}),
      'maren':person('Maren Vale',33,'shipping clerk','inn',"Maren learned her numbers in this reading room while waiting for her father to finish deliveries. She now keeps charges for the winter wagons and sends money to a brother studying outside the valley. She prefers a dispute that can be settled on paper; the last month has given her several that cannot.",'A woman in a plain travelling dress keeps a leather document folder closed on her lap.',memories=['I came to discuss an old freight charge with Oren.'],family={'brother':'Adit, studying elsewhere'}),
      'tobin':person('Tobin Hale',45,'watch repairer','inn',"Tobin can make a worn spring work for another winter, but finds promises harder to repair. An advance for a workshop never became the workshop he described. He still comes to the inn because there are customers here who remember his father and will sit while he explains a delay.",'A repairer in a well-brushed coat turns a watch chain between his fingers.',memories=['I came to settle a disputed workshop advance with Oren.'],family={'daughter':'Elsie, a school pupil'}),
      'nell':person('Nell Voss',48,'innkeeper','inn',"Nell has run the Pine Lantern through three winters of closed roads. She knows when a guest needs company and when a question would only lengthen an already difficult evening. She has no wish to protect violence in her own reading room. Being asked to say only what she saw is a relief.",'An innkeeper has rolled her sleeves above the wrists; a clean towel rests over one shoulder.',memories=['I was laying the reading-room table before the lamps were lowered.'],family={'son':'Perrin, a porter'},goals=['Keep the guests safe.','Describe your actual observations accurately; do not withhold an ordinary eyewitness account.'])}
    connection="Nell once kept a bowl of soup warm while your family waited for a delayed coach. You remember her bringing it out twice. Maren and Tobin are familiar faces from the square, although you have never worked with either of them."
    motive={'maren':'an altered freight account','tobin':'a workshop advance that was never repaid'}[culprit]
    return {'family_id':'lantern_room','locations':locations,'people':people,'detective':biography(connection),
      'culprit':culprit,'other':other,'victims':['oren'],'start':'inn','target_predicates':['killed'],
      'secrets':{culprit:[f'Oren intended to publish {motive}. I came prepared to stop him by violence.']},
      'objects':[
       ('lamp base','inn','hearth','A heavy brass lamp base rests on the hearth shelf. Its edge is intact.','lamp'),
       ('accounts book','inn','table','The book lists two disputes: a freight account under Maren Vale and a workshop advance under Tobin Hale. Neither entry says how the dispute was resolved.','accounts')],
      'tape':[('move',other,'hall'),('take',culprit,'lamp'),('strike',culprit,'oren'),('move',other,'inn')],
      'reference_witness':'nell','disclosure_relevance':{culprit:['lamp','accounts']}}


def passenger(seed):
    rng=random.Random(seed);culprit=rng.choice(['brin','elin']);primary='vesper' if culprit=='brin' else 'joel'
    locations={
      'forest':place('Old bridge crossing',"The old bridge crosses a narrow channel between the firs. A path climbs back to the boarding yard. The river can be heard beneath its ice. The bridge approach, the bank and anything below the crossing can be inspected separately.",['courtyard'],['wreckage','bank','bridge approach']),
      'courtyard':place('Coach boarding yard',"A covered bay keeps the worst weather off the coaches. A repair stand faces the gate and a narrow notice board holds the day's departures. The road descends to the bridge; doors lead to the inn, while a short lane reaches the square. From the stand a person can see the rear brake assembly without seeing inside the coach.",['forest','inn','square'],['repair stand','notice board']),
      'inn':place('Pine Lantern booking room',"The booking room smells of damp tickets and tea. A desk holds the dispatch ledger; a writing shelf has been cleared for visitors. The boarding yard is just outside. Passengers have left scarves over the backs of chairs, expecting to return for them after the short journey.",['courtyard'],['dispatch desk','writing shelf']),
      'square':place('Toll office at the square',"The toll office has a broad public counter and a low stove. Receipts are tied in monthly bundles, with specimen signatures in the cover book. The boarding yard lies along the lane. A clerk has left enough lamp oil for the last accounts to be checked.",['courtyard'],['counter','cover book'])}
    people={
      'vesper':person('Vesper Rane',39,'bridge surveyor','courtyard',"Vesper measures things others prefer to estimate. The bridge report has become a quarrel about livelihoods as much as timber. She has kept her calculations separate from the letters asking her to revise them, and means to deliver both to the regional office.",'A surveyor’s wool coat is folded beside a rolled drawing case.',memories=['My dispatch code is BLUE-17.']),
      'joel':person('Joel Arden',29,'mail carrier','courtyard',"Joel carries official packets without being told why their seals matter. Recently he began keeping duplicate charges because two offices remembered the same delivery differently. His sister thinks the work is steady; he has not told her about the disputed toll accounts.",'A carrier’s satchel has a repaired strap and a brass dispatch tag.',memories=['My dispatch code is AMBER-4.']),
      'brin':person('Brin Calder',56,'bridge contractor','inn',"Brin has spent thirty years making the valley's repairs possible on credit. A closed bridge would cost the business more than the price of new timber. He regards Vesper's figures as a public judgment of work whose difficulties she has never had to finance.",'A contractor wears a heavy coat with a neatly patched shoulder.',memories=['I objected to the surveyor’s proposal to close the bridge.']),
      'elin':person('Elin Frost',36,'toll registrar','square',"Elin inherited an office in which several old conveniences had never been written down. She kept some of them because people asked politely, then because stopping would require an explanation. Joel's duplicate accounts have made those explanations urgent.",'A registrar keeps her sleeves clear of the ink on the counter.',memories=['Joel and I disagreed about duplicate toll charges.']),
      'neri':person('Neri Bell',43,'coach repairer','courtyard',"Neri signs a repair only after testing it. Brin helped his family after a roof fire, a debt he has never liked having mentioned. He is wary of officials who turn a practical observation into a complete accusation. Show him the part in question and give him room to be exact.",'A repairer wipes grease from a thumb before touching his notebook.',memories=['I inspected the brake before departure. The dated inspection card is on the repair stand.']),
      'pella':person('Pella Ash',31,'booking clerk','inn',"Pella knows passengers first by their handwriting and only later by their faces. She keeps a code ledger so a late change can be checked without opening a sealed packet. She has been accused of favouring both sides of the bridge dispute and is tired of explaining a booking as though it were a political act.",'A booking clerk has a pencil tucked behind one ear.',memories=['The dispatch ledger ties sealed packets to their carriers.'])}
    code='BLUE-17' if primary=='vesper' else 'AMBER-4'
    objects=[('brake rod','courtyard','repair stand','An intact brake-release rod is fitted to the coach.','brake_trace'),
      ('inspection card','courtyard','repair stand','Signed before departure by Neri Bell: the brake-release rod and retaining pawl were intact and held under load. A diagram records their fitted positions.','inspection'),
      ('dispatch ledger','inn','dispatch desk','The departure list records Vesper Rane carrying BLUE-17 and Joel Arden carrying AMBER-4 on the same coach. The entries were countersigned before departure.','dispatch_ledger')]
    for pid,loc in [('brin','inn'),('elin','square')]:objects.append(('signed business receipt',loc,'writing shelf' if loc=='inn' else 'cover book',f'A routine business receipt is signed in full by {people[pid]["name"]}. The hand has a distinctive joined final r.' if pid==culprit else f'A routine business receipt is signed in full by {people[pid]["name"]}. Its hand is evenly spaced and upright.','sample_'+pid))
    return {'family_id':'second_passenger','locations':locations,'people':people,
      'detective':biography("You remember Brin patching the workshop roof after a storm, and Elin copying a difficult account for your mother. Neri repaired a coach wheel on the journey when you first left the valley. These memories concern ordinary help given years ago."),
      'culprit':culprit,'primary':primary,'code':code,'victims':['vesper','joel'],'start':'forest','target_predicates':['killed','targeted'],
      'secrets':{culprit:[f'I decided to prevent {people[primary]["name"]} reaching the regional office. I planned to disable the coach carrying {code}.']},
      'objects':objects,'disclosure_relevance':{'neri':['brake_trace','inspection'],culprit:['brake_trace','route_slip','sample_'+culprit]},
      'tape':[('travel',culprit,'inn'),('write_route',culprit,code),('travel',culprit,'courtyard'),('tamper',culprit,'brake_trace'),('travel',culprit,'inn'),('depart','joel','forest'),('cross','joel','forest')],
      'reference_witness':'neri'}


def bell(seed):
    rng=random.Random(seed);culprit=rng.choice(['maela','lewin'])
    locations={
      'chapel':place('Chapel scriptorium',"A lamp burns beside the reading lectern. A cup and a small labelled bottle stand on a tray, where evening visitors leave their remedies before sitting down. On the keeper's desk lie dispensary papers and a sealed reference vial. Doors open toward the square and the quieter side hall. The bell rope hangs motionless beside the wall.",['square','hall'],['floor','lectern','keeper desk']),
      'hall':place('Chapel side hall',"Two writing tables stand beneath the coat hooks. One is used by Maela for hospital copies; the other holds Lewin's repair accounts. The chapel and square can both be reached from here. A parcel shelf catches paper scraps that the stove has not yet claimed.",['chapel','square'],['copying table','repair table','parcel shelf']),
      'square':place('The lamp-lit square',"Snow has collected against the chapel steps. Across the road the inn keeps a line of light under its door. The chapel side hall opens beside a covered passage. Voices travel across the square more easily than faces can be made out.",['hall','chapel','inn','forest'],['notice board','steps']),
      'inn':place('Pine Lantern common room',"The stove has gathered a small audience who pretend not to be listening to one another. A notice board stands beside the counter, and the lodging desk has a clock that gains a minute each winter. The square is outside. Someone has pinned a narrow sheet under a warning about the road.",['square'],['notice board','lodging desk']),
      'forest':place('Fir path above the chapel',"The path rises only a short way before the last window disappears. Branches rub together in the wind, making an uneven tapping. The town can be reached only by returning to the square. Nothing here supplies a face to a sound.",['square'],['path','milestone'])}
    people={
      'tessa':person('Tessa Rowan',58,'hospital records keeper','inn',"Tessa kept two copies when one would have made her life easier. Her private index contains changes to hospital night-duty lists and the reasons offered afterward. She has asked both her daughter and an old family friend to explain discrepancies before she gives the index to the district office.",'A records keeper’s shawl has been laid over the chapel chair.',family={'daughter':'Maela'}),
      'maela':person('Maela Rowan',26,'hospital copyist','hall',"Maela grew up making clean copies of her mother's difficult pages. When a disputed night-duty entry put a colleague's post at risk, she changed a line before asking permission. The change became larger in other people's accounts. She wants a life that is not forever measured against her mother's exactness.",'A woman in an ink-marked cuff keeps loose pages tied with blue thread.',memories=['I use the copying table in the chapel hall.','My mother asked about changes to a night-duty list.'],family={'mother':'Tessa'}),
      'lewin':person('Lewin Crowe',61,'clock repairer and family friend','hall',"Lewin has mended the Rowan household's clocks since Maela needed a stool to see their faces. He also maintained hospital attendance mechanisms, sometimes certifying a repair before it was done. Tessa's index could turn those conveniences into a public account of his working life.",'An older repairer rests a cloth tool roll on the table.',memories=['I use the repair table in the chapel hall.','Tessa questioned some of my hospital attendance certificates.']),
      'ivo':person('Ivo Lark',47,'itinerant reader and storyteller','inn',"Ivo has learned that an uncertain sentence is remembered as a prediction once something happens. He believes some of the things he says and has embellished others to keep an audience. A paper delivered to him tonight seemed to promise the sort of detail that makes a room fall silent. He is frightened of being held responsible for what the paper described.",'A reader holds a folded scarf against his chest and chooses his words slowly.',memories=['I am staying at the inn and have not gone into the chapel tonight.']),
      'alba':person('Alba Reed',34,'chapel keeper and dispensary assistant','chapel',"Alba records what is put on the remedy shelf because labels survive longer than a person's certainty about a busy evening. Lewin once argued for her appointment, while Maela has helped with the copying. She does not want kindness returned as an accusation, but she will account for a bottle when shown the actual material.",'A chapel keeper has a pencil tied to the dispensary book with string.',memories=['The sealed reference vial and dispensing record are on my desk.']),
      'niv':person('Niv Soren',22,'parcel runner','hall',"Niv carries the errands that everyone calls small until their contents become important. He has learned to keep a delivery docket even when an older customer calls it unnecessary. He would like to be paid and to stop being the person who must explain a letter someone else wrote.",'A young runner has melted snow on the shoulders of his coat.',memories=['I keep delivery dockets at the lodging desk after the evening round.'])}
    objects=[('labelled tonic bottle','chapel','lectern','A small bottle is labelled ordinary mint cordial. Its seal is intact.','tonic'),
      ('sealed reference vial','chapel','keeper desk','A sealed reference vial contains the ordinary cordial, retained with its dispensing entry. The entry describes the fictional ironleaf preparation as a different, harmful dispensary material; no quantities or preparation instructions are given.','reference_vial'),
      ('dispensing record','chapel','keeper desk','Alba recorded the cordial as clear before it left the dispensary. A retained-paper assay distinguishes it from the fictional ironleaf preparation, which leaves a dark stain.','dispensary')]
    for pid,surface in [('maela','copying table'),('lewin','repair table')]:
        objects.extend([('paper offcut','hall',surface,'An unused offcut has an uneven toothed tear.' if pid==culprit else 'An unused offcut has a straight trimmed edge.','paper_'+pid),
          ('signed account','hall',surface,f'An ordinary account signed in full by {people[pid]["name"]}. Its lettering is closely spaced, with a double stroke on the final letter.' if pid==culprit else f'An ordinary account signed in full by {people[pid]["name"]}. Its lettering is broad and upright.','sample_'+pid)])
    return {'family_id':'bell_before_dawn','locations':locations,'people':people,
      'detective':biography("Lewin kept the workshop clock running after your father died. Maela once copied a school certificate for Tara's friend. Ivo read a supposed message at a winter gathering you attended; you remember how the room responded, and the silence afterward. Tessa has written to you about ordinary clerical work for years."),
      'culprit':culprit,'victims':['tessa'],'start':'chapel','target_predicates':['killed','forged','relayed'],
      'objects':objects,'secrets':{culprit:['Tessa’s index would expose my own alterations. I decided to kill her and make a warning appear to come from a dead bell keeper.']},
      'disclosure_relevance':{'alba':['tonic','reference_vial','dispensary'],'ivo':['warning','delivery'],'niv':['warning','delivery'],culprit:['tonic','warning','sample_'+culprit]},
      'tape':[('write_warning',culprit,'warning'),('handoff',culprit,'niv'),('travel','niv','inn'),('deliver','niv','ivo'),('announce','ivo','warning'),
              ('travel',culprit,'chapel'),('adulterate',culprit,'tonic'),('travel','tessa','chapel'),('drink','tessa','tonic')],
      'reference_witness':'alba'}


BUILDERS={'lantern_room':lantern,'second_passenger':passenger,'bell_before_dawn':bell}


def definition(family,seed):
    return deepcopy(BUILDERS[family](seed))
