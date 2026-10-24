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

ROOT = Path(__file__).resolve().parents[1]
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
    source.write_text('''<!doctype html><html><head><meta charset="utf-8"><style>
@page {size: '''+page_size+'''; margin: 12mm} * {box-sizing:border-box}
body {font-family:Arial,sans-serif;color:#182b3c;margin:0;font-size:'''+font+''';line-height:1.36}
section {height:'''+height+''';position:relative;break-after:page;padding:5px 10px 25px} section:last-child {break-after:auto}
h1 {font-size:2.1em;line-height:1.1;margin:18px 0 18px;color:#142b3b} h2 {font-size:1.32em;margin:15px 0 7px;color:#1b605f}
p {margin:8px 0 13px} .kicker {color:#65788a;font-size:.7em;letter-spacing:.12em}
.large {font-size:1.4em;color:#1b605f;margin:24px 0}.small {font-size:.78em;color:#4a6071}
table {border-collapse:collapse;width:100%;margin:14px 0;font-size:.86em} th,td {text-align:left;border-bottom:1px solid #ccd9e2;padding:9px}
th {color:#1b605f;background:#edf4f5} blockquote {border-left:4px solid #b47a4c;padding:10px 20px;margin:24px 0;background:#f5f2ed}
code {background:#edf3f5;padding:2px 6px;font-family:monospace} footer {position:absolute;bottom:0;right:12px;font-size:.65em;color:#65788a}
</style></head><body>'''+body+'</body></html>')
    pdf = ROOT/'docs'/(name+'.pdf')
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
    if len(gates)<5 or not all(row['passed'] for row in gates): raise RuntimeError('All task gates required')
    live_good = sum(row['exercise_reward']==1 for row in live['rows'])
    live_caption = f'{live_good}/{len(live["rows"])} completed live checkpoint exercises; small unpaired smoke, not whole-case success.'
    rows = [('Untrained sampling','1 / 160','0.625%'),('Trained sampling','140 / 160','87.5%'),('Trained greedy','147 / 160','91.875%')]
    proof = 'R = clamp(C − 0.20 F − 0.10 U, 0, 1)'
    design = [
      '<h1>Mercy House</h1><p class="large">Can a detective establish the truth when loyalty and plausible evidence point in the wrong direction?</p>'
      '<h2>Task and world</h2><p>A fictional mountain town, 1900. Sixteen profiles, fourteen places. The detective receives its remembered life and the local crime scene, then chooses where to go, whom to question and what to inspect. A recorded LLM incident tape is executed at seeded reset; the injury and planted threat create causal traces. Historical background is authored. Post-reset characters use isolated private memories and live model calls.</p>'
      +table(['Task / level','Objective'],[(r['task_id'],{'last_witness':'Fatal assault / introductory demo','borrowed_signature':'Document fabrication / intermediate','brothers_letter':'Concealment and recovery / advanced','garden_burials':'Recovered remains and relocation / advanced','mercy_inquest':'Seven material acts / advanced'}[r['task_id']]) for r in gates])+
      '<h2>Action and observation</h2><p>Observe, identify people here, travel, search or delegate, secure material, ask with optional evidence, seek access, compare, excavate and report. Actions validate local presence, permissions, custody and types. Hearsay and partial perception retain their basis. A statement cannot create an object or permission. A real isolated shell can use the same public town tools.</p>'
      '<h2>Reward</h2><p><code>'+proof+'</code></p><p>C is supported scoped target coverage; F and U are distinct false and unsupported findings. Full success requires C=1 and no F/U. A correct name alone gets zero. Duplicate findings cannot multiply credit. Programmatic proof requires acquired provenance; no LLM judge. Narrative is retained but unscored.</p>',
      '<h1>Verification, isolation and evidence</h1><h2>Defences</h2><p>The protected world owns truth and reward. The shell has no repository, verifier, private logs, credential or orchestration token, and no external route. A trusted public gateway accepts only validated town actions. A separate model gateway holds keys and fixed endpoint configuration. All roles are unprivileged; shell filesystems, resources and subprocesses are bounded. Private planners receive deterministic question topics; public speakers see only released memories.</p>'
      '<h2>Run contract</h2><p>Selected-task reference/no-op gates precede the detective. Same task/seed gives the same starting hash. MODEL/API_KEY/BASE_URL, TASK_ID, SEED, MODE and exact APPEND_FILE suffix are wired. Forty replies, ten executed calls per reply, six hundred seconds, tool deadlines and forced-end grading. Malformed responses consume a step and receive feedback. Public reply logs include raw input/output, actions, results, errors, hash, usage and reward; private audits remain protected.</p>'
      '<h2>Measured evidence</h2><p>All five references score 1.0 and no-ops 0.0. '+str(tests['town_tests'])+' current town tests and '+str(tests['legacy_tests'])+' historical regression tests pass. The command isolation probe passes. A new no-cache builder produced all four images in '+str(tests['cold_build_seconds'])+' seconds locally.</p>'
      '<p>Optional CPU RL: 20,000 episodes, 530.243 seconds, 460 coefficients, zero model calls. Held-out greedy 147/160 versus untrained 1/160. Training uses fixture NPCs and public candidate rules; LLM weights stay fixed. '+html.escape(live_caption)+'</p>'
      '<h2>Known weaknesses</h2><p>One canonical plot with five task scopes; small checkpoint families; authored proof vocabulary; live refusal and proposal distribution shift; no demonstrated complete-case LLM success. No direct score for internal emotions. Continuous offstage lives and a scored ghost mechanism are unfinished. Docker isolation assumes a trusted host/daemon. Organizer-machine timing and independent NPC deployment remain external checks. We make no universal security or winning claim.</p>'
      '<p class="small">Source requirements: supplied 2une.ai PS. Research: TextWorld (2018), Generative Agents (2023), Werewolf RL (ICML 2024), MACHIAVELLI (ICML 2023). Full primary links and competition-result caveats are in docs/RESEARCH_AND_WIN_PLAN.md.</p>'
    ]
    deck = [
      '<h1>Mercy House</h1><p class="large">An evidence-grounded investigation world for language agents.</p><blockquote>The lamps have been turned up too high. Beneath the archive window, a woman lies motionless beside the desk.</blockquote><p>1900. A mountain town. A detective with a personal history here.</p><p class="small">10-minute presentation · Games & World Simulations / Open-compatible · Judges bring the detective.</p>',
      '<h1>The challenge</h1><p class="large">A plausible accusation is not a solved case.</p>'+table(['Pressure','Required behavior'],[('A threatening letter bears a name','Test authorship and provenance'),('A familiar subordinate handles a search','Preserve custody and examine omissions'),('A witness gives a frightened account','Separate observation, hearsay and inference'),('A personal connection suggests a story','Acquire support and revise conclusions')]),
      '<h1>An incident that executes</h1><p>Characters choose legal actions from their own situation. The engine commits movement, obstruction, assault and fabrication, then creates local perceptions and physical traces.</p><p class="large">Recorded action tape → deterministic seeded reset → live investigation</p><p>We freeze the starting incident for reproducibility. We do not pretend a new LLM-generated crime is deterministic.</p><p class="small">Current tape: four participants, three rounds. Other residents have authored routines; continuous autonomous lives are future work.</p>',
      '<h1>The detective controls the inquiry</h1>'+table(['Choose','Receive'],[('Where to go','Local scene, routes and searchable features'),('Whom to question','Released recollections with source basis'),('Search yourself or delegate','Actual discoveries, omissions and custody'),('Which material to compare','Concrete correspondences, not a verdict'),('When to report','Supported coverage and false/unsupported penalties')])+'<p>No required-claim list, omniscient evidence catalog or instruction to suspect a named person.</p>',
      '<h1>Reward proof, not confident prose</h1><p class="large"><code>'+proof+'</code></p><p>C: supported target coverage. F: distinct false findings. U: distinct unsupported findings.</p><p>A cloth match cannot identify a killer. Paper ownership cannot establish forgery. A correct accusation without acquired support scores zero.</p><p>Comparisons can compose into proof. Narrative uncertainty is retained separately; narrative itself is not automatically fact-checked.</p>',
      '<h1>Protect the answer from the solver</h1>'+table(['Role','Authority'],[('Shell workspace','Notes, scripts, validated public town tools'),('Trusted harness','Budget, parsing, logging and orchestration'),('Protected world','Hidden state, provenance, transitions, reward'),('Model gateway','Credentials and configured model endpoints')])+'<p>Private character planner → gated recollections → public speaker. Raw hostile questions do not enter the private planner.</p>',
      '<h1>Actual local RL</h1><p>Five skills: document comparison, witness choice, statement checking, following contacts, supervised delegation.</p>'+table(['Policy','Successes','Rate'],rows)+'<p>20,000 CPU episodes · 8.8 minutes · 460 coefficients · no GPU · no training API calls.</p><p class="small">Eighty held-out checkpoints, repeated twice. Same authored families. Public proposer supplies arguments; this is not learned language comprehension or LLM fine-tuning.</p>',
      '<h1>Live transfer is a separate result</h1><p class="large">'+html.escape(live_caption)+'</p>'+table(['Exercise','Reward / 1'],[(r['skill'],r['exercise_reward']) for r in live['rows']])+'<p class="small">Frozen weights, real character/proposer calls. An interrupted partial attempt is retained and disclosed. Complete crime-scene detective runs so far have failed; checkpoint success is not a solved full case.</p>',
      '<h1>Evidence under stress</h1>'+table(['Check','Result'],[('Five task reference/no-op pairs','1.0 / 0.0 for every task'),('Town + legacy tests',str(tests['town_tests'])+' + '+str(tests['legacy_tests'])+' pass'),('Real-command isolation probe','Private routes denied; forged proof earns zero'),('Timeout recovery','Timed command followed by a valid action'),('Fresh no-cache local build',str(tests['cold_build_seconds'])+' seconds')])+'<p class="small">Sample success is explicitly scripted reference behavior. Failed model runs and raw logs are provided, not replaced with a staged score.</p>',
      '<h1>What this entry establishes</h1><p class="large">A reproducible world where supported reconstruction matters more than naming a culprit.</p><p>Runnable tools, private memories, grounded reward, observable failures and local RL learning.</p><p>Next: new causal plots and role assignments, repeated live transfer evaluations, controlled relationship interventions, and supernatural mechanics only when their causes are discoverable.</p><p class="small">Limits: one canonical case, fixture training, limited report semantics, no whole-case live success yet. Final NPC deployment and organizer-machine timing must be configured and verified.</p>'
    ]
    render('design-doc',design)
    render('deck',deck,True)
    folder = ROOT/'submission'/TEAM
    if folder.exists(): shutil.rmtree(folder)
    folder.mkdir(parents=True)
    shutil.copytree(ROOT/'baseline-results',folder/'baseline-results')
    run_summaries = []
    for index, summary_path in enumerate(sorted((ROOT/'logs/public').glob('*/*/summary.json')),1):
        run_folder = summary_path.parent
        if not (run_folder/'episode.jsonl').exists(): continue
        target = folder/'test-run-logs'/('model-run-'+str(index))
        for name in ('opening.json','run.json','episode.jsonl','summary.json'):
            if (run_folder/name).exists(): copy(run_folder/name,target/name)
        summary = json.loads(summary_path.read_text())
        run_summaries.append({'folder':str(target.relative_to(folder)),'original_run':str(run_folder.relative_to(ROOT)),
            'task_id':summary['task_id'],'termination':summary['termination_reason'],'score':summary['result']['score']})
    if len(run_summaries)<3: raise RuntimeError('At least three actual model runs required')
    shutil.copytree(ROOT/'baseline-results/mercy_inquest/reference',folder/'sample-trajectories/success-reference')
    (folder/'sample-trajectories/success-reference/README.txt').write_text('Scripted public-tool reference with cooperative fixture characters. The script knows the authored solution. This proves a legal proof route; it is NOT an LLM or learned-policy success.\n')
    failure = ROOT/run_summaries[-1]['original_run']
    shutil.copytree(failure,folder/'sample-trajectories/failure-model')
    (folder/'sample-trajectories/failure-model/README.txt').write_text('Actual API detective crime-scene run. Failure is retained; no success is inferred from narrative or a correct guess.\n')
    for name in ('design-doc.pdf','deck.pdf','RL_TRAINING_REPORT.md','RL_TRAINING_RESULT.json','RL_LIVE_TRANSFER_RESULT.json','PS_COMPLIANCE_AUDIT.md','SECURITY.md','POLICY_AND_REWARD.md','VALIDATION_RESULT.json'):
        copy('docs/'+name,folder/name)
    copy('models/action-selector-final.json',folder/'rl/action-selector-final.json')
    for name in ('experiment.json','learning.jsonl','evaluation.json','exercise-gates.json'):
        copy('logs/selector-final-curriculum-145/'+name,folder/'rl'/name)
    frozen = Path(result['frozen_source'])
    copy(frozen/'source-manifest.json',folder/'rl/frozen-source-manifest.json')
    for name in ('final-town-tests.txt','final-legacy-tests.txt','cold-build.json'):
        copy('logs/'+name,folder/'validation'/name)
    copy('logs/public/command-isolation-probe.json',folder/'validation/command-isolation-probe.json')
    for run in live['runs']:
        origin = ROOT/run
        for path in origin.rglob('*'):
            if path.is_file() and 'private' not in path.name:
                copy(path,folder/'rl/live'/origin.name/path.relative_to(origin))
    manifest = {'team':TEAM,'purpose':'Private reference material; judges run the source repository, not this zip.',
                'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'model_runs':run_summaries,'live_limitations':live['limitations'],
                'sample_success_kind':'scripted reference with cooperative fixture NPCs; not an LLM result',
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
