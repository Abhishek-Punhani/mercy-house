"""Bundle labeled public trajectories; never read private actor/world logs."""
import json
import re
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from mercy.town.factory import build
from mercy.town.reference import solve
from mercy.town.tasks import TASKS
from mercy.viewer.events import replay
from mercy.viewer.events import action_event, reply_event, verdict


def main():
    destination=ROOT/'viewer/data';destination.mkdir(parents=True,exist_ok=True)
    catalog=[]
    for task in ('lantern_room','second_passenger','bell_before_dawn'):
        world=build(task,37);initial=world.opening();folder=ROOT/'logs/viewer-family-references'/task;folder.mkdir(parents=True,exist_ok=True)
        trajectory=folder/'episode.jsonl'
        if trajectory.exists():trajectory.unlink()
        solve(world,folder);rows=[json.loads(s) for s in trajectory.read_text().splitlines()]
        entry={'id':'reference-'+task,'kind':'reference','label':TASKS[task]['name'],'task_id':task,'seed':37,
               'description':'Scripted public-tool feasibility route with cooperative fixture characters, not a learned model result.'}
        (destination/(entry['id']+'.json')).write_text(json.dumps({'events':replay(initial,rows,{'termination_reason':'success','result':world.result},'reference')},ensure_ascii=False)+'\n');catalog.append(entry)
    # Recompute the reference with the current engine and label it explicitly.
    world=build('mercy_inquest',7);initial=world.opening()
    folder=ROOT/'logs/viewer-reference';folder.mkdir(exist_ok=True)
    trajectory=folder/'episode.jsonl'
    if trajectory.exists():trajectory.unlink()
    solve(world,folder)
    rows=[json.loads(s) for s in trajectory.read_text().splitlines()]
    entry={'id':'reference-inquest','kind':'reference','label':'The Mercy House Inquest','task_id':'mercy_inquest','seed':7,
      'description':'Scripted public-tool reference with cooperative fixture characters. This is not a learned or LLM success.'}
    (destination/(entry['id']+'.json')).write_text(json.dumps({'events':replay(initial,rows,{'termination_reason':'success','result':world.result},'reference')},ensure_ascii=False)+'\n');catalog.append(entry)
    archive=ROOT/'Kasukabe Defence Force.zip'
    if archive.exists():
        with zipfile.ZipFile(archive) as bundle:
            names=bundle.namelist()
            originals={r['folder']:r.get('original_run','') for r in json.loads(bundle.read('MANIFEST.json')).get('model_runs',[])}
            summaries=sorted(n for n in names if n.startswith('test-run-logs/') and n.endswith('/summary.json'))
            for i,name in enumerate(summaries,1):
                prefix=name.rsplit('/',1)[0];summary=json.loads(bundle.read(name))
                number=int(prefix.rsplit('model-run-',1)[-1])
                if prefix+'/opening.json' not in names:continue
                initial=json.loads(bundle.read(prefix+'/opening.json'));rows=[json.loads(s) for s in bundle.read(prefix+'/episode.jsonl').decode().splitlines()]
                saved=re.search(r'logs/ui-runs/([a-f0-9]{10})/',originals.get(prefix,''))
                original=originals.get(prefix,'')
                native='native-'+original.split('/')[-2] if summary['task_id'] in ('lantern_room','second_passenger','bell_before_dawn') and original else None
                entry={'id':saved[1] if saved else native or 'recorded-model-'+str(number),'kind':'recorded-model','label':TASKS[summary['task_id']]['name']+' · model run '+str(number),
                       'task_id':summary['task_id'],'seed':summary['seed'],
                       'description':'Actual API detective crime-scene run. Termination: '+summary['termination_reason']+'. '+('The verifier accepted its acquired support.' if summary['result'].get('success') else 'The verifier withheld success.')}
                (destination/(entry['id']+'.json')).write_text(json.dumps({'events':replay(initial,rows,summary)},ensure_ascii=False)+'\n');catalog.append(entry)
    for path in sorted((ROOT/'logs/public').glob('*/*/summary.json')):
        if not (path.parent/'opening.json').exists():continue
        summary=json.loads(path.read_text());task=summary['task_id']
        if task not in ('lantern_room','second_passenger','bell_before_dawn'):continue
        ident='native-'+path.parent.parent.name
        if any(e['id']==ident for e in catalog):continue
        initial=json.loads((path.parent/'opening.json').read_text());rows=[json.loads(s) for s in (path.parent/'episode.jsonl').read_text().splitlines()]
        entry={'id':ident,'kind':'recorded-model','label':TASKS[task]['name']+' · live-character run','task_id':task,'seed':summary['seed'],
               'description':'Actual isolated API detective and character agents. Result: '+summary['termination_reason']+'. The report is scored from acquired evidence.'}
        (destination/(ident+'.json')).write_text(json.dumps({'events':replay(initial,rows,summary)},ensure_ascii=False)+'\n');catalog.append(entry)
    for skill,run in [('statement_review','selector-final-live-671000'),('navigation','selector-final-live-671003-continuation'),('forgery','selector-final-live-671000')]:
        source=ROOT/'logs'/run/skill
        if not (source/'summary.json').exists():continue
        packet=json.loads((source/'opening.json').read_text());summary=json.loads((source/'summary.json').read_text())
        here=packet['scene'].get('place',{}).get('id')
        scene={**packet['scene'],'people':packet.get('people_seen',{}).get(here,[])}
        initial={**packet['opening'],'now':scene,'notes':packet['acquired_records']}
        initial['assignment']=initial.get('exercise',{}).get('instruction','Checkpoint exercise')
        projected=replay(initial,[],None)
        for line in (source/'episode.jsonl').read_text().splitlines():
            row=json.loads(line)
            if not row.get('parsed_actions'):continue
            projected.append(reply_event(row))
            chosen=row['selected_index'];projected.append({'type':'selection','reply':row['step'],
                'selected_tool':row['parsed_actions'][0]['tool'],'probability':row['selection_probabilities'][chosen],
                'candidate_count':len(row['candidates'])})
            for action,result in zip(row['parsed_actions'],row['tool_result']):projected.append(action_event(action,result,row['step']))
        projected.append({'type':'finished','termination':'checkpoint_success' if summary['exercise_reward']==1 else 'checkpoint_failure',
                          'exercise_reward':summary['exercise_reward'],'result':verdict(summary['verifier'])})
        projected=[{**event,'seq':i+1} for i,event in enumerate(projected)]
        entry={'id':'rl-'+skill,'kind':'selector-checkpoint','label':skill.replace('_',' ').title()+' · trained selector',
               'task_id':'checkpoint-'+skill,'seed':summary['seed'],'model':'Frozen CPU selector + API proposer',
               'max_steps':packet['steps_left'],
               'description':'Actual frozen-selector evaluation with live character calls, starting at a skill checkpoint with prior acquired material. Exercise reward and broader Town score are separate.'}
        (destination/(entry['id']+'.json')).write_text(json.dumps({'events':projected},ensure_ascii=False)+'\n');catalog.append(entry)
    for entry in catalog:
        task=entry.get('task_id');entry['difficulty']=TASKS.get(task,{}).get('difficulty','checkpoint')
        entry['family']=TASKS.get(task,{}).get('family','mercy_house')
    # Prefer an actual successful beginner model run when available; recorded
    # references remain explicitly labeled in the library.
    catalog.sort(key=lambda e:(0 if e.get('task_id')=='lantern_room' and e.get('kind')=='recorded-model' and e.get('seed')==211 else 1))
    (destination/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    print(json.dumps({'replays':len(catalog),'source':'current public-tool reference + existing archive public model runs','private_logs_read':False}))


if __name__=='__main__':main()
