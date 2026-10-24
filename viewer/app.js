import {backdrop,portrait} from './art.js';
import {initialState,stateAt,actionTitle,recordKind,recordLabel,recordText} from './state.js';

const $=id=>document.getElementById(id);
const csrf=document.querySelector('meta[name="mercy-csrf"]').content;
let settings={},runs=[],run=null,events=[],position=0,state=initialState(),playing=false,live=false,stream=null,clock=null,filter='all',sceneId='',actorKey='',opened=false;
const icon={go:'↗',ask:'◌',search:'⌕',collect:'◇',compare:'≋',request_access:'⚿',excavate:'⌁',submit_report:'▤',people_here:'♧',look:'◈',record_note:'✎',review_records:'▱',run_command:'›_'};

function node(tag,className,text){const el=document.createElement(tag);if(className)el.className=className;if(text!==undefined)el.textContent=String(text);return el;}
function toast(text){$('toast').textContent=text;$('toast').classList.remove('hidden');setTimeout(()=>$('toast').classList.add('hidden'),6000);}
async function api(path,options={}){const response=await fetch(path,{...options,headers:{'Content-Type':'application/json','X-Mercy-CSRF':csrf,...options.headers}});const value=await response.json();if(!response.ok)throw new Error(value.error||'Request failed');return value;}
function kindLabel(item){return item.kind==='reference'?'SCRIPTED REFERENCE':item.kind==='selector-checkpoint'?'RL CHECKPOINT REPLAY':item.kind==='live-model'&&['starting','building','running','stopping'].includes(item.status)?'LIVE API MODEL':'RECORDED API MODEL';}
function showDetail(title,text,kicker='FROM THE CASEBOOK'){$('detail-title').textContent=title;$('detail-kicker').textContent=kicker;$('detail-body').replaceChildren(node('div','',text));$('detail-dialog').showModal();}
function addActor(id,name,appearance=''){
 const el=node('div','actor');el.innerHTML=portrait(id,appearance);el.append(node('span','actor-name',name));return el;
}
function renderActors(){
 const conversation=state.conversation,ids=conversation?['detective',conversation.pid]:['detective',...state.here.filter(id=>!state.people[id]?.appearance?.includes('Motionless')).slice(0,4)];
 const key=JSON.stringify([sceneId,ids,!!conversation]);if(key===actorKey)return;actorKey=key;
 $('occupants').classList.toggle('interview',!!conversation);
 $('occupants').replaceChildren(...ids.map(id=>addActor(id,id==='detective'?'Inspector Mehra':state.people[id]?.name||id,state.people[id]?.appearance||'')));
}
function renderRecords(){
 const records=Object.values(state.records).filter(r=>!['note'].includes(recordKind(r))).filter(r=>filter==='all'||filter==='material'&&r.object_id||filter==='accounts'&&r.recollections).reverse();
 $('evidence-list').replaceChildren();
 if(!records.length){const empty=node('div','evidence-empty');empty.append(node('span','','▱'),node('h3','','Nothing on the table. Yet.'),node('p','','Acquired material and accounts will appear here.'));$('evidence-list').append(empty);return;}
 for(const record of records){
  const card=node('button','evidence-card');card.type='button';card.setAttribute('aria-label','Read '+recordLabel(record));
  card.append(node('span','record-type',recordKind(record).toUpperCase()),node('span','record-corner',record.record_id),node('h3','',recordLabel(record)),node('p','',recordText(record)),node('small','',state.secured.includes(record.object_id)?'SECURED IN CUSTODY':record.where?'FOUND AT '+record.where.replaceAll('_',' ').toUpperCase():record.recollections?'RECOLLECTIONS RETAIN THEIR SOURCE BASIS':'ACQUIRED OBSERVATION'));
  card.addEventListener('click',()=>{
   $('detail-title').textContent=recordLabel(record);$('detail-kicker').textContent=record.record_id+' · '+recordKind(record).toUpperCase();
   const content=[node('div','',recordText(record))];
   if(record.recollections)for(const m of record.recollections)content.push(node('span','source-line',m.basis.replaceAll('_',' ').toUpperCase()+' — '+m.text));
   if(record.compared)content.push(node('span','source-line','Compared acquired sources: '+record.compared.join(', ')));
   if(record.where)content.push(node('span','source-line','Found at '+record.where.replaceAll('_',' ')+'. Found by '+record.found_by+'.'));
   $('detail-body').replaceChildren(...content);$('detail-dialog').showModal();
  });$('evidence-list').append(card);
 }
}
function renderTimeline(){
 $('timeline-meta').textContent=state.history.length+' ACTIONS OBSERVED';
 $('timeline-events').replaceChildren();
 if(!state.history.length){$('timeline-events').append(node('p','empty-copy','Movement, discoveries and conversations will appear here.'));return;}
 for(const item of state.history.slice(-12).reverse()){
  const row=node('div','timeline-item'),content=node('div');let detail='';const o=item.observation;
  if(o.error)detail=o.error;
  else if(item.action.tool==='go')detail=o.place?.name||'Following a visible route.';
  else if(o.findings)detail=o.findings.length?o.findings.map(recordLabel).join(' · '):'No new material found on this feature.';
  else if(o.words)detail=o.words.slice(0,180)+(o.words.length>180?'…':'');
  else if(o.observation)detail=o.observation.slice(0,180);
  else if(o.people)detail=o.people.map(p=>p.name).join(' · ');
  else if(o.summary)detail=o.summary;
  else if(o.secured)detail='Custody recorded for '+o.secured;
  else if(o.submitted)detail='The final report is being checked against acquired support.';
  else if(o.records)detail='Reviewed '+o.records.length+' acquired records.';
  else if(item.action.tool==='run_command')detail=o.timed_out?'Command timed out; the investigation can continue.':'Isolated command completed. Local files cannot create evidence.';
  else if(o.granted!==undefined)detail=o.granted?'Access was granted.':'Access was declined.';
  else detail='A public observation was recorded.';
  content.append(node('strong','',actionTitle(item.action,state)),node('p','',detail));row.append(node('span','timeline-icon',icon[item.action.tool]||'·'),content,node('small','',item.reply?'REPLY '+item.reply:'EVENT '+item.seq));$('timeline-events').append(row);
 }
}
function render(){
 const place=state.scene.place||{};
 if(place.id&&place.id!==sceneId){sceneId=place.id;$('backdrop').innerHTML=backdrop(sceneId);document.querySelector('.stage').classList.remove('scene-change');void document.querySelector('.stage').offsetWidth;document.querySelector('.stage').classList.add('scene-change');}
 $('location-name').textContent=place.name||'The town is waiting';$('scene-description').textContent=place.description||'';
 $('reply-count').textContent=state.reply?(run?.kind==='reference'?'ACTION '+state.reply:run?.kind==='selector-checkpoint'?'DECISION '+state.reply+' / '+run.max_steps:'REPLY '+state.reply+' / 40'):'PROLOGUE';
 $('activity-text').textContent=state.status;$('activity-detail').textContent=state.pending?.tool==='model_request'?'The model request is in progress. No private reasoning is shown.':state.pending?'Waiting for this action to return. The scene follows actual engine events.':state.finished?'Open the final report to see what was supported.':live?'The agent is running independently.':'The stage reflects the selected replay event.';
 $('decision-note').textContent=state.note||'No decision note recorded yet. The detective’s private reasoning is not shown.';
 $('selector-panel').classList.toggle('hidden',!state.selection);
 if(state.selection){$('selector-choice').textContent=state.selection.tool+' · '+(state.selection.probability*100).toFixed(1)+'% among '+state.selection.count+' candidates';$('selector-probability').value=state.selection.probability;}
 $('hypotheses').replaceChildren(...state.hypotheses.map(h=>{const item=node('div','hypothesis');item.append(node('span','',h.status.replaceAll('_',' ')),node('div','',h.statement),node('small','',h.sources.length?'Sources: '+h.sources.join(', '):'No acquired source cited.'));return item;}));
 $('record-count').textContent=Object.values(state.records).filter(r=>recordKind(r)!=='note').length;$('people-count').textContent=Object.keys(state.people).length;$('place-count').textContent=state.visited.length;
 $('conversation').classList.toggle('hidden',!state.conversation);
 if(state.conversation){const c=state.conversation;$('question-text').textContent=c.question;$('answer-text').textContent=c.answer;$('witness-name').textContent=state.people[c.pid]?.name||c.pid;$('dialogue-basis').textContent=[...new Set(c.recollections.map(m=>m.basis.replaceAll('_',' ')))].join(' · ')||'NO FACTUAL RECOLLECTION RELEASED';}
 renderActors();renderRecords();renderTimeline();
 $('event-count').textContent=position+' / '+events.length;$('seek').max=events.length;$('seek').value=position;
 $('play-button').textContent=playing?'Ⅱ':'▶';$('play-button').setAttribute('aria-label',playing?'Pause the viewer':'Play the viewer');
 $('play-label').textContent=live?(playing?'Following live':'Display paused'):playing?'Playing recorded events':'Recorded replay';
 $('playback-note').textContent=live?'Playback controls affect the viewer only. The agent continues.':run?.kind==='reference'?'Scripted public-tool reference · fixture characters':run?.kind==='selector-checkpoint'?'RL skill checkpoint · prior acquired material · not a whole-case run':'Recorded API detective · actual observations';
 $('stage-caption').textContent=state.finished?(state.finished.termination==='success'?'Report accepted · acquired support verified':'Investigation ended · '+state.finished.termination):state.pending?actionTitle(state.pending,state):state.conversation?'A conversation, with limits on what each person knows.':state.scene.immediately_visible||'Only acquired observations are shown.';
 $('arrival-card').classList.toggle('hidden',opened||live||position>1);$('stop-button').classList.toggle('hidden',!live||!!state.finished);
 $('end-button').textContent=state.finished?'Read final report →':'Go to report →';
}
function seek(value){position=Math.max(1,Math.min(events.length,value));state=stateAt(events,position);opened=true;render();}
function pause(){playing=false;if(clock)clearTimeout(clock);clock=null;render();}
function tick(){
 if(!playing||live)return;
 if(position>=events.length){pause();return;}
 seek(position+1);const current=events[position-1];
 const delay=(current?.action?.tool==='ask'?5500:current?.type==='reply'?350:1400)/Number($('speed-select').value);
 clock=setTimeout(tick,delay);
}
function play(){if(!events.length&&!live)return;opened=true;playing=true;if(live){if(events.length)seek(events.length);render();}else{if(position>=events.length)seek(1);tick();}}
async function loadRun(ident){
 pause();if(stream){stream.close();stream=null;}
 run=await api('/api/runs/'+encodeURIComponent(ident));events=run.events||[];position=Math.min(1,events.length);state=stateAt(events,position);opened=false;sceneId='';actorKey='';
 live=run.kind==='live-model'&&['starting','building','running','stopping'].includes(run.status);
 $('run-kind').textContent=kindLabel(run);$('case-title').textContent=run.label;$('provider-label').textContent=run.model||'Public-tool reconstruction';$('status-dot').classList.toggle('live',live);
 $('arrival-label').textContent=run.kind==='reference'?'A recorded public-tool reference. No model calls.':run.kind==='selector-checkpoint'?'An actual trained-selector checkpoint run. Prior evidence is included.':'A recorded model run. Failures are retained.';
 render();
 if(live){
  playing=true;opened=true;stream=new EventSource('/api/runs/'+encodeURIComponent(ident)+'/events?after='+events.length);
  stream.onmessage=message=>{const event=JSON.parse(message.data);if(event.seq<=events.length)return;events.push(event);if(playing)seek(events.length);else render();if(['finished','run_error','stopped'].includes(event.type)){live=false;playing=false;run.status='finished';stream.close();stream=null;$('status-dot').classList.remove('live');$('run-kind').textContent=kindLabel(run);render();}};
  stream.onerror=()=>{$('activity-detail').textContent='Reconnecting to the local observer feed…';};
  if(events.length)seek(events.length);else render();
 }
}
function showReport(){
 if(!state.finished){const end=events.findIndex(e=>e.type==='finished'||e.type==='run_error'||e.type==='stopped');if(end<0){toast(live?'The investigation is still running.':'No final report was recorded.');return;}pause();seek(end+1);}
 const finished=state.finished,result=finished.result||{};$('detail-title').textContent=run.kind==='selector-checkpoint'?'The checkpoint result':finished.termination==='success'?'A supported reconstruction':'An unfinished reconstruction';$('detail-kicker').textContent='FINAL VERIFIER RESULT · '+finished.termination.toUpperCase();
 const blocks=[];const narrative=state.history.findLast(h=>h.action.tool==='submit_report')?.action.args?.narrative;
 blocks.push(node('div','',run.kind==='reference'?'This is a scripted reference with cooperative fixture characters. It demonstrates a legal proof route; it is not a learned detective result.':run.kind==='selector-checkpoint'?'This is an actual trained-selector skill checkpoint with previously acquired material. Its exercise reward is separate from the broader Town report score; it is not a fresh crime-scene solve.':'This is an actual model run. A plausible narrative is not counted as a supported finding.'));
 if(finished.exercise_reward!==undefined){const row=node('div','verdict-row');row.append(node('span','','Exercise reward'),node('strong','',finished.exercise_reward));blocks.push(row);}
 for(const [label,value] of [[run.kind==='selector-checkpoint'?'Town report score':'Reward',result.score??'Not graded'],['Supported findings',result.supported_findings?.length??0],['False findings',result.false_findings?.length??0],['Unsupported findings',result.unsupported_findings?.length??0]]){const row=node('div','verdict-row');row.append(node('span','',label),node('strong','',value));blocks.push(row);}
 for(const [key,label] of [['supported_findings','SUPPORTED'],['false_findings','FALSE'],['unsupported_findings','UNSUPPORTED']])for(const f of result[key]||[])blocks.push(node('span','source-line',label+' — '+f.actor+' / '+f.predicate+' / '+f.object));
 if(narrative)blocks.push(node('span','source-line','THE DETECTIVE’S SUBMITTED NARRATIVE (UNSCORED)'),node('div','',narrative));
 if(finished.message)blocks.push(node('div','',finished.message));$('detail-body').replaceChildren(...blocks);$('detail-dialog').showModal();
}
async function showLibrary(){
 const data=await api('/api/runs');runs=data.runs;$('library-list').replaceChildren();
 for(const item of runs){const button=node('button','library-entry');button.append(node('span','badge',kindLabel(item)),node('strong','',item.label),node('small','',(item.description||'Recorded investigation')+' · seed '+item.seed));button.addEventListener('click',()=>{$('library-dialog').close();loadRun(item.id).catch(e=>toast(e.message));});$('library-list').append(button);}
 $('library-dialog').showModal();
}
function configure(){
 $('form-error').textContent='';$('configuration-status').textContent=settings.characters_configured?'Town character model is configured server-side.':'Town character credentials are not configured. Add NPC settings to the server .env before a live run.';
 $('configured-key-input').disabled=!settings.key_configured;$('configured-key-input').checked=!!settings.key_configured;$('key-field').classList.toggle('hidden',!!settings.key_configured);
 $('key-input').required=!settings.key_configured;$('settings-dialog').showModal();
}
$('run-form').addEventListener('submit',async event=>{
 event.preventDefault();$('form-error').textContent='';const seed=Number($('seed-input').value);
 if(!Number.isSafeInteger(seed)){$('form-error').textContent='Enter a seed within JavaScript’s exact integer range.';return;}
 const body={task_id:$('task-input').value,seed,model:$('model-input').value,base_url:$('endpoint-input').value,api_key:$('key-input').value,use_configured_key:$('configured-key-input').checked};
 $('start-button').disabled=true;
 try{const value=await api('/api/runs',{method:'POST',body:JSON.stringify(body)});$('key-input').value='';$('settings-dialog').close();await loadRun(value.id);toast('The isolated live investigation is starting.');}
 catch(error){$('form-error').textContent=error.message;}
 finally{$('key-input').value='';body.api_key='';$('start-button').disabled=false;}
});
$('configured-key-input').addEventListener('change',()=>{const enabled=$('configured-key-input').checked;$('key-field').classList.toggle('hidden',enabled);$('key-input').required=!enabled;});
$('stop-button').addEventListener('click',async()=>{try{await api('/api/runs/'+run.id+'/stop',{method:'POST',body:'{}'});toast('Stopping this live run.');}catch(e){toast(e.message);}});
$('library-button').addEventListener('click',()=>showLibrary().catch(e=>toast(e.message)));$('new-button').addEventListener('click',configure);
$('begin-button').addEventListener('click',play);$('play-button').addEventListener('click',()=>playing?pause():play());
$('next-button').addEventListener('click',()=>{pause();seek(position+1);});$('back-button').addEventListener('click',()=>{pause();seek(position-1);});
$('seek').addEventListener('input',event=>{const value=Number(event.target.value);pause();seek(value);});$('end-button').addEventListener('click',showReport);
$('scene-button').addEventListener('click',()=>showDetail(state.scene.place?.name||'The room',state.scene.place?.description||'No room description acquired.','CURRENT PUBLIC SCENE'));
$('biography-button').addEventListener('click',()=>showDetail('Arun’s remembered life',state.opening?.your_life?.recollections||'No remembered life recorded.','HIS OWN HISTORY · NOT EVIDENCE OF GUILT'));
$('scope-button').addEventListener('click',()=>showDetail(state.opening?.task?.name||'The assignment',(state.opening?.task?.scope||state.opening?.assignment||'')+'\n\nFull success: '+(state.opening?.task?.success||'Acquire support for the report.'),'PUBLIC TASK · NO ANSWER CHECKLIST'));
$('about-button').addEventListener('click',()=>showDetail('An observer, not an oracle','The stage reads public observations only. Undisclosed memories, private planner calls, credentials and provider reasoning fields are excluded.\n\nNotes show the detective’s stated views, not a measurement of internal emotions. Playback does not change the world or its reward.\n\n'+(run?.description||'')+'\nRun: '+(run?.id||'—')+'\nKind: '+(run?.kind||'—'),'HOW THIS VIEW WORKS'));
document.querySelectorAll('.close-dialog').forEach(button=>button.addEventListener('click',()=>button.closest('dialog').close()));
document.querySelectorAll('dialog').forEach(dialog=>dialog.addEventListener('click',event=>{if(event.target===dialog){const box=dialog.getBoundingClientRect();if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)dialog.close();}}));
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{filter=button.dataset.filter;document.querySelectorAll('[data-filter]').forEach(b=>b.classList.toggle('active',b===button));renderRecords();}));

async function boot(){
 $('detective-portrait').innerHTML=portrait('detective');$('backdrop').innerHTML=backdrop('archive');
 try{
  settings=await api('/api/config');const data=await api('/api/runs');runs=data.runs;
  $('task-input').replaceChildren(...settings.tasks.map(task=>{const option=node('option','',task.name+' · '+task.difficulty);option.value=task.task_id;return option;}));
  $('model-input').value=settings.defaults.model;$('endpoint-input').value=settings.defaults.base_url;
  if(runs.length)await loadRun(runs[0].id);else{$('arrival-label').textContent='No recorded cases yet. Start a live investigation.';$('begin-button').textContent='Configure a detective →';$('begin-button').addEventListener('click',configure);}
 }catch(error){toast(error.message);$('stage-caption').textContent='The local viewer service is unavailable.';}
}
boot();
