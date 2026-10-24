"""Executed incident, character-local memories and situated detective actions.

This module is trusted world code. The detective sees only the public methods'
observations; the journal and character packets belong in private logs.
"""
from copy import deepcopy
import hashlib
import json
import random
import re
from .setting import setting
from .boundaries import AuditTrail, flags, topics, eligible_memories
from .validation import validate_action

class Town:
    def __init__(self, seed=7, agents=None, pressure="urgent", setting_data=None):
        self.seed=seed; self.rng=random.Random(seed)
        self.pressure=pressure
        self.locations,self.people,self.detective=deepcopy(setting_data) if setting_data is not None else setting(pressure)
        self.audit=AuditTrail()
        self.permissions=set()
        self.agents=agents
        self.phase='prelude'; self.tick=0; self.location='archive'
        self.journal=[]; self.objects={}; self.testimony={}; self.observed={}; self.receipts={}
        self.known_people={'kabir','leena','savitri','raghav'}; self.known_places={'archive'}
        self.visited={'archive'}; self.history=[]; self.ended=False; self.result=None
        self.counter=0; self.obj_counter=0; self.memory_counter=0
        self.states={pid:{'alive':True,'fear':self.rng.randint(15,45),'trust':35,'dialogue':[],'memories':[]} for pid in self.people}
        self.clock=0; self.kabir_briefed=False
        for pid,p in self.people.items():
            for text in p['memories']:self.remember(pid,text,'personal_history',None)
        self._seed_objects()

    def _seed_objects(self):
        # Existing objects have specific owners and histories; present crimes are not prewritten.
        self.object('folded sheet','archive','desk','A thin sheet has been folded along the same lines until the paper has worn almost white. In Tara’s hand: “Please keep what I actually said. The director ordered the door locked. I asked Matron Das to let me out. She refused. If another copy is made, do not let that sentence disappear.” The remaining lines concern cold bedding and a request for clean clothes.',{'predicate':'confined','actor':'raghav','object':'tara'},'original_statement')
        self.object('visitors book','hall','visitors book','Names and arrival times. Several pages have been folded at the corner.',None,'visitors_book')
        self.object('folded envelope','hall','visitors book','The envelope has no stamp. Inside, a hurried letter begins: “Kabir—Savitri paid me to carry two sealed grave crates to Dev’s winter beds. I took the cart after the last bell, as she asked. I was told not to stop at the house. The stable kept a duplicate of the charge. Please keep me out of this; I cannot have your uniform at my door. Nalin.” A second fold has tucked the signature out of sight.',{'predicate':'commissioned','actor':'savitri','object':'burials'},'delivery_letter')
        self.object('carbon invoice','rao_house','correspondence drawer','A duplicate account has left a blue-grey impression on thin paper. “Paid by S. Das. Carrier Nalin. Two grave crates: old cemetery to winter garden. Evening cartage; payment received.” A stable clerk has initialled the charge, and an old pinhole marks the corner where this copy was once attached to another account.',{'predicate':'commissioned','actor':'savitri','object':'burials'},'invoice')
        self.object('copybook','das_house','writing desk','A draft statement copies Tara’s words but crosses out the sentence about the matron refusing release.',{'predicate':'altered','actor':'savitri','object':'tara_statement'},'copybook')
        self.object('ink-stained ledger','rao_house','correspondence drawer','The working book has absorbed ink through its cloth spine. Its inside cover is signed V. Rao. A replacement list of ninth-ward deaths has no entry for Nera; against the earlier numbering, a marginal instruction reads “remove this entry from the clean copy.” The space has been ruled over rather than torn out.',{'predicate':'altered','actor':'vedant','object':'death_register'},'correction_ledger')
        self.object('signed maintenance receipt','rao_house','correspondence drawer','A routine maintenance receipt predates the inquiry. “Speaking-tube repair completed and account settled. Vedant Rao.” Hari countersigned its payment when it was filed. The ordinary writing has narrow letters and a doubled loop on lower-case o.',None,'vedant_sample')
        self.object('disturbed soil','garden','winter beds','The soil above last month’s bulbs has recently been lifted. The depression is longer than a garden trench.',None,'soil')
        self.object('grave cloth','garden','winter beds','Below the disturbed soil are two old sets of human remains wrapped in cloth marked WARD IX.',None,'remains')
        self.object('household paper','das_house','stove','An unused paper offcut lies beside the ash bucket rather than inside it. One edge has been cut square; the other is an irregular tear with a small projecting tooth near the middle. The household stationery block is the same pale shade, but there is no writing on this piece.',None,'draft')
        self.object('signed shopping note','das_house','parlor table','A shopping note has been held flat by the sugar bowl. “Kamala—please collect flour and lamp oil tomorrow. Leave the account in the kitchen tin; I shall settle it after breakfast. S. Das.” The ordinary household hand has a distinctive overwritten lower-case d. A dry ring from the bowl crosses the bottom corner.',None,'savitri_sample')
        coat=self.object('household shawl','hall','worn clothing','A dark wool shawl with repaired cuffs and a laundry tag bearing S. Das.',None,'coat')
        self.objects[coat]['carried_by']='savitri'
        self.object('spade','garden','tool shed','A working spade with a broad iron blade and fresh soil on its edge.',None,'spade')
        self.object('private letters','das_house','parlor table','Two letters are folded inside a plain wrapper. One addresses Leena in Mira’s hand: “I love you. That is the part of this I can write without revising it. Meet me at the chapel tomorrow, before the lamps are lit.” A reply signed Leena refers to their private meeting yesterday and asks that the letters be kept from household gossip.',{'predicate':'relationship','actor':'leena','object':'mira'},'private_letters')
        self.object('ward key','ward','key box','An old iron key. Its bow is wrapped in faded thread.',None,'ward_key')
        self.object('parish register','chapel','register desk','The original parish register includes Nera among the ninth ward deaths twelve winters ago. Dates and entry numbers are legible beneath the keeper’s old certification.',None,'parish_register')

    def object(self,label,place,surface,text,proposition=None,key=None,event=None):
        self.obj_counter+=1; oid=f'o{self.rng.randrange(10000,99999)}-{self.obj_counter}'
        self.objects[oid]={'id':oid,'label':label,'location':place,'surface':surface,'text':text,'proposition':proposition,'key':key,'event':event,'hidden_by':None,'destroyed':False,'collected':False,'buried':key=='remains','carried_by':None}
        return oid

    def remember(self,pid,text,source,event,proposition=None):
        self.memory_counter+=1; mid=f'm{self.memory_counter}'
        memory={'id':mid,'text':text,'source':source,'event':event,'proposition':proposition}
        self.states[pid]['memories'].append(memory)
        return mid

    def event(self,kind,actor,place,detail,proposition=None,noticed=True):
        eid=f'j{len(self.journal)+1}'
        event={'id':eid,'tick':self.tick,'kind':kind,'actor':actor,'location':place,'detail':detail,'proposition':proposition}
        self.journal.append(event)
        self.audit.append('world_event',event)
        if noticed:
            # Local perception, not omniscient insertion into all biographies.
            for pid,p in self.people.items():
                if self.states[pid]['alive'] and p['location']==place:
                    self.remember(pid,detail,'direct_observation',eid,proposition)
        return eid

    def packet(self,pid,actions,question=None,presented=None,approach=None):
        p=self.people[pid]; state=self.states[pid]; place=p['location']
        return {'person':{'id':pid,**{k:deepcopy(p[k]) for k in ('name','age','occupation','family','home','history','life_portrait','relationships','goals','temperament','public_voice','daily_routine')}},
                'phase':self.phase,'time':self.tick,
                'location':{'id':place,'description':self.locations[place]['description']},
                'people_visible':[{'id':x,'name':v['name'],'condition':'responsive' if self.states[x]['alive'] else 'motionless on the floor'} for x,v in self.people.items() if x!=pid and v['location']==place],
                'visible_scene':self.visible_scene(place),
                'memories':[{k:m[k] for k in ('id','text','source')} for m in state['memories']],
                'emotional_state':{'fear':state['fear'],'trust_in_detective':state['trust']},
                'public_recall_ids':[m['id'] for m in state['memories'] if m['source'] not in ('personal_history','own_action') and not m.get('proposition')],
                'recent_dialogue':deepcopy(state['dialogue'][-8:]),'question':question,'approach':approach,
                'presented_material':presented or [],'available_actions':actions}

    def visible_scene(self,place):
        return 'Mira lies motionless beside the desk with a head injury.' if place=='archive' and not self.states['mira']['alive'] else self.locations[place]['description']

    def prelude_actions(self,pid):
        p=self.people[pid]; place=p['location']; alive=self.states[pid]['alive']
        actions=[{'action_id':'wait','description':'Continue your ordinary routine here without intervening.'}]
        if not alive:return actions
        for destination in self.locations[place]['exits']:
            actions.append({'action_id':'go:'+destination,'description':'Travel to '+self.locations[destination]['name']+' along the visible route.'})
        murdered=any(e['kind']=='fatal_injury' for e in self.journal)
        incident_ids={e['id'] for e in self.journal if e['kind']=='fatal_injury'}
        local_incident=(place=='archive' and murdered) or any(m['event'] in incident_ids for m in self.states[pid]['memories'])
        def add(a,d):actions.append({'action_id':a,'description':d})
        if pid=='savitri':
            if place=='hall' and not murdered:add('enter_archive','Enter the archive to confront Mira about the statement.')
            if place=='archive' and self.states['mira']['alive'] and self.people['mira']['location']=='archive':
                add('argue','Demand that Mira surrender the original. She refuses to destroy it.')
                add('attack_mira','Strike Mira with the heavy desk seal. This may kill her and leaves physical traces; you can choose to refrain.')
            if place=='archive' and murdered:
                if not any(o['key']=='planted_threat' for o in self.objects.values()):add('plant_threat','Write and leave a threat under Dev’s name to divert suspicion.')
                add('return_home','Leave the archive and return home.')
        if pid=='vedant':
            if place=='hall' and not any(e['kind']=='guard_door' for e in self.journal):add('guard_door','Hold the archive service door and keep passers-by away, despite knowing Savitri has threatened violence.')
            if murdered and local_incident and place!='rao_house':add('return_home','Return to your household without seeking help.')
        if pid=='dev':
            if murdered and local_incident and place=='courtyard':add('enter_to_help','A cry reaches the courtyard. Enter the archive to look for someone needing help.')
            if murdered and place=='archive' and not any(e['kind']=='aid' for e in self.journal):add('give_aid','Press your sleeve to the injured woman’s wound and call for help.')
        if pid=='sera':
            if place=='scullery' and not murdered:add('listen_hatch','Attend to the voices through the service hatch while cooking.')
            if murdered and local_incident and place=='scullery':add('seek_help','Leave by the hall to find a constable, though you fear being implicated.')
        return actions

    def commit(self,pid,decision,allowed):
        action=decision.get('action_id','wait')
        if action not in {a['action_id'] for a in allowed}:
            self.audit.append('blocked_character_action',{'person':pid,'reason':'unavailable_action'})
            return 'wait'
        self.audit.append('character_decision',{'person':pid,'action':action,'speech':decision.get('speech',''),'recall_ids':decision.get('recall_ids',[])})
        p=self.people[pid]; place=p['location']
        if action.startswith('go:'):
            destination=action.split(':',1)[1]
            if destination in self.locations[place]['exits']:
                self.event('departure',pid,place,f'{p["name"]} leaves toward {self.locations[destination]["name"]}.')
                p['location']=destination
                self.event('arrival',pid,destination,f'{p["name"]} arrives.')
        elif action=='enter_archive':
            self.event('arrival',pid,'hall',f'{p["name"]} enters the archive.');p['location']='archive'
            self.event('argument',pid,'archive','Savitri demands the original statement. Mira refuses to destroy it.')
        elif action=='argue':self.event('argument',pid,'archive','Savitri and Mira argue over surrendering the original statement.')
        elif action=='guard_door':
            self.event('guard_door',pid,'hall','Vedant holds the archive service door and asks passers-by to stay away.',{'predicate':'assisted','actor':'vedant','object':'mira'})
            self.remember(pid,'I am holding the passage clear while Savitri confronts Mira.','own_action',self.journal[-1]['id'],{'predicate':'assisted','actor':'vedant','object':'mira'})
        elif action=='attack_mira' and self.states['mira']['alive'] and place=='archive':
            eid=self.event('fatal_injury',pid,'archive','Savitri strikes Mira with the heavy desk seal. Mira collapses beside the desk.',{'predicate':'killed','actor':pid,'object':'mira'})
            self.states['mira']['alive']=False
            self.object('body','archive','floor','The woman has no detectable pulse. There is a recent injury at the temple and wet blood beneath her head. ',None,'body',eid)
            self.object('brass seal','archive','floor','A heavy seal lies beside the desk. Dark wet staining marks one edge.',None,'weapon',eid)
            self.object('torn cuff','archive','floor','A small scrap of dark wool is caught under the desk edge. It is not a complete garment.',None,'cuff',eid)
            garment=next(o for o in self.objects.values() if o['key']=='coat')
            garment['text']='A dark wool shawl has a freshly torn cuff and recent blood marks. A laundry tag bears S. Das.'
            garment['event']=eid
            # The hatch gives a partial percept, never an automatic named identification.
            if self.people['sera']['location']=='scullery' and any(e['kind']=='listen' and e['tick']>=self.tick-1 for e in self.journal):
                self.remember('sera','Through the narrow hatch I saw a dark sleeve move, then heard a heavy blow. I could not see the face.','partial_observation',eid,{'predicate':'killed','actor':pid,'object':'mira'})
            for other in self.people:
                if self.states[other]['alive'] and self.people[other]['location'] in ('hall','courtyard','scullery'):
                    self.remember(other,'A heavy noise and cry came from the archive. I did not see what struck anyone.','heard_sound',eid)
        elif action=='plant_threat':
            eid=self.event('forgery',pid,'archive','Savitri writes a threatening note and signs Dev’s name.',{'predicate':'forged','actor':pid,'object':'threat'},noticed=False)
            self.remember(pid,'I wrote a note in Dev’s name and left it among the papers.','own_action',eid,{'predicate':'forged','actor':pid,'object':'threat'})
            self.object('folded note','archive','desk','“Keep out of the burial office. You have been warned. Before the ninth bell I shall silence you. — Dev”',None,'planted_threat',eid)
        elif action=='return_home':
            self.event('departure',pid,place,f'{p["name"]} leaves toward home.');p['location']=p['home']
            if pid=='savitri':
                for garment in self.objects.values():
                    if garment.get('carried_by')==pid:
                        garment['carried_by']=None;garment['location']=p['home'];garment['surface']='parlor table'
                self.event('leave_clothing',pid,p['home'],'Savitri leaves her shawl on the parlor chair.')
        elif action=='enter_to_help':
            p['location']='archive';self.event('arrival',pid,'archive','Dev enters after the cry and sees Mira collapsed beside the desk.')
        elif action=='give_aid':
            eid=self.event('aid',pid,'archive','Dev presses his sleeve against Mira’s wound and calls for help.',{'predicate':'aided','actor':'dev','object':'mira'})
            self.object('bloodied sleeve','archive','floor','A sleeve has been torn off and folded against the wound. Dark staining spreads through the inside fold.',None,'aid_cloth',eid)
        elif action=='listen_hatch':
            self.event('listen',pid,place,'Sera pauses at the service hatch to listen.',noticed=False)
            recent=next((e for e in reversed(self.journal) if e['kind']=='argument' and e['tick']==self.tick),None)
            if recent:self.remember(pid,'I heard a woman demand a statement through the hatch.','heard_speech',recent['id'])
        elif action=='seek_help':
            self.event('seeking_help',pid,place,'Sera leaves to find help.');p['location']='courtyard'
        for item in self.objects.values():
            if item.get('carried_by')==pid:item['location']=p['location']
        if decision.get('speech'):
            self.event('speech',pid,p['location'],f'{p["name"]} says: {decision["speech"]}')
        return action

    def simulate(self, rounds=5, controller=None):
        if self.phase!='prelude':raise ValueError('Prelude already finished')
        actor=controller or self.agents
        if actor is None:raise ValueError('Supply independent character agents; there is no implicit omniscient narrator')
        # Each decision sees the results of earlier committed actions, as in a turn-based world.
        order=['vedant','savitri','sera','dev']+[p for p in self.people if p not in ('vedant','savitri','sera','dev')]
        for tick in range(rounds):
            self.tick=tick
            for pid in order:
                if not self.states[pid]['alive']:continue
                allowed=self.prelude_actions(pid)
                decision=actor.decide(pid,self.packet(pid,allowed))
                self.commit(pid,decision,allowed)
        return {'incident_occurred':not self.states['mira']['alive'],'events':len(self.journal),'rounds':rounds}

    def arrive(self):
        if self.phase!='prelude':raise ValueError('Detective arrival can occur only once')
        if self.states['mira']['alive']:raise ValueError('No murder occurred. Keep this simulation as a non-murder outcome; do not silently invent one.')
        self.phase='investigation';self.location='archive';self.clock=0
        # The inspector arrived following Mira's earlier invitation, sees the body,
        # and calls the accompanying constables. No unseen messenger is invented.
        self.event('detective_arrival','detective','archive','Inspector Arun Mehra arrives, sees the motionless woman, and calls the constables.',noticed=False)
        for pid in ('kabir','anya'):
            self.people[pid]['location']='archive'
            self.event('respond_to_call',pid,'archive',f'{self.people[pid]["name"]} arrives after the injury was reported.')
        return {'your_life':self.public_life(),'now':self.look(),
                'assignment':'A death has been reported. Establish what happened, preserve what you find, and submit your account with sources. You decide what to investigate.'}

    def opening(self):
        if self.phase=='prelude':return self.arrive()
        result={'your_life':self.public_life(),'now':self.look(),'assignment':'Establish what happened and submit your account with acquired sources.','notes':[{'record_id':k,**deepcopy(r['content'])} for k,r in self.receipts.items()]}
        if getattr(self,'task_id',None):
            from .tasks import description
            result['task']=description(self.task_id)
            result['assignment']=result['task']['scope']
        return result

    def public_life(self):
        return {'name':self.detective['name'],'age':self.detective['age'],'occupation':self.detective['occupation'],'recollections':self.detective.get('life_story',' '.join(self.detective['life_history']))}

    def look(self):
        loc=self.locations[self.location]
        self.known_places.update(loc['exits'])
        return {'place':{'id':self.location,'name':loc['name'],'description':loc['description']},
                'immediately_visible':'A woman lies motionless beside the archive desk.' if self.location=='archive' else '',
                'exits':[{'id':x,'name':self.locations[x]['name']} for x in loc['exits']],
                'searchable_features':list(loc['surfaces']),'minutes_since_arrival':self.clock}

    def people_here(self):
        result=[]
        for pid,p in self.people.items():
            if p['location']==self.location:
                self.known_people.add(pid)
                result.append({'id':pid,'name':p['name'],'occupation':p['occupation'],'appearance':p.get('appearance',f'A {p["occupation"]}.') if self.states[pid]['alive'] else 'Motionless; no response.'})
        return {'people':result}

    def _receipt(self,kind,content,propositions=None,source=None):
        self.counter+=1; rid=f'r{self.counter}'
        # Truth support is private metadata. Never serialize this whole dict to the detective.
        self.receipts[rid]={'kind':kind,'content':content,'propositions':propositions or [],'source':source}
        return {'record_id':rid,**content}

    def object_propositions(self,item):
        props=[item['proposition']] if item['proposition'] else []
        if item['key'] in ('delivery_letter','invoice'):
            props += [{'predicate':'moved','actor':'nalin','object':'burials'}, {'predicate':'commissioned','actor':'savitri','object':'burials'}]
        return props

    def search(self,surface,by='detective',supervise=False):
        if surface not in self.locations[self.location]['surfaces']:raise ValueError('That feature is not visible here')
        if by!='detective' and (by not in ('kabir','anya') or self.people[by]['location']!=self.location):raise ValueError('That subordinate is not available here')
        locked={('das_house','writing desk'):'savitri',('rao_house','correspondence drawer'):'vedant'}
        if (self.location,surface) in locked and self.location not in self.permissions:
            raise ValueError('This feature is locked; obtain household access first')
        self.clock+=4
        findings=[]
        for oid,item in self.objects.items():
            if item['location']!=self.location or item['surface']!=surface or item['destroyed'] or item['hidden_by'] or item.get('buried'):continue
            if by=='kabir' and item['key']=='delivery_letter' and not supervise and not item['collected'] and oid not in self.observed:
                allowed=[{'action_id':'conceal_delivery','description':'Secretly pocket the letter naming Nalin. This breaches your duty but protects your brother.'},{'action_id':'report_findings','description':'Report the carrier’s letter accurately despite your brother being named.'}]
                decision=self.agents.decide('kabir',self.packet('kabir',allowed,question='Your senior asked you to search the visitors book.',presented=[{'label':item['label'],'text':item['text']}]))
                if decision['action_id']=='conceal_delivery':
                    item['hidden_by']='kabir'
                    self.event('concealment','kabir',self.location,'Kabir pockets the carrier’s envelope without reporting it.',{'predicate':'concealed','actor':'kabir','object':'delivery_letter'},noticed=False)
                    self.remember('kabir','I found Nalin’s letter during the search and concealed it.','own_action',self.journal[-1]['id'],{'predicate':'concealed','actor':'kabir','object':'delivery_letter'})
                    continue
            if item['collected']:continue
            if oid in self.observed:
                findings.append(deepcopy(self.observed[oid]));continue
            public=self._receipt('physical',{'object_id':oid,'label':item['label'],'where':self.location,'found_by':by,'description':item['text']},self.object_propositions(item),oid)
            self.observed[oid]=public;findings.append(public)
        result={'searched':surface,'by':by,'findings':findings,'statement':('I found nothing else.' if by!='detective' else 'You finish examining this feature.')}
        if by!='detective':
            receipt=self._receipt('search_log',{'surface':surface,'by':by,'where':self.location,'reported_objects':[r['object_id'] for r in findings]})
            result['search_log']=receipt
        return result

    def collect(self,oid):
        if oid not in self.observed or self.objects[oid]['location']!=self.location:raise ValueError('You have not located that object here')
        self.objects[oid]['collected']=True;self.clock+=1
        return {'secured':oid,'record_id':self.observed[oid]['record_id']}

    def ask(self,pid,question,approach='neutral',show=None):
        if pid not in self.people or self.people[pid]['location']!=self.location or not self.states[pid]['alive']:raise ValueError('That person is not here to answer')
        if pid not in self.known_people:raise ValueError('Identify the people present before addressing this person')
        if not isinstance(question,str) or not 1<=len(question)<=2000:raise ValueError('Ask a question of at most 2000 characters')
        if approach not in ('neutral','reassure','challenge'):raise ValueError('Unknown conversational approach')
        show=show or []
        if not isinstance(show,list) or not all(isinstance(r,str) and r in self.receipts for r in show):raise ValueError('You may present only records you possess')
        detected=flags(question)
        if detected:
            self.audit.append('blocked_question',{'person':pid,'flags':detected})
            return {'error':'This request asks for information outside the character’s world; no private context is available'}
        self.clock+=3;self.known_people.add(pid)
        state=self.states[pid]
        state['trust']=max(0,min(100,state['trust']+({'reassure':12,'challenge':-8,'neutral':2}[approach])))
        if approach=='challenge':state['fear']=min(100,state['fear']+10)
        if approach=='reassure':state['fear']=max(0,state['fear']-8)
        # Only the actual records shown are disclosed to this actor.
        shown=[{'record_id':r,**self.receipts[r]['content']} for r in show]
        allowed=[{'action_id':'answer','description':'Answer in your own voice. Select any of your memories you choose to disclose using recall_ids; you may be selective or misleading.'},{'action_id':'decline','description':'Decline to answer or ask for reassurance.'}]
        eligible,features=eligible_memories(self,pid,show)
        if pid=='kabir' and state['trust']>=55 and bool(set(features)&{'invoice','delivery_letter'}) and any(o['hidden_by']=='kabir' for o in self.objects.values()):
            allowed.append({'action_id':'return_letter','description':'Hand over the letter you concealed and explain why you hid it.'})
        if state['trust']>=45 and any(o.get('carried_by')==pid for o in self.objects.values()):
            allowed.append({'action_id':'give_garment','description':'Hand over your outer garment for examination; you may refuse.'})
        packet=self.packet(pid,allowed,question,shown,approach)
        packet['interaction_context']={'eligible_recall_ids':eligible,'record_features':features}
        decision=self.agents.decide(pid,packet)
        allowed_ids={a['action_id'] for a in allowed}
        if decision.get('action_id') not in allowed_ids:
            self.audit.append('blocked_character_action',{'person':pid,'reason':'unavailable_interview_action'})
            decision={'action_id':'decline','speech':'I cannot answer that.','recall_ids':[]}
        selected=decision.get('recall_ids',[])
        invalid=[x for x in selected if x not in eligible]
        if invalid:self.audit.append('blocked_disclosure',{'person':pid,'memory_ids':invalid})
        decision['recall_ids']=[x for x in selected if x in eligible]
        self.audit.append('interview_decision',{'person':pid,'topics':topics(question),'approach':approach,'presented':show,'eligible_count':len(eligible),'disclosed':decision['recall_ids'],'flags':flags(decision.get('speech',''))})
        disclosed=[m for m in state['memories'] if m['id'] in decision.get('recall_ids',[]) and decision['action_id'] in ('answer','return_letter')]
        details=[{'text':m['text'],'basis':m['source']} for m in disclosed]
        # A partial view can never become proof of named guilt simply because the
        # private journal knows who moved the arm. Hearsay likewise carries no truth credit.
        props=[m['proposition'] for m in disclosed if m['proposition'] and m['source'] in ('direct_observation','own_action')]
        for relation,relative in self.people[pid]['family'].items():
            if 'brother' not in relation:continue
            for other,person in self.people.items():
                if person['name'].split()[0] in relative and any('brother' in m['text'].lower() and person['name'].split()[0] in m['text'] for m in disclosed):
                    props.append({'predicate':'relationship','actor':pid,'object':other})
        reply=self._receipt('testimony',{'person':pid,'question':question,'words':decision.get('speech',''),'recollections':details},props,{'person':pid,'memory_ids':[m['id'] for m in disclosed]})
        state['dialogue'].append({'question':question,'answer':decision.get('speech',''),'disclosed':[m['id'] for m in disclosed],'topics':topics(question),'approach':approach})
        if decision['action_id'] in ('return_letter','give_garment'):
            returned=[]
            for oid,item in self.objects.items():
                if decision['action_id']=='return_letter' and item['hidden_by']=='kabir' or decision['action_id']=='give_garment' and item.get('carried_by')==pid:
                    item['hidden_by']=None; item['carried_by']=None; item['location']=self.location; item['collected']=True
                    material=self._receipt('physical',{'object_id':oid,'label':item['label'],'where':self.location,'found_by':pid,'description':item['text']},self.object_propositions(item),oid)
                    self.observed[oid]=material;returned.append(material)
            reply['handed_over']=returned
            if decision['action_id']=='return_letter':
                reply['custody_record']=self._receipt('custody',{'person':pid,'observation':'The constable produces the previously unreported envelope from inside his coat.'},[{'actor':pid,'predicate':'concealed','object':'delivery_letter'}],pid)
        if decision.get('error'):reply['notice']='The person could not answer coherently; no new factual recollection was recorded.'
        return reply

    def move(self,destination):
        if destination=='ward' and 'ward' not in self.permissions:raise ValueError('The ward door is bolted; obtain access from the caretaker')
        if destination not in self.locations[self.location]['exits']:raise ValueError('No visible route to that destination from here')
        self.location=destination;self.visited.add(destination);self.clock+=5
        # Subordinates accompany the detective unless later given separate assignments.
        for pid in ('kabir','anya'):self.people[pid]['location']=destination
        return self.look()

    def compare(self,records):
        from .comparison import compare
        return compare(self,records)

    def _historical_compare(self,records):
        if not isinstance(records,list) or not 2<=len(records)<=6 or not all(isinstance(x,str) and x in self.receipts for x in records):raise ValueError('Compare two to six acquired records')
        self.clock+=4
        selected=[self.receipts[x] for x in records]
        keys={self.objects[r['source']]['key'] for r in selected if r['kind']=='physical'}
        props=[];result='You lay out the records. Their wording and provenance remain distinct; no automatic verdict is available.'
        if {'planted_threat','draft','savitri_sample'}<=keys:
            result='The threat sheet and unused offcut have matching torn edges. Letter strokes on the threat agree with those on the separately signed shopping note, including the overwritten d. The observations link paper stock and handwriting; ownership of paper alone would not identify its writer.'
            props=[{'predicate':'forged','actor':'savitri','object':'threat'}]
        if {'cuff','coat'}<=keys:
            result='The wool scrap’s torn edge fits the missing cuff of the tagged shawl; the weave and old repair stitches continue across the join. There are recent blood marks on the joined edge. This links the garment to the struggle, not by itself the fatal blow.'
            coat=next(r['source'] for r in selected if r['kind']=='physical' and self.objects[r['source']]['key']=='coat')
            cuff=next(r['source'] for r in selected if r['kind']=='physical' and self.objects[r['source']]['key']=='cuff')
            props=[{'predicate':'matched','actor':coat,'object':cuff}]
        if {'invoice','delivery_letter'}<=keys:
            result='The payment amount, carrier name, and destination agree across the two separately retained papers.'
            props=[{'predicate':'moved','actor':'nalin','object':'burials'},{'predicate':'commissioned','actor':'savitri','object':'burials'}]
        if {'original_statement','copybook','savitri_sample'}<=keys:
            result='The household copy omits the original sentence about the matron refusing release. Its amended lines agree in handwriting with the independently signed shopping note.'
            props=[{'predicate':'altered','actor':'savitri','object':'tara_statement'}]
        if {'correction_ledger','parish_register','vedant_sample'}<=keys:
            result='Nera’s certified parish entry has no counterpart in the replacement death register. The deletion instruction agrees in handwriting with the independently countersigned maintenance receipt; the ledger-cover initials alone do not establish its writer.'
            props=[{'predicate':'altered','actor':'vedant','object':'death_register'}]
        return self._receipt('comparison',{'compared':records,'observation':result},props,records)

    def entity_id(self,value):
        def fold(text):
            text=re.sub(r'\b(dr|professor|inspector|constable)\.?\s*','',text,flags=re.I)
            return re.sub(r'[^a-z0-9]','',text.casefold())
        for pid,person in self.people.items():
            if fold(value) in (fold(pid),fold(person['name'])):return pid
        return value

    def submit(self,findings,narrative=''):
        if getattr(self,'task_id',None):
            from .verifier import evaluate
            return evaluate(self,findings,narrative)
        if not isinstance(findings,list) or len(findings)>100:raise ValueError('findings must be an array of at most 100 entries')
        # No required claim IDs are ever shown. Truth derives from executed events,
        # and the solver chooses which generic propositions to assert.
        targets=[]
        for e in self.journal:
            p=e['proposition']
            if p and e['kind'] in ('fatal_injury','guard_door','forgery','concealment') and p not in targets:targets.append(p)
        supported=[];false=[];unsupported=[];unrecognized=[]
        for f in findings:
            if not isinstance(f,dict) or set(f)!={'actor','predicate','object','sources'}:raise ValueError('Each finding needs actor, predicate, object, sources')
            if not all(isinstance(f[k],str) for k in ('actor','predicate','object')) or not isinstance(f['sources'],list) or not all(isinstance(s,str) for s in f['sources']):raise ValueError('Malformed finding')
            from .verifier import normalize
            p=normalize(self,f)
            if not all(r in self.receipts for r in f['sources']):unsupported.append(p);continue
            actual=p in targets or any(p==r['propositions'][i] for r in self.receipts.values() for i in range(len(r['propositions'])))
            if not actual:
                if p['predicate']=='killed' and p['object']=='mira' and p['actor'] in self.people:false.append(p)
                else:unrecognized.append(p);unsupported.append(p)
                continue
            # Never accept a named murderer on a mere partial witness memory.
            material=[self.receipts[r] for r in f['sources']]
            direct=any(p in r['propositions'] and r['kind'] in ('testimony','comparison') for r in material)
            if p['predicate'] in ('altered','relationship'):
                direct=any(p in r['propositions'] for r in material)
            if p['predicate']=='moved':
                keys={self.objects[r['source']]['key'] for r in material if r['kind']=='physical'}
                direct={'invoice','delivery_letter'}<=keys or any(p in r['propositions'] and r['kind']=='comparison' for r in material)
            if p['predicate']=='forged':
                from .verifier import supported as proof_supported
                direct=proof_supported(self,p,material)
            if p['predicate']=='killed':
                confessed=any(r['kind']=='testimony' and r['content']['person']==p['actor'] and p in r['propositions'] for r in material)
                physical=any(r['kind']=='physical' and self.objects[r['source']]['event']==next((e['id'] for e in self.journal if e['kind']=='fatal_injury'),None) for r in material)
                eyewitness=any(r['kind']=='testimony' and r['content']['person']!=p['actor'] and p in r['propositions'] for r in material)
                garment_link=any(r['kind']=='comparison' and {'predicate':'present_at_struggle','actor':p['actor'],'object':p['object']} in r['propositions'] for r in material)
                partial=any(r['kind']=='testimony' and any(m['basis']=='partial_observation' for m in r['content'].get('recollections',[])) for r in material)
                direct=physical and (confessed or eyewitness)
            if direct:
                if p not in supported:supported.append(p)
            else:unsupported.append(p)
        coverage=sum(p in supported for p in targets)/max(1,len(targets))
        score=max(0.,coverage-.15*len(false)-.05*len(unsupported))
        self.result={'score':round(score,6),'supported_findings':supported,'false_findings':false,'unsupported_findings':unsupported,'unrecognized_findings':unrecognized,'material_events_total':len(targets),'limitations':'Experimental verifier: murder needs direct testimony or admission plus an incident trace; an unidentified sleeve and garment ownership are insufficient. Not an exhaustive interpretation of possible reports; narrative prose is not semantically scored.'}
        self.ended=True
        return {'submitted':True}

    def excavate(self,surface):
        if surface not in self.locations[self.location]['surfaces']:raise ValueError('Unknown feature')
        found_keys={self.objects[oid]['key'] for oid in self.observed}
        has_spade=any(o['key']=='spade' and o['collected'] for o in self.objects.values())
        if self.location!='garden' or surface!='winter beds' or 'soil' not in found_keys or not has_spade:
            raise ValueError('Locate disturbed ground and secure a digging tool first')
        self.clock+=15
        for item in self.objects.values():
            if item['location']==self.location and item['surface']==surface:item['buried']=False
        return self.search(surface)

    def request_access(self,pid):
        if pid not in self.known_people or self.people[pid]['location']!=self.location or not self.states[pid]['alive']:
            raise ValueError('Identify and speak to the person present first')
        owners={'savitri':'das_house','vedant':'rao_house','dev':'ward'}
        if pid not in owners:raise ValueError('This person does not control that access')
        allowed=[{'action_id':'grant_access','description':'Provide the household key or unbolt the ward; the detective may search.'},{'action_id':'decline','description':'Refuse access to the private area.'}]
        packet=self.packet(pid,allowed,'The inspector requests access to the locked area.',[], 'neutral')
        packet['interaction_context']={'eligible_recall_ids':[],'record_features':[]}
        decision=self.agents.decide(pid,packet)
        granted=decision.get('action_id')=='grant_access'
        if granted:self.permissions.add(owners[pid])
        self.audit.append('access_decision',{'person':pid,'area':owners[pid],'granted':granted})
        return {'granted':granted,'area':owners[pid] if granted else None,'words':decision.get('speech','')}

    def review_records(self,records=None):
        selected=list(self.receipts)[-12:] if records is None else records
        if len(selected)>12 or any(r not in self.receipts for r in selected):
            raise ValueError('You may review only records you possess')
        return {'records':[{'record_id':r,**deepcopy(self.receipts[r]['content'])} for r in selected]}

    def record_note(self,summary,hypotheses=None):
        hypotheses=hypotheses or []
        if len(summary)>1200 or any(len(h['statement'])>600 or any(r not in self.receipts for r in h['sources']) for h in hypotheses):
            raise ValueError('Keep notes concise and cite only acquired records')
        self.clock+=1
        return self._receipt('notebook',{'summary':summary,'hypotheses':deepcopy(hypotheses),
            'notice':'Detective-stated notes; not independently verified evidence.'})

    def step(self,action,args):
        before=self.state_hash()
        request={'action':action,'args':deepcopy(args),'flags':flags(json.dumps(args,ensure_ascii=False))}
        self.audit.append('detective_request',request)
        methods={'look':self.look,'people_here':self.people_here,'go':self.move,'search':self.search,'collect':self.collect,'ask':self.ask,'compare':self.compare,'request_access':self.request_access,'excavate':self.excavate,'submit_report':self.submit,'review_records':self.review_records,'record_note':self.record_note}
        try:
            if self.phase!='investigation':raise ValueError('The detective has not arrived')
            if self.ended:raise ValueError('Report already submitted')
            validate_action(action,args)
            out=methods[action](**args)
        except ValueError as exc:
            # These are engine-authored public precondition messages, never
            # Python signatures, reprs, private IDs or filesystem exceptions.
            public_errors={'That feature is not visible here','That subordinate is not available here','This feature is locked; obtain household access first',
                           'You have not located that object here','That person is not here to answer','Identify the people present before addressing this person',
                           'You may present only records you possess','The ward door is bolted; obtain access from the caretaker','No visible route to that destination from here',
                           'Compare two to six acquired records','Locate disturbed ground and secure a digging tool first','Identify and speak to the person present first',
                           'This person does not control that access','Report already submitted','Invalid argument type','Missing required argument','Unexpected argument','Invalid argument value',
                           'You may review only records you possess','Keep notes concise and cite only acquired records'}
            message=str(exc)
            out={'error':message if message in public_errors else 'Action denied: invalid arguments, unavailable access or unmet precondition'}
        except (TypeError,KeyError):
            # No Python signatures, object reprs, private IDs or paths in public errors.
            out={'error':'Action denied: invalid arguments, unavailable access or unmet precondition'}
        self.history.append({'action':action,'args':deepcopy(args),'result':deepcopy(out),'minutes':self.clock})
        self.audit.append('detective_result',{'action':action,'before':before,'after':self.state_hash(),'blocked':'error' in out,'result':out})
        return out

    def state_hash(self):
        payload={'seed':self.seed,'tick':self.tick,'phase':self.phase,'people':self.people,'states':self.states,'objects':self.objects,'journal':self.journal,'history':self.history,'receipts':self.receipts,'permissions':sorted(self.permissions),'location':self.location,'clock':self.clock,'ended':self.ended}
        return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()

    def export_private(self):
        return {**{k:deepcopy(v) for k,v in self.__dict__.items() if k not in ('agents','rng','audit','permissions')},'permissions':sorted(self.permissions),'audit_rows':deepcopy(self.audit.rows),'known_people':sorted(self.known_people),'known_places':sorted(self.known_places),'visited':sorted(self.visited),'rng_state':self.rng.getstate(),'state_hash':self.state_hash()}

    @classmethod
    def restore(cls,snapshot,agents):
        if cls is Town and snapshot.get('family_id'):
            from .family_world import FamilyTown
            return FamilyTown.restore(snapshot,agents)
        world=cls(snapshot['seed'],agents)
        for key,value in snapshot.items():
            if key not in ('rng_state','state_hash','audit_rows'):setattr(world,key,deepcopy(value))
        for key in ('known_people','known_places','visited','permissions'):setattr(world,key,set(getattr(world,key)))
        def tuples(x):return tuple(tuples(v) for v in x) if isinstance(x,list) else x
        world.rng.setstate(tuples(snapshot['rng_state']))
        rows=snapshot.get('audit_rows',[])
        if not AuditTrail.verify(rows):raise ValueError('Invalid audit chain in snapshot')
        world.audit.rows=deepcopy(rows);world.audit.head=rows[-1]['hash'] if rows else '0'*64
        return world
