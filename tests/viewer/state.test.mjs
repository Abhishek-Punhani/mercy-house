import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,reduceEvent,stateAt} from '../../viewer/state.js';

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
