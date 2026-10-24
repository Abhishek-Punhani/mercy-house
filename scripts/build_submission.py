"""Build private reference material, with no network/model calls or credentials.

Requires local Chrome and pdfinfo for PDF rendering/validation. They are authoring
tools only; the runtime environment uses neither dependency.
"""
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
import base64
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TEAM = 'Kasukabe Defence Force'


def read(path):
    return json.loads((ROOT / path).read_text())


def table(headers, rows):
    return '<table><thead><tr>'+''.join('<th>'+html.escape(str(x))+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'


def render(name, pages, landscape=False):
    page_size = '13.333in 7.5in' if landscape else 'A4'
    font = '22px' if landscape else '12px'
    height = '6.45in' if landscape else '263mm'
    body = ''.join('<section><div class="kicker">'+html.escape(TEAM)+' / MERCY HOUSE</div>'+page+'<footer>'+str(i+1)+' / '+str(len(pages))+'</footer></section>' for i,page in enumerate(pages))
    source = ROOT/'docs'/(name+'.html')
    document = '''<!doctype html><html><head><meta charset="utf-8"><style>
@page {size: '''+page_size+'''; margin: 12mm} * {box-sizing:border-box}
body {font-family:Arial,sans-serif;color:#182b3c;margin:0;font-size:'''+font+''';line-height:1.36}
section {height:'''+height+''';position:relative;break-after:page;padding:5px 10px 25px} section:last-child {break-after:auto}
h1 {font-size:2.1em;line-height:1.1;margin:18px 0 18px;color:#142b3b} h2 {font-size:1.32em;margin:15px 0 7px;color:#1b605f}
p {margin:8px 0 13px} .kicker {color:#65788a;font-size:.7em;letter-spacing:.12em}
.large {font-size:1.4em;color:#1b605f;margin:24px 0}.small {font-size:.78em;color:#4a6071}
table {border-collapse:collapse;width:100%;margin:14px 0;font-size:.86em} th,td {text-align:left;border-bottom:1px solid #ccd9e2;padding:9px}
th {color:#1b605f;background:#edf4f5} blockquote {border-left:4px solid #b47a4c;padding:10px 20px;margin:24px 0;background:#f5f2ed}
code {background:#edf3f5;padding:2px 6px;font-family:monospace} footer {position:absolute;bottom:0;right:12px;font-size:.65em;color:#65788a}
</style></head><body>'''+body+'</body></html>'
    changed = not source.exists() or source.read_text() != document
    if changed: source.write_text(document)
    pdf = ROOT/'docs'/(name+'.pdf')
    if changed or not pdf.exists():
        with (ROOT/'logs'/(name+'-chrome.log')).open('w') as output:
            subprocess.run(['google-chrome','--headless','--no-sandbox','--disable-gpu','--no-pdf-header-footer','--print-to-pdf='+str(pdf),source.as_uri()],stdout=output,stderr=subprocess.STDOUT,check=True,timeout=60)
    info = subprocess.check_output(['pdfinfo',str(pdf)],text=True)
    count = int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))
    if count != len(pages):
        raise RuntimeError(f'{name} rendered {count} pages; expected {len(pages)}')
    return pdf


def copy(source, destination):
    source = ROOT/source if not isinstance(source, Path) else source
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination)


