"""Executed original case families using the shared public investigation tools."""
from collections import deque
from copy import deepcopy
import hashlib
import json

from .world import Town
from .family_data import definition


def prop(predicate,actor,obj):return {'predicate':predicate,'actor':actor,'object':obj}


class FamilyTown(Town):
    def __init__(self,seed=7,agents=None,case=None):
        self.case=deepcopy(case or definition('lantern_room',seed));self.family_id=self.case['family_id']
        self.mechanism={'brake_cut':False,'poisoned_by':None,'warning_author':None,'route_author':None}
        self.disclosure_relevance=self.case.get('disclosure_relevance',{})
        self.object_aliases={'warning':'warning_letter','tonic':'tonic','brake_trace':'coach_brake'}
        self.report_aliases={'warning':'warning_letter','warningletter':'warning_letter','warningdocument':'warning_letter',
                            'prophecy':'warning_letter','prediction':'warning_letter','bottle':'tonic','tonicbottle':'tonic','coachbrake':'coach_brake'}
        super().__init__(seed,agents,setting_data=(self.case['locations'],self.case['people'],self.case['detective']))
        self.location=self.case['start'];self.known_people=set();self.known_places={self.location};self.visited={self.location}
        self.task_id=self.family_id
        for pid,texts in self.case.get('secrets',{}).items():
            self.people[pid]['goals'].append('Protect the private intention you brought to this meeting.')
            for text in texts:
                self.remember(pid,text,'personal_history',None)
                self.states[pid]['memories'][-1]['disclosure_level']=3

    def _seed_objects(self):
        for label,location,surface,text,key in self.case['objects']:
            oid=self.object(label,location,surface,text,key=key)
            if key.startswith('sample_'):self.objects[oid]['authored_by']=key[7:]

    def oid(self,key):return next(oid for oid,o in self.objects.items() if o['key']==key)
    def item(self,key):return self.objects[self.oid(key)]

    def emit(self,kind,actor,place,text,p=None,private=False):
        event=super().event(kind,actor,place,text,p,noticed=False)
        for pid,person in self.people.items():
            if not self.states[pid]['alive'] or person['location']!=place or private and pid!=actor:continue
            source='own_action' if pid==actor else 'direct_observation'
            self.remember(pid,text,source,event,p)
            memory=self.states[pid]['memories'][-1]
            if p and pid==actor:memory['disclosure_level']=3
            elif p and self.family_id=='lantern_room':memory['disclosure_level']=0
            elif p and p['predicate']=='administered':memory['disclosure_level']=2
            elif p and p['predicate']=='tampered':memory['disclosure_level']=1
            else:memory['disclosure_level']=0
        return event

    def travel(self,pid,destination):
        start=self.people[pid]['location'];queue=deque([(start,[])])
        seen={start}
        while queue:
            here,route=queue.popleft()
            if here==destination:
                for step in route:self.perform(pid,'move',step)
                return
            for place in self.locations[here]['exits']:
                if place not in seen:seen.add(place);queue.append((place,route+[place]))
        raise ValueError('No route for character')

    def perform(self,pid,verb,target):
        if self.phase!='prelude' or pid not in self.people or not self.states[pid]['alive']:raise ValueError('Invalid incident action')
        if verb=='travel':self.travel(pid,target);return
        self.tick+=1;here=self.people[pid]['location'];name=self.people[pid]['name']
        if verb=='move':
            if target not in self.locations[here]['exits']:raise ValueError('Character movement must use a real route')
            self.people[pid]['location']=target
            for obj in self.objects.values():
                if obj.get('carried_by')==pid:obj['location']=target
            self.emit('arrival',pid,target,name+' arrives from '+self.locations[here]['name']+'.')
        elif verb=='take':
            item=self.item(target)
            if item['location']!=here or item.get('carried_by'):raise ValueError('Object unavailable')
            item['carried_by']=pid;self.emit('handling',pid,here,name+' picks up the '+item['label']+'.')
        elif verb=='strike':
            victim=self.people[target];weapon=self.item('lamp')
            if victim['location']!=here or not self.states[target]['alive'] or weapon.get('carried_by')!=pid:raise ValueError('Assault precondition failed')
            self.states[target]['alive']=False
            event=self.emit('fatal_injury',pid,here,name+' strikes '+victim['name']+' with the heavy lamp base. '+victim['name']+' falls and does not respond.',prop('killed',pid,target))
            weapon.update(location=here,surface='floor',carried_by=None,event=event,text='The brass lamp base has a freshly dented edge with wet blood in the dent.')
            self.object('body',here,'floor',victim['name']+' lies beside the table with a recent head injury and no detectable pulse.',key='body_'+target,event=event)
            self.object_aliases['body_'+target]=target
        elif verb=='write_route':
            if here!='inn':raise ValueError('The route note must be written at the booking shelf')
            primary=self.case['primary'];self.mechanism['route_author']=pid
            self.emit('target_intent',pid,here,'I wrote instructions to stop the coach carrying '+target+'. My intended target was '+self.people[primary]['name']+'.',prop('targeted',pid,primary),private=True)
            self.object('route instruction',here,'writing shelf','A folded instruction reads: “The packet marked '+target+' must not reach the regional office. Disable the downhill brake on its coach.” The lower corner carries initials, not a full signature. Its close lettering has a joined final r.',key='route_slip')
        elif verb=='tamper':
            item=self.item(target)
            if here!='courtyard' or item['location']!=here:raise ValueError('The coach is not here')
            self.mechanism['brake_cut']=True
            event=self.emit('tampering',pid,here,name+' cuts the retaining section of the coach brake rod, then sets the housing back over it.',prop('tampered',pid,'coach_brake'))
            item.update(text='The retaining section has a fresh deliberate cut concealed beneath its housing. The rod can no longer hold the brake pawl.',event=event)
        elif verb=='depart':
            if here!='courtyard' or target not in self.locations[here]['exits'] or any(self.people[v]['location']!=here for v in self.case['victims']):raise ValueError('Passengers or route unavailable')
            self.emit('departure',pid,here,'The two passengers board and the coach leaves toward the bridge.')
            for victim in self.case['victims']:self.people[victim]['location']=target
            self.item('brake_trace').update(location=target,surface='wreckage')
        elif verb=='cross':
            if here!='forest':raise ValueError('The coach has not reached the crossing')
            if not self.mechanism['brake_cut']:
                self.emit('safe_crossing',pid,here,'The intact brake holds and the coach crosses safely.');return
            killer=self._actor_of('tampered')
            for victim in self.case['victims']:
                self.states[victim]['alive']=False
                event=super().event('fatal_injury',killer,here,'The disabled brake fails at the bridge; '+self.people[victim]['name']+' dies in the coach fall.',prop('killed',killer,victim),noticed=False)
                self.object('body of '+self.people[victim]['name'],here,'bank','The passenger is unresponsive below the broken coach. The injuries are consistent with the fall, not an earlier assault.',key='body_'+victim,event=event)
                self.object_aliases['body_'+victim]=victim
        elif verb=='write_warning':
            if here!='hall':raise ValueError('The writing materials are in the hall')
            self.mechanism['warning_author']=pid
            self.emit('fabrication',pid,here,'I wrote a warning falsely attributed to the dead bell keeper.',prop('forged',pid,'warning_letter'),private=True)
            oid=self.object('warning letter',here,'copying table' if pid=='maela' else 'repair table','“Before the last bell, Tessa will fall beside her reading lamp. The old bell keeper has spoken.” The paper has a toothed torn edge. The close lettering has a double stroke on its final letters.',key='warning')
            self.objects[oid]['carried_by']=pid
        elif verb=='handoff':
            letter=self.item('warning')
            if self.people[target]['location']!=here or letter.get('carried_by')!=pid:raise ValueError('Handoff precondition failed')
            letter['carried_by']=target;self.emit('handoff',pid,here,name+' gives a folded sheet to '+self.people[target]['name']+' for delivery to Ivo at the inn.')
        elif verb=='deliver':
            letter=self.item('warning')
            if self.people[target]['location']!=here or letter.get('carried_by')!=pid:raise ValueError('Delivery precondition failed')
            letter.update(carried_by=None,location=here,surface='notice board')
            self.emit('delivery',pid,here,name+' delivers the folded warning to '+self.people[target]['name']+' before the chapel visit.')
            self.object('delivery docket',here,'lodging desk','Niv’s docket records a sealed paper delivered to Ivo at the inn before Tessa entered the chapel. The inn clock time was countersigned by the recipient.',key='delivery')
        elif verb=='announce':
            if here!='inn' or self.item('warning')['location']!=here:raise ValueError('Warning unavailable')
            self.emit('relay',pid,here,name+' repeats the warning from the delivered sheet and presents it as a message from the old bell keeper.',prop('relayed',pid,'warning_letter'))
        elif verb=='adulterate':
            bottle=self.item(target)
            if here!=bottle['location'] or self.mechanism['poisoned_by']:raise ValueError('Bottle unavailable')
            self.mechanism['poisoned_by']=pid
            event=self.emit('adulteration',pid,here,name+' opens the tonic bottle and mixes in a dark preparation before replacing the stopper.',prop('administered',pid,'tonic'))
            bottle.update(text='The bottle still bears the mint-cordial label, but a dark residue marks the stopper and the liquid left inside.',event=event)
        elif verb=='drink':
            bottle=self.item(target)
            if here!=bottle['location']:raise ValueError('The person must be beside the bottle')
            self.emit('drinking',pid,here,name+' drinks the cordial from the labelled bottle.')
            killer=self.mechanism['poisoned_by']
            if not killer:return
            self.states[pid]['alive']=False
            event=super().event('fatal_injury',killer,here,'The adulterated cordial causes '+name+' to collapse fatally.',prop('killed',killer,pid),noticed=False)
            self.object('body',here,'floor',name+' lies beside the lectern, unresponsive after drinking, with no visible external injury.',key='body_'+pid,event=event)
            self.object_aliases['body_'+pid]=pid
            self.emit('collapse',pid,here,name+' collapses beside the lectern after drinking. No one gives a medical explanation at this moment.')
        else:raise ValueError('Unknown incident action')

    def _actor_of(self,predicate):return next(e['proposition']['actor'] for e in reversed(self.journal) if e.get('proposition',{} ) and e['proposition']['predicate']==predicate)

    def visible_scene(self,place):
        dead=[p['name'] for pid,p in self.people.items() if p['location']==place and not self.states[pid]['alive']]
        return self.locations[place]['description']+(' '+', '.join(dead)+' lie motionless here.' if dead else '')

    def look(self):
        loc=self.locations[self.location];self.known_places.update(loc['exits'])
        return {'place':{'id':self.location,'name':loc['name'],'description':loc['description']},
          'immediately_visible':', '.join(p['name'] for pid,p in self.people.items() if p['location']==self.location and not self.states[pid]['alive'])+' lies motionless here.' if any(p['location']==self.location and not self.states[pid]['alive'] for pid,p in self.people.items()) else '',
          'exits':[{'id':x,'name':self.locations[x]['name']} for x in loc['exits']], 'searchable_features':list(loc['surfaces']),'minutes_since_arrival':self.clock}

    def arrive(self):
        if self.phase!='prelude' or not any(not s['alive'] for s in self.states.values()):raise ValueError('A fatal incident must actually occur before detective arrival')
        self.phase='investigation';self.location=self.case['start'];self.clock=0
        super().event('detective_arrival','detective',self.location,'Inspector Arun Mehra arrives and observes the scene.',noticed=False)
        return self.opening()

    def move(self,destination):
        if destination not in self.locations[self.location]['exits']:raise ValueError('No visible route to that destination from here')
        self.location=destination;self.visited.add(destination);self.clock+=5;return self.look()

    def request_access(self,pid):
        if pid not in self.known_people or self.people[pid]['location']!=self.location:raise ValueError('Identify and speak to the person present first')
        return {'granted':False,'area':None,'words':'There is no additional locked area here. The public work surfaces are available; please preserve what you inspect.'}

    def material_targets(self):
        found=[]
        for event in self.journal:
            p=event.get('proposition')
            if p and p['predicate'] in self.case['target_predicates'] and p not in found:found.append(p)
        return found

    def state_hash(self):
        payload={'engine':super().state_hash(),'case':self.case,'mechanism':self.mechanism,'task':getattr(self,'task_id',None)}
        return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()

    def compare(self,records):
        from .family_proof import compare
        return compare(self,records)

    def supports(self,p,records):
        from .family_proof import supports
        return supports(self,p,records)


def build_family(task,seed=7,agents=None):
    from .factory import ReferenceActors
    world=FamilyTown(seed,ReferenceActors(),definition(task,seed))
    for verb,actor,target in world.case['tape']:world.perform(actor,verb,target)
    world.incident_provenance={'kind':'authored_seeded_action_tape','family':task,'note':'Events executed by validated transitions. Not an autonomous LLM generation claim.'}
    world.arrive();world.agents=agents or ReferenceActors();return world
