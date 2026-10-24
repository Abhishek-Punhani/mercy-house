import test from 'node:test';
import assert from 'node:assert/strict';
import {BrowserVoice,dialogueParts,caseBriefing} from '../../viewer/speech.js';

test('narration uses spoken public dialogue, not hidden fields or recalled private material',()=>{
 const parts=dialogueParts({type:'action',action:{tool:'ask',args:{pid:'p',question:'What did you see?'}},observation:{words:'A lamp.',private_state:'secret-canary',recollections:[{text:'not spoken'}]}},{p:{name:'A witness'}});
 assert.equal(parts.length,2);assert.match(parts[0].text,/What did you see/);assert.match(parts[1].text,/A lamp/);
 assert.doesNotMatch(JSON.stringify(parts),/secret-canary|not spoken/);
 assert.deepEqual(dialogueParts({type:'reply',note:'private reasoning'}),[]);
});
test('briefing reads only public setup and does not inspect arbitrary private fields',()=>{
 const s=caseBriefing({briefing:'An incident was reported.',scope:'Inspect the room.',private_solution:'secret'},{place:{name:'An inn'},private_world:'canary'});
 assert.match(s,/An inn/);assert.match(s,/An incident/);assert.doesNotMatch(s,/secret|canary/);
});
test('unavailable browser speech falls back without blocking investigation',async()=>{
 const messages=[];const voice=new BrowserVoice({},m=>messages.push(m));assert.equal(voice.supported,false);
 assert.equal(await voice.speak([{text:'Briefing'}]),'unavailable');assert.match(messages[0],/text remains/);
});
test('speech queues questions before answers and cancellation resolves waiting playback',async()=>{
 const spoken=[];class Utterance{constructor(text){this.text=text;}}
 const synth={getVoices:()=>[],cancel(){},speak(u){spoken.push(u);}};
 const voice=new BrowserVoice({speechSynthesis:synth,SpeechSynthesisUtterance:Utterance});
 const one=voice.speak([{speaker:'detective',text:'Question'},{speaker:'witness',text:'Answer'}]);
 assert.equal(spoken[0].text,'Question');spoken[0].onend();assert.equal(spoken[1].text,'Answer');spoken[1].onend();assert.equal(await one,'finished');
 const pending=voice.speak([{text:'A long briefing'}]);voice.cancel();assert.equal(await pending,'cancelled');
 spoken.at(-1).onend();assert.equal(voice.current,null);assert.equal(voice.queue.length,0);
});
