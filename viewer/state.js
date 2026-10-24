export function initialState(){return {opening:null,scene:{},people:{},here:[],records:{},secured:[],visited:[],history:[],reply:0,note:'',hypotheses:[],conversation:null,pending:null,finished:null,submission:null,selection:null,status:'At the crime scene'};}
export function actionTitle(action={},state={people:{}}){
 const a=action.args||{}, person=state.people?.[a.pid]?.name||a.pid||'a witness';
 return ({model_request:'Choosing the next action',look:'Observing the room',people_here:'Identifying people present',go:`Travelling to ${(a.destination||'the next place').replaceAll('_',' ')}`,search:`Searching the ${a.surface||'room'}`,collect:'Securing recovered material',ask:`Speaking with ${person}`,compare:'Comparing acquired records',excavate:'Excavating disturbed ground',request_access:`Requesting access from ${person}`,review_records:'Reviewing the acquired casebook',record_note:'Recording a decision note',submit_report:'Submitting the investigation report',run_command:'Using the isolated workspace'})[action.tool]||'Investigating';
}
function acquire(state,value){
 if(!value||typeof value!=='object')return;
 if(Array.isArray(value)){value.forEach(v=>acquire(state,v));return;}
 if(typeof value.record_id==='string')state.records[value.record_id]={...state.records[value.record_id],...value};
 for(const key of ['findings','handed_over','records','search_log','custody_record'])if(value[key])acquire(state,value[key]);
}
export function reduceEvent(previous,event){
 const state=structuredClone(previous);
 if(event.type==='opening'){
  state.opening=event.opening;state.scene=event.opening.now||{};
  if(state.scene.people){state.here=state.scene.people.map(p=>p.id);for(const p of state.scene.people)state.people[p.id]=p;}
  const place=state.scene.place?.id;if(place&&!state.visited.includes(place))state.visited.push(place);
  acquire(state,event.opening.notes||[]);return state;
 }
 if(event.type==='status'){state.status=event.message;return state;}
 if(event.type==='selection'){state.selection={tool:event.selected_tool,probability:event.probability,count:event.candidate_count};return state;}
 if(event.type==='activity'){state.pending=event.action;state.status=actionTitle(event.action,state);state.reply=event.reply||state.reply;return state;}
 if(event.type==='reply'){state.reply=event.reply||state.reply;if(event.note)state.note=event.note;return state;}
 if(event.type==='action'){
  const action=event.action||{},o=event.observation||{};state.reply=event.reply||state.reply;state.pending=null;state.status=actionTitle(action,state);
  if(o.place){if(o.place.id!==state.scene.place?.id){state.here=[];state.conversation=null;}state.scene=o;if(!state.visited.includes(o.place.id))state.visited.push(o.place.id);}
  if(o.people){state.here=o.people.map(p=>p.id);for(const p of o.people)state.people[p.id]=p;}
  acquire(state,o);
  if(o.secured&&!state.secured.includes(o.secured))state.secured.push(o.secured);
  if(action.tool==='ask'&&!o.error)state.conversation={pid:action.args.pid,question:action.args.question,answer:o.words||'No spoken answer recorded.',recollections:o.recollections||[]};
  else if(!['record_note','review_records'].includes(action.tool))state.conversation=null;
  if(action.tool==='record_note'&&!o.error){state.note=o.summary||'';state.hypotheses=o.hypotheses||[];}
  if(action.tool==='submit_report'&&o.submitted===true&&!o.error)state.submission={findings:structuredClone(action.args?.findings||[]),narrative:action.args?.narrative||'',reply:event.reply,seq:event.seq};
  state.history.push({action,observation:o,reply:event.reply,seq:event.seq,minutes:event.minutes});
  return state;
 }
 if(event.type==='finished'){state.finished=event;state.pending=null;state.status=event.termination==='success'?'Supported report accepted':'Investigation ended';return state;}
 if(event.type==='run_error'||event.type==='stopped'){state.finished={termination:event.type,message:event.message,result:{}};state.pending=null;state.status=event.message;}
 return state;
}
export function stateAt(events,count){return events.slice(0,count).reduce(reduceEvent,initialState());}
export function recordKind(r){return r.object_id?'material':r.recollections?'account':r.compared?'comparison':r.hypotheses?'note':'record';}
export function recordLabel(r){return r.label||(r.recollections?'Account · '+(r.person||'witness'):r.compared?'Material comparison':r.hypotheses?'Decision note':r.observation?'Custody observation':'Search record');}
export function recordText(r){return r.description||r.words||r.observation||r.summary||'An acquired record of the inquiry.';}

export function reportOutcome(state,kind){
 const end=state.finished;if(!end)return {label:'Report submitted',tone:'pending',detail:'Awaiting the programmatic verifier. Submission alone does not establish success.'};
 if(kind==='selector-checkpoint'&&end.exercise_reward!==undefined)return {label:end.exercise_reward===1?'Checkpoint completed':'Checkpoint incomplete',tone:end.exercise_reward===1?'success':'failure',detail:'Exercise reward is separate from the Town report score. This run starts with prior acquired material.'};
 if(typeof end.result?.success==='boolean')return {label:end.result.success?'Case solved':'Case not solved',tone:end.result.success?'success':'failure',detail:end.result.success?'Every scoped material finding has acquired support, with no false or unsupported findings.':'The scoped success conditions were not all met. Review supported, false and unsupported findings below.'};
 return {label:'Investigation not graded',tone:'pending',detail:end.message||'No final programmatic grade is available for this run.'};
}

export function findingDescription(finding){
 const verb={assisted:'knowingly facilitated the fatal incident involving',aided:'gave aid to'}[finding.predicate]||finding.predicate;
 return String(finding.actor)+' · '+String(verb)+' · '+String(finding.object);
}

export function interviewGroups(state){
 const groups=new Map();
 for(const event of state.history){
  if(event.action.tool!=='ask'||event.observation.error)continue;
  const pid=event.action.args.pid;
  if(!groups.has(pid))groups.set(pid,{pid,name:state.people[pid]?.name||pid,exchanges:[]});
  groups.get(pid).exchanges.push({question:event.action.args.question,answer:event.observation.words||'No spoken answer recorded.',show:event.action.args.show||[],reply:event.reply});
 }
 return [...groups.values()];
}