def main():
    result = read('docs/RL_TRAINING_RESULT.json')
    live = read('docs/RL_LIVE_TRANSFER_RESULT.json')
    tests = read('docs/VALIDATION_RESULT.json')
    gates = read('baseline-results/gate.json')
    from mercy.town.tasks import TASKS
    if {r['task_id'] for r in gates} != set(TASKS) or not all(row['passed'] for row in gates): raise RuntimeError('All task gates required')
    family = read('docs/FAMILY_VALIDATION_RESULT.json')
    comparison = read('docs/FAMILY_POLICY_COMPARISON.json')
    source_result=read('docs/SOURCE_TRAINING_RESULT.json')
    elite=read('docs/ELITE_TRANSFER_RESULT.json')
    elite_success=elite['successes']
    elite_caption=f"New two-scope elite calibration: LLM-ranked {elite_success['llm_ranked']}/2; source-trained selector {elite_success['rl_selected']}/2. Same API proposal contract and grounded fixed character response bank; not the native live-character harness."
    live_good = sum(row['exercise_reward']==1 for row in live['rows'])
    live_caption = f'{live_good}/{len(live["rows"])} completed live checkpoint exercises; small unpaired smoke, not whole-case success.'
    proof = 'R = clamp(C − 0.20 F − 0.10 U, 0, 1)'
    design = [
      '<h1>Mercy House</h1><p class="large">Evidence-grounded investigations, from an accessible assault to an entangled town inquest.</p>'
      '<h2>World and tasks</h2><p>Eight tasks, four causal case families, three designed levels. The detective receives its own remembered life and the local scene; it chooses where to go, whom to question and what to inspect. Character agents have isolated lives and memories. Required answers and private plans are never supplied.</p>'
      +table(['Family / level','Investigation'],[('Lantern Room / introductory','Witnessed lamp assault; seeded assailant; four locals, three places.'),('Second Passenger / intermediate','Coach sabotage; two deaths; intended target differs from casualty count.'),('Bell Before Dawn / advanced','Apparently prophetic warning; forged paper, delivery chain and death.'),('Mercy House / intermediate–advanced','Five scopes over one canonical incident; sixteen profiles, fourteen places.')])+
      '<p>Canonical reset executes a recorded LLM action tape. New families execute authored seeded action tapes. Preconditions, movement and local perception create persistent traces. Removing sabotage or adulteration prevents the corresponding deaths. Historical background is authored; continuous offstage lives are unfinished.</p>'
      '<h2>Actions and reward</h2><p>Observe, identify people, travel, search or delegate, secure, ask, seek access, compare, excavate and report. Presence, permissions, custody and types are validated. Characters cannot create evidence through dialogue. A casebook preserves acquired sources and unscored notes.</p><p><code>'+proof+'</code></p><p>C: supported scoped target coverage; F/U: distinct false/unsupported findings. Full success requires C=1 and no F/U. A correct name alone earns zero. Authored, programmatic proof routes require acquired provenance; no LLM judge. Narrative is retained but unscored.</p>'
      '<h2>Actual calibration</h2><p>Four cold-start native-tool detective runs with live character models solved Lantern Room with score 1.0 and no false/unsupported findings, including both culprit assignments. This is a small development set, not a reliability estimate. Other families have scripted feasibility proofs; complete live solving is not established.</p>',
      '<h1>Isolation, evaluation and limits</h1><h2>Protect truth from the solver</h2><p>Four unprivileged containers separate world, credentials, trusted harness and real shell. The shell has no verifier, private files, orchestration token, keys or external route. Its gateway accepts only validated public tools. Private character planners receive derived question topics; public speakers see only released memories. Live UI events omit private memories and provider reasoning. Docker security assumes a trusted host/daemon.</p>'
      '<h2>Run contract</h2><p>Exact Compose command; MODEL/API_KEY/BASE_URL, TASK_ID/SEED/MODE; exact UTF-8 APPEND_FILE suffix. Selected-task reference/no-op gates run before detective calls. Forty replies, ten calls per reply, 600 seconds; tool and grading deadlines. Malformed replies consume steps. Logs retain requests, raw outputs, actions, errors, state hashes, reward, latency and usage. Optional localhost story viewer remains independent.</p>'
      '<h2>Measured checks</h2><p>All 184 task/seed gate pairs passed (eight tasks, 23 seeds); references 1 and no-ops 0. Six public-only scripted investigations also solved the three new families with both culprit assignments. '+str(tests['town_tests'])+' town, '+str(tests['legacy_tests'])+' legacy and '+str(tests['node_state_tests'])+' Node tests pass. Browser/filter/form checks and real-command isolation probes pass. Fresh no-cache four-image build: '+str(tests['cold_build_seconds'])+' seconds locally; organizer timing remains external.</p>'
      '<h2>Policy training and transfer</h2><p>Earlier five-skill prototype: 20,000 CPU episodes; unchanged weights rechecked 147/160 with corrected sources. Historical training remains separately labeled. New fresh-zero selector: 6,000 episodes, 132 coefficients, 48.251 seconds, zero training API calls. Three original mechanism-inspired checkpoints, 48 training and 48 held-out states; greedy 96/96 versus untrained 3/96. Prepared acquisitions and rule-based candidate parsing are disclosed; no LLM fine-tuning or full-TV-episode training. '+html.escape(elite_caption)+'</p>'
      '<h2>Known weaknesses</h2><p>Authored small families and proof vocabulary; small transfer sample; no direct score for internal grief/ego; no discovered supernatural mechanism. Live refusal can block the sole independent named witness in the canonical incident. Other levels are design complexity, not measured success-rate bands. Source originality is authored, not an exhaustive uniqueness guarantee. Final separate NPC setup and upload remain external. No winning or universal jailbreak-resistance claim.</p>'
      '<p class="small">Primary research and PS links: docs/RESEARCH_AND_WIN_PLAN.md. Full trajectories and source manifests accompany this entry.</p>'
    ]
    render('design-doc',design)
    subprocess.run([sys.executable,str(ROOT/'scripts/build_presentation.py')],check=True,cwd=ROOT)
    archive=ROOT/(TEAM+'.zip')
    retained=[]
    if archive.exists():
        with zipfile.ZipFile(archive) as previous:
            old=json.loads(previous.read('MANIFEST.json'))
            for item in old.get('model_runs',[]):
                prefix=item['folder']+'/'
                files={name[len(prefix):]:previous.read(name) for name in previous.namelist() if name.startswith(prefix)}
                retained.append((item,files))
    folder = ROOT/'submission'/TEAM
    if folder.exists(): shutil.rmtree(folder)
    folder.mkdir(parents=True)
    shutil.copytree(ROOT/'baseline-results',folder/'baseline-results')
    run_summaries = []
    for item,files in retained:
        target=folder/'test-run-logs'/('model-run-'+str(len(run_summaries)+1))
        for name,data in files.items():
            path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        run_summaries.append({**item,'folder':str(target.relative_to(folder))})
    paths=sorted((ROOT/'logs/public').glob('*/*/summary.json'))+sorted((ROOT/'logs/ui-runs').glob('*/public/*/*/summary.json'))
    for summary_path in paths:
        run_folder = summary_path.parent
        if not (run_folder/'episode.jsonl').exists(): continue
        if any(r['original_run']==str(run_folder.relative_to(ROOT)) for r in run_summaries):continue
        target = folder/'test-run-logs'/('model-run-'+str(len(run_summaries)+1))
        for name in ('opening.json','run.json','episode.jsonl','summary.json','actions.jsonl'):
            if (run_folder/name).exists(): copy(run_folder/name,target/name)
        summary = json.loads(summary_path.read_text())
        run_summaries.append({'folder':str(target.relative_to(folder)),'original_run':str(run_folder.relative_to(ROOT)),
            'task_id':summary['task_id'],'termination':summary['termination_reason'],'score':summary['result']['score']})
    for item in run_summaries:
        origin=ROOT/item['original_run']
        if 'ui-runs' in origin.parts:
            ui_root=origin.parents[2]
            for name in ('source-manifest.json','meta.json'):
                if (ui_root/name).exists():copy(ui_root/name,folder/item['folder']/name)
    if len(run_summaries)<3: raise RuntimeError('At least three actual model runs required')
    shutil.copytree(ROOT/'baseline-results/mercy_inquest/reference',folder/'sample-trajectories/success-reference')
    (folder/'sample-trajectories/success-reference/README.txt').write_text('Scripted public-tool reference with cooperative fixture characters. The script knows the authored solution. This proves a legal proof route; it is NOT an LLM or learned-policy success.\n')
    failure = folder/next(r['folder'] for r in reversed(run_summaries) if r['score'] < 1.)
    success = folder/next(r['folder'] for r in run_summaries if r['score'] == 1. and r['task_id'] == 'lantern_room')
    shutil.copytree(success,folder/'sample-trajectories/success-model')
    (folder/'sample-trajectories/success-model/README.txt').write_text('Actual cold-start native API detective with live character agents. All required findings have acquired support; no scripted solver or disclosed answer checklist. Small development calibration, not a reliability estimate.\n')
    shutil.copytree(failure,folder/'sample-trajectories/failure-model')
    (folder/'sample-trajectories/failure-model/README.txt').write_text('Actual API detective crime-scene run. Failure is retained; no success is inferred from narrative or a correct guess.\n')
    for name in ('design-doc.pdf','deck.pdf','RL_TRAINING_REPORT.md','RL_TRAINING_RESULT.json','RL_LIVE_TRANSFER_RESULT.json','PS_COMPLIANCE_AUDIT.md','SECURITY.md','POLICY_AND_REWARD.md','VALIDATION_RESULT.json','STORY_VIEWER.md','UI_VALIDATION_RESULT.json','viewer-stage.png','FAMILY_VALIDATION_RESULT.json','FAMILY_POLICY_COMPARISON.json','CASE_FAMILIES.md','FAMILY_AUTHOR_REVIEW.md','deck.pptx','PRESENTATION_MANIFEST.json','SOURCE_TRAINING_REPORT.md','SOURCE_TRAINING_RESULT.json','ELITE_TRANSFER_RESULT.json','ELITE_TRANSFER_REPORT.md','ELITE_EVALUATION_PLAN.json','CASE_SOLVABILITY_AUDIT.md','CASE_SOLVABILITY_AUDIT.json','VERIFIER_AND_REVIEWER.md','UI_REPORT_IMPROVEMENTS.md','ui-report.png','ui-interview.png','AUTHOR_REVIEW_SMOKE.json','LEGACY_POLICY_CURRENT_RECHECK.json','SAVED_UI_RUN_RESULTS.json','DEPLOYMENT.md','DEPLOYMENT_RESULT.json','PRESENTATION_VALIDATION.json','qr-repository.png','qr-live-demo.png','PUBLIC_SITE_BROWSER_CHECKS.json','BRIEFING_VOICE_AND_INTERVIEWS.md','BRIEFING_VOICE_VALIDATION.json','INTERVIEW_DEPTH_LIVE_RESULT.json','FINAL_VIEWER_HANDOFF.md','FINAL_VIEWER_VALIDATION.json','PROVIDER_TRANSPORT_SMOKE.json','FINAL_NATIVE_SMOKE.json','SUBMISSION_VIDEO.json','submission-walkthrough.mp4','FINAL_HOSTED_BROWSER.json','ui-providers.png','ui-guided-tour.png'):
        copy('docs/'+name,folder/name)
    copy('models/action-selector-final.json',folder/'rl/action-selector-final.json')
    copy('logs/legacy-policy-current-recheck.json',folder/'rl/legacy-current-recheck.json')
    for name in ('experiment.json','learning.jsonl','evaluation.json','exercise-gates.json'):
        copy('logs/selector-final-curriculum-145/'+name,folder/'rl'/name)
    frozen = Path(result['frozen_source'])
    copy(frozen/'source-manifest.json',folder/'rl/frozen-source-manifest.json')
    for name in ('final-town-tests.txt','final-legacy-tests.txt','cold-build.json','fresh-clone-compose.json'):
        copy('logs/'+name,folder/'validation'/name)
    copy('logs/public/command-isolation-probe.json',folder/'validation/command-isolation-probe.json')
    for name in ('ui-town-tests.txt','ui-legacy-tests.txt','viewer-state-tests.txt','viewer-browser-checks.json','viewer-form-checks.json','viewer-cold-build.json'):
        copy('logs/'+name,folder/'validation'/name)
    for run in live['runs']:
        origin = ROOT/run
        for path in origin.rglob('*'):
            if path.is_file() and 'private' not in path.name:
                copy(path,folder/'rl/live'/origin.name/path.relative_to(origin))
    calibration = ROOT/'logs/family-policy-calibration'
    for path in calibration.rglob('*'):
        if path.is_file() and path.name != 'private-response-bank.json':
            copy(path,folder/'rl/family-calibration'/path.relative_to(calibration))
    source_training=read('docs/SOURCE_TRAINING_RESULT.json')
    source_run=ROOT/source_training['run']
    copy('models/action-selector-sources.json',folder/'rl/source-training/action-selector-sources.json')
    for name in ('experiment.json','learning.jsonl','evaluation.json','exercise-gates.json'):
        copy(source_run/name,folder/'rl/source-training'/name)
    source_frozen=Path(source_training['experiment']['frozen_source'])
    copy(source_frozen/'source-manifest.json',folder/'rl/source-training/frozen-source-manifest.json')
    for path in (source_frozen/'mercy').rglob('*'):
        if path.is_file() and path.suffix in ('.py','.json'):
            copy(path,folder/'rl/source-training/frozen-source/mercy'/path.relative_to(source_frozen/'mercy'))
    elite_frozen=Path(elite['experiment']['frozen_source'])
    copy(elite_frozen/'source-manifest.json',folder/'rl/elite-transfer/frozen-source-manifest.json')
    for path in (elite_frozen/'mercy').rglob('*'):
        if path.is_file() and path.suffix in ('.py','.json'):
            copy(path,folder/'rl/elite-transfer/frozen-source/mercy'/path.relative_to(elite_frozen/'mercy'))
    for path in (ROOT/'logs/source-elite-617-619').rglob('*'):
        if path.is_file() and path.name!='private-response-bank.json':
            copy(path,folder/'rl/elite-transfer'/path.relative_to(ROOT/'logs/source-elite-617-619'))
    (folder/'rl/README.txt').write_text('Historical action-selector-final checkpoint and147/160 metrics predate the payer/carrier proof audit; they are not validation of current delegation semantics. The separate fresh source-training checkpoint begins from zero; its checkpoint and elite conditions are independently documented. No LLM assigns the official score.\n')
    manifest = {'team':TEAM,'purpose':'Private reference material; judges run the source repository, not this zip.',
                'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'model_runs':run_summaries,'live_limitations':live['limitations'],
                'sample_success_kind':'actual native detective + live characters (success-model); separate scripted feasibility reference (success-reference)',
                'source_training':{'checkpoint_sha256':source_training['checkpoint_sha256'],'elite_result':'ELITE_TRANSFER_RESULT.json','scope':'original mechanism-inspired skill checkpoints, not exact TV episode reproduction'},
                'family_calibration':{'native_successes':family['native_successes'],'controlled_successes':comparison['successes']},
                'files_sha256':{str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.rglob('*')) if p.is_file()}}
    (folder/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    secrets=[]
    if (ROOT/'.env').exists():
        for line in (ROOT/'.env').read_text().splitlines():
            if '=' in line:
                key,value=line.split('=',1)
                if key.strip() in ('API_KEY','NPC_API_KEY') and value.strip().strip('"'): secrets.append(value.strip().strip('"').encode())
    for path in folder.rglob('*'):
        if path.is_file() and (path.name=='.env' or any(s in path.read_bytes() for s in secrets)):
            raise RuntimeError('Credential detected in package: '+str(path.relative_to(folder)))
    archive = ROOT/(TEAM+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(folder.rglob('*')):
            if path.is_file(): bundle.write(path,path.relative_to(folder))
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None: raise RuntimeError('Archive integrity check failed')
    print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'model_runs':len(run_summaries),'design_pages':2,'deck_pages':read('docs/PRESENTATION_MANIFEST.json')['slides'],'credential_scan':'passed'}))


if __name__ == '__main__': main()
