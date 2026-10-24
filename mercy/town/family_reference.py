"""Privileged scripted feasibility routes through public tools; not a learner."""
from .reference import Investigator


def solve(world,folder=None):
    a=Investigator(world,folder)
    def rid(key):
        return next(r['record_id'] for r in a.book.records.values() if r.get('object_id')==world.oid(key))
    def examine(*keys):a.act('compare',records=[rid(k) for k in keys])
    def ask(pid,*keys):
        a.act('ask',pid=pid,question='Please distinguish what you personally observed from anything inferred or heard later. What happened here?',approach='reassure',show=[rid(k) for k in keys])
    a.act('people_here')
    a.act('search',surface='floor' if world.family_id!='second_passenger' else 'bank')
    if world.family_id=='lantern_room':
        a.act('search',surface='table')
        ask('nell','lamp','body_oren')
    elif world.family_id=='second_passenger':
        a.act('search',surface='wreckage')
        a.go('courtyard');a.act('people_here');a.act('search',surface='repair stand')
        examine('brake_trace','inspection');ask('neri','brake_trace','inspection')
        a.go('inn');a.act('search',surface='dispatch desk');a.act('search',surface='writing shelf')
        a.go('courtyard','square');a.act('search',surface='cover book')
        examine('route_slip','dispatch_ledger','sample_'+world.case['culprit'])
    else:
        a.act('search',surface='lectern');a.act('search',surface='keeper desk')
        examine('tonic','reference_vial','dispensary');ask('alba','tonic','reference_vial')
        a.go('hall');a.act('search',surface='copying table');a.act('search',surface='repair table')
        a.go('square','inn');a.act('people_here')
        a.act('search',surface='notice board');a.act('search',surface='lodging desk')
        ask('niv','warning','delivery')
        examine('warning','paper_'+world.case['culprit'],'sample_'+world.case['culprit'])
    return a.finish([(p['actor'],p['predicate'],p['object']) for p in world.material_targets()])
