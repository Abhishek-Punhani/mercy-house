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
    live_good = sum(row['exercise_reward']==1 for row in live['rows'])
    live_caption = f'{live_good}/{len(live["rows"])} completed live checkpoint exercises; small unpaired smoke, not whole-case success.'
    viewer_image=ROOT/'docs/viewer-stage.png'
    viewer_slide=('<h1>Watch the actual inquiry</h1><div style="display:flex;align-items:center;gap:28px"><img alt="Actual scripted-reference dialogue in the Mercy House viewer" style="width:65%;max-height:420px;object-fit:contain" src="data:image/png;base64,'+base64.b64encode(viewer_image.read_bytes()).decode()+'"><div style="font-size:.9em"><p>Places change after movement.</p><p>Dialogue and evidence follow public observations.</p><p>Provider setup, live streaming and labeled replays.</p><p>No hidden character memories or invented thoughts.</p></div></div><p class="small">Shown: an actual scripted-reference replay. The UI labels it explicitly. New live runs still use strict scoring.</p>') if viewer_image.exists() else None
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
      '<h2>Measured checks</h2><p>All eight references score 1.0 and no-ops 0.0. '+str(tests['town_tests'])+' town, '+str(tests['legacy_tests'])+' legacy and four Node tests pass. Browser/filter/form checks and real-command isolation probes pass. Fresh no-cache four-image build: '+str(tests['cold_build_seconds'])+' seconds locally; organizer timing remains external.</p>'
      '<h2>RL and negative transfer</h2><p>Optional REINFORCE selector: 20,000 CPU episodes, 460 coefficients, 530.243 seconds, zero training API calls. Frozen historical offline greedy: 147/160; live checkpoint smoke: 2/5. LLM weights stay fixed. New matched three-case calibration: LLM-ranked 1/3, frozen RL-selected 0/3, with the same 2–6 proposal contract and fixed response bank. This is not live-NPC evaluation or evidence of RL superiority. Both hard-family runs failed.</p>'
      '<h2>Known weaknesses</h2><p>Authored small families and proof vocabulary; no whole-case RL benefit demonstrated; no direct score for internal grief/ego; no discovered supernatural mechanism. Other levels are design complexity, not measured success-rate bands. Source originality is authored, not an exhaustive uniqueness guarantee. Final separate NPC setup and upload remain external. No winning or universal jailbreak-resistance claim.</p>'
      '<p class="small">Primary research and PS links: docs/RESEARCH_AND_WIN_PLAN.md. Full trajectories and source manifests accompany this entry.</p>'
    ]
    deck = [
      '<h1>Mercy House</h1><p class="large">Can a detective prove what happened when a plausible story is wrong?</p><blockquote>A snowbound town in 1900. Local memories. Physical traces. No answer checklist.</blockquote><p>Eight tasks · Four case families · Three designed levels.</p><p class="small">Games & World Simulations / Open-compatible. Judges bring the detective; our deliverable is the environment.</p>',
      '<h1>A real progression</h1>'+table(['Case family','Challenge'],[('Lantern Room / beginner','Witnessed fatal assault; learn tools and sourced reporting'),('Second Passenger / intermediate','Two deaths; identify sabotage and intended target'),('Bell Before Dawn / advanced','Forged foreknowledge, delivery chain and an unrelated-looking death'),('Mercy House / five scopes','Loyalty, concealed evidence, fabricated threats and historical crimes')])+'<p>New cases change the assailant with the seed and regenerate actions, traces and recollections. They are original authored scenarios using broad mystery mechanisms.</p>',
      '<h1>Causes execute before arrival</h1><p class="large">Validated actions → local perceptions → persistent evidence → investigation</p><p>Remove the assault: no body. Leave the brake intact: the coach survives. Leave the cordial unadulterated: drinking does not kill.</p><p>Witnesses know what they saw, not an offstage cause of death.</p><p class="small">Canonical tape: recorded LLM decisions. New families: authored seeded tapes. Neither is claimed to be a continuously autonomous town.</p>',
      '<h1>Watch the actual inquiry</h1><p>Local story viewer: changing locations, discovered character mascots, actual dialogue, acquired documents and provider configuration.</p><p>Public events only. No invented thoughts or hidden character memories.</p><p>Replay library filters by level and labels model runs, scripted references and skill checkpoints separately.</p><p class="small">python -m mercy.viewer.server → http://localhost:8787</p>',
      '<h1>Reward proof, not a lucky name</h1><p class="large"><code>'+proof+'</code></p><p>C: supported target coverage. F: distinct false findings. U: distinct unsupported findings.</p><p>Physical mechanisms and testimony must agree. Paper ownership alone cannot establish forgery. An unsupported correct guess earns zero.</p><p class="small">Narrative is retained but unscored. Programmatic authored proof paths; no LLM judge.</p>',
      '<h1>Protect the answer from the solver</h1>'+table(['Role','Authority'],[('Shell workspace','Notes, scripts and validated public town tools'),('Trusted harness','Budget, parsing, public logging and orchestration'),('Protected world','Hidden state, transitions, provenance and reward'),('Model gateway','Credentials and fixed endpoint configuration')])+'<p>Private planner → gated recollections → public speaker. Actor questions cannot directly inspect private memories.</p>',
      '<h1>Measured beginner success</h1><p class="large">4 / 4 live detective runs · reward 1.0</p>'+table(['Seeds','NPC condition / conclusion'],[('211, 307, 401','Native API detective and live isolated character agents'),('37','Additional opposite-assailant calibration')])+'<p>No false or unsupported findings. The actual acquired proof and raw runs are retained.</p><p class="small">Small development sample, one model deployment. Not a reliability estimate. No complete live success established for the other families.</p>',
      '<h1>RL: useful evidence, honest failure</h1>'+table(['Evaluation','Result'],[('20,000 CPU training episodes','530.243 seconds; 460 coefficients; no GPU'),('Historical offline greedy checkpoints','147/160 versus untrained 1/160'),('Historical live checkpoint smoke','2/5; not whole cases'),('New matched family comparison','LLM-ranked 1/3; frozen selector 0/3')])+'<p class="small">Same 2–6 ranked candidate contract, fixed grounded response bank and normal disclosure gates. Three cases only; branch-dependent proposals differ. Frozen policy showed no whole-case advantage and remains optional.</p>',
      '<h1>Evidence under stress</h1>'+table(['Check','Result'],[('Eight task reference/no-op pairs','1.0 / 0.0 for every task'),('Town + legacy + Node tests',str(tests['town_tests'])+' + '+str(tests['legacy_tests'])+' + 4 pass'),('Real-command isolation','Private routes denied; workspace forgery scores zero'),('Causal counterfactuals','No destructive action → no corresponding death'),('No-cache four-image build',str(tests['cold_build_seconds'])+' seconds locally')])+'<p class="small">Failed runs stay in the archive. Scripted references are not presented as learned or LLM results.</p>',
      '<h1>What this entry establishes</h1><p class="large">A reproducible investigation environment with an accessible demo and evidence-grounded difficulty.</p><p>Local tools, isolated character memories, strict scoring, observable failures and measured CPU RL.</p><p>Limits: authored proof vocabulary, small samples, no established whole-case RL gain, incomplete offstage-life and supernatural mechanics.</p><p class="small">Final separate character-model deployment and organizer-machine timing must be verified. User handles the private repository and submission form.</p>'
    ]
    if viewer_slide:deck[3]=viewer_slide
    render('design-doc',design)
    render('deck',deck,True)
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
    if len(run_summaries)<3: raise RuntimeError('At least three actual model runs required')
    shutil.copytree(ROOT/'baseline-results/mercy_inquest/reference',folder/'sample-trajectories/success-reference')
    (folder/'sample-trajectories/success-reference/README.txt').write_text('Scripted public-tool reference with cooperative fixture characters. The script knows the authored solution. This proves a legal proof route; it is NOT an LLM or learned-policy success.\n')
    failure = folder/next(r['folder'] for r in reversed(run_summaries) if r['score'] < 1.)
    success = folder/next(r['folder'] for r in run_summaries if r['score'] == 1. and r['task_id'] == 'lantern_room')
    shutil.copytree(success,folder/'sample-trajectories/success-model')
    (folder/'sample-trajectories/success-model/README.txt').write_text('Actual cold-start native API detective with live character agents. All required findings have acquired support; no scripted solver or disclosed answer checklist. Small development calibration, not a reliability estimate.\n')
    shutil.copytree(failure,folder/'sample-trajectories/failure-model')
    (folder/'sample-trajectories/failure-model/README.txt').write_text('Actual API detective crime-scene run. Failure is retained; no success is inferred from narrative or a correct guess.\n')
    for name in ('design-doc.pdf','deck.pdf','RL_TRAINING_REPORT.md','RL_TRAINING_RESULT.json','RL_LIVE_TRANSFER_RESULT.json','PS_COMPLIANCE_AUDIT.md','SECURITY.md','POLICY_AND_REWARD.md','VALIDATION_RESULT.json','STORY_VIEWER.md','UI_VALIDATION_RESULT.json','viewer-stage.png','FAMILY_VALIDATION_RESULT.json','FAMILY_POLICY_COMPARISON.json','CASE_FAMILIES.md','FAMILY_AUTHOR_REVIEW.md'):
        copy('docs/'+name,folder/name)
    copy('models/action-selector-final.json',folder/'rl/action-selector-final.json')
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
    manifest = {'team':TEAM,'purpose':'Private reference material; judges run the source repository, not this zip.',
                'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'model_runs':run_summaries,'live_limitations':live['limitations'],
                'sample_success_kind':'actual native detective + live characters (success-model); separate scripted feasibility reference (success-reference)',
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
    print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'model_runs':len(run_summaries),'design_pages':2,'deck_pages':10,'credential_scan':'passed'}))


if __name__ == '__main__': main()
