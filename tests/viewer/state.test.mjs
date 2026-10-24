import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,reduceEvent,stateAt,reportOutcome,findingDescription} from '../../viewer/state.js';

test('only observed people enter a scene; movement clears previous presence',()=>{
 let s=reduceEvent(initialState(),{type:'opening',opening:{now:{place:{id:'archive'}}}});
 assert.deepEqual(s.here,[]);
 s=reduceEvent(s,{type:'action',action:{tool:'people_here',args:{}},observation:{people:[{id:'p',name:'A witness'}]}});
 assert.deepEqual(s.here,['p']);
 s=reduceEvent(s,{type:'action',action:{tool:'go',args:{destination:'hall'}},observation:{place:{id:'hall'}}});
 assert.deepEqual(s.here,[]);assert.deepEqual(s.visited,['archive','hall']);
});
test('custody acknowledgements preserve a discovered document and note labels',()=>{
 let s=reduceEvent(initialState(),{type:'action',action:{tool:'search',args:{}},observation:{findings:[{record_id:'r1',object_id:'o1',description:'A letter.'}]}});
 s=reduceEvent(s,{type:'action',action:{tool:'collect',args:{}},observation:{record_id:'r1',secured:'o1'}});
 assert.equal(s.records.r1.description,'A letter.');assert.deepEqual(s.secured,['o1']);
 s=reduceEvent(s,{type:'action',action:{tool:'record_note',args:{}},observation:{record_id:'r2',summary:'An unverified idea.',hypotheses:[{statement:'A theory',status:'open',sources:['r1']}]}});
 assert.equal(s.note,'An unverified idea.');assert.equal(s.hypotheses[0].status,'open');assert.equal(s.finished,null);
});
test('replay seeking cannot reveal a future observation',()=>{
 const events=[{type:'opening',opening:{now:{place:{id:'archive'}}}},{type:'action',action:{tool:'search',args:{}},observation:{findings:[{record_id:'r1',description:'Later discovery'}]}}];
 assert.equal(Object.keys(stateAt(events,1).records).length,0);
 assert.equal(stateAt(events,2).records.r1.description,'Later discovery');
});
test('a labeled checkpoint retains prior observations and selection is not a verdict',()=>{
 let state=reduceEvent(initialState(),{type:'opening',opening:{now:{place:{id:'hall'},people:[{id:'known',name:'Already observed'}]},notes:[{record_id:'r1',description:'Previously acquired'}]}});
 assert.deepEqual(state.here,['known']);assert.equal(state.records.r1.description,'Previously acquired');
 state=reduceEvent(state,{type:'selection',selected_tool:'ask',probability:.75,candidate_count:8});
 assert.equal(state.selection.probability,.75);assert.equal(state.finished,null);assert.deepEqual(state.hypotheses,[]);
});

test('accepted report persists with sources and does not appear before its event',()=>{
 const submitted={type:'action',action:{tool:'submit_report',args:{findings:[{actor:'observed-person',predicate:'killed',object:'victim',sources:['r1']}],narrative:'A supported reconstruction.'}},observation:{submitted:true}};
 const events=[{type:'opening',opening:{now:{place:{id:'inn'}}}},submitted,{type:'finished',termination:'success',result:{success:true,score:1}}];
 assert.equal(stateAt(events,1).submission,null);
 const state=stateAt(events,3);assert.equal(state.submission.findings[0].sources[0],'r1');assert.equal(state.submission.narrative,'A supported reconstruction.');
 assert.equal(reportOutcome(state,'recorded-model').label,'Case solved');
});
test('denied reports and arbitrary shell stdout cannot fabricate an accepted report',()=>{
 let state=reduceEvent(initialState(),{type:'action',action:{tool:'submit_report',args:{findings:[]}},observation:{error:'Invalid report'}});
 assert.equal(state.submission,null);
 state=reduceEvent(state,{type:'action',action:{tool:'run_command',args:{command:'printf a fabricated report'}},observation:{stdout:'{"submitted":true,"findings":["not trusted"]}',exit_code:0}});
 assert.equal(state.submission,null);
 // A real CLI call is observed as an inner public tool action, not parsed from stdout.
 state=reduceEvent(state,{type:'action',action:{tool:'submit_report',args:{findings:[],narrative:'Actual inner town call.'}},observation:{submitted:true}});
 state=reduceEvent(state,{type:'action',action:{tool:'run_command',args:{command:'town submit_report ...'}},observation:{stdout:'{"submitted":true}',exit_code:0}});
 assert.equal(state.submission.narrative,'Actual inner town call.');
});
test('forced endings do not invent a submission and a grade determines case success',()=>{
 const state=reduceEvent(initialState(),{type:'finished',termination:'step_cap',result:{success:false,score:0}});
 assert.equal(state.submission,null);assert.equal(reportOutcome(state,'recorded-model').label,'Case not solved');
 assert.equal(reportOutcome(reduceEvent(initialState(),{type:'stopped',message:'Stopped before grading.'}),'live-model').label,'Investigation not graded');
});
test('checkpoint completion does not imply that its Town case was solved',()=>{
 const state=reduceEvent(initialState(),{type:'finished',termination:'checkpoint_success',exercise_reward:1,result:{success:false,score:0}});
 assert.equal(reportOutcome(state,'selector-checkpoint').label,'Checkpoint completed');
 assert.equal(reportOutcome(state,'recorded-model').label,'Case not solved');
});

test('fatal assistance and aid to a victim have distinct display meanings',()=>{
 const facilitation={actor:'Vedant',predicate:'assisted',object:'Mira',sources:['r1']};
 assert.match(findingDescription(facilitation),/knowingly facilitated the fatal incident involving/);
 assert.equal(findingDescription({...facilitation,predicate:'aided'}),'Vedant · gave aid to · Mira');
 assert.equal(facilitation.predicate,'assisted'); // Display does not rewrite exact submitted JSON.
});
