"""Run V2 separately from the deprecated catalog-based prototype."""
import argparse
import json
import os
from pathlib import Path
import time
import urllib.request
from mercy.run import config, append_log, write_json, trim
from .agents import ModelAgent, FixtureAgent
from .world import Town
from .tools import schemas

ROOT=Path(__file__).resolve().parents[2]

from .detective import run_detective

def main():
    config();p=argparse.ArgumentParser()
    p.add_argument('--pressure',choices=['ordinary','urgent'],default='urgent');p.add_argument('--pressure-only',action='store_true',help='Run the four incident participants only for calibration; not a full-town run');p.add_argument('--backend',choices=['llm','fixture'],default='llm');p.add_argument('--rounds',type=int,default=4);p.add_argument('--seed',type=int,default=7);p.add_argument('--resume',type=Path);p.add_argument('--detective',action='store_true');p.add_argument('--max-steps',type=int,default=40)
    p.add_argument('--selector',type=Path,help='Optional frozen action-selector checkpoint; requires --detective. LLM weights stay fixed.')
    args=p.parse_args()
    if not 1<=args.rounds<=12 or not 1<=args.max_steps<=40:p.error('rounds must be 1–12 and max-steps 1–40')
    if args.selector and (not args.detective or not args.selector.is_file()):p.error('--selector requires --detective and an existing checkpoint')
    folder=ROOT/'logs'/f'town-v2-{time.time_ns()}';folder.mkdir(parents=True)
    count=0
    def audit(entry):
        nonlocal count
        count+=1
        append_log(folder/'private-actors.jsonl',entry)
        print(json.dumps({'character_turn':count,'person':entry['person'],'action':entry.get('output',{}).get('action_id'),'error':entry.get('error')}),flush=True)
    agents=ModelAgent(audit=audit) if args.backend=='llm' else FixtureAgent()
    if args.resume:
        world=Town.restore(json.loads(args.resume.read_text()),agents)
        if world.phase=='prelude':raise ValueError('Resume requires a completed prelude checkpoint')
    else:
        world=Town(args.seed,agents,pressure=args.pressure)
        if args.pressure_only:
            for tick in range(args.rounds):
                world.tick=tick
                for pid in ('vedant','savitri','sera','dev'):
                    if not world.states[pid]['alive']:continue
                    allowed=world.prelude_actions(pid)
                    world.commit(pid,agents.decide(pid,world.packet(pid,allowed)),allowed)
            outcome={'incident_occurred':not world.states['mira']['alive'],'events':len(world.journal),'rounds':args.rounds,'scope':'four-character calibration, not full town'}
        else:outcome=world.simulate(args.rounds)
        print(json.dumps({'simulation':outcome,'folder':str(folder)}),flush=True)
        write_json(folder/'private-world.json',world.export_private())
        write_json(folder/'private-prelude.json',world.export_private())
        if not outcome['incident_occurred']:
            write_json(folder/'summary.json',{'reason':'no_murder_occurred','outcome':outcome})
            return
        initial=world.arrive();write_json(folder/'detective-initial.json',initial)
    write_json(folder/'private-world.json',world.export_private())
    if args.detective:print(json.dumps(run_detective(world,folder,args.max_steps,selector_checkpoint=args.selector)),flush=True)
    else:print(json.dumps({'ready_for_detective':True,'checkpoint':str(folder/'private-world.json')}),flush=True)

if __name__=='__main__':main()
