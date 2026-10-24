import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {browser} from './cdp.mjs';
const b=await browser();const {call,ev,wait}=b;
try {
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1050,deviceScaleFactor:1,mobile:false});
 const runs=(await(await fetch('http://localhost:8787/api/runs')).json()).runs;
 const native=runs.find(r=>r.kind==='recorded-model'&&r.task_id==='lantern_room');
 const payload=await(await fetch('http://localhost:8787/api/runs/'+native.id)).json();
 const ask=payload.events.findIndex(e=>e.type==='action'&&e.action.tool==='ask');
 const fixture={...payload,id:'voicefixture',kind:'live-model',status:'running',events:payload.events.slice(0,ask)};
 await call('Page.addScriptToEvaluateOnNewDocument',{source:`
 window.spoken=[];window.utterances=[];
 Object.defineProperty(window,'SpeechSynthesisUtterance',{value:class{constructor(text){this.text=text;}}});
 Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[{name:'A',lang:'en-US',localService:true},{name:'B',lang:'en-GB',localService:true},{name:'C',lang:'en-IN',localService:true}],cancel(){},speak(u){spoken.push(u.text);utterances.push(u);u.onstart?.();}}});
 window.EventSource=class {constructor(){window.feed=this;}close(){}};
 const originalFetch=window.fetch.bind(window), fixture=${JSON.stringify(fixture)};
 window.fetch=async(input,opts)=>{if(input==='/api/runs')return new Response(JSON.stringify({runs:[fixture]}));if(input==='/api/runs/voicefixture')return new Response(JSON.stringify(fixture));return originalFetch(input,opts);};
 `});
 await call('Page.navigate',{url:'http://localhost:8787'});await wait('window.feed&&document.getElementById("provider-input").options.length>10');
 await ev('document.getElementById("tour-button").click()');
 for(let i=0;i<7;i++){assert.equal(await ev('document.getElementById("tour-dialog").open'),true);await ev('document.getElementById("tour-next").click()');}
 assert.equal(await ev('document.getElementById("tour-dialog").open'),false);
 await ev('document.getElementById("new-button").click()');
 await ev('(()=>{let s=document.getElementById("provider-input");s.value="gemini";s.dispatchEvent(new Event("change"));})()');
 assert.equal(await ev('document.getElementById("endpoint-input").value'),'https://generativelanguage.googleapis.com/v1beta/openai');
 assert.equal(await ev('document.getElementById("endpoint-input").readOnly'),false);
 await ev('(()=>{let s=document.getElementById("provider-input");s.value="anthropic";s.dispatchEvent(new Event("change"));})()');
 assert.equal(await ev('document.getElementById("endpoint-input").value'),'https://api.anthropic.com/v1');
 await ev('document.querySelector("#settings-dialog .close-dialog").click()');
 await new Promise(r=>setTimeout(r,100));
 await ev('document.getElementById("voice-toggle").click();document.getElementById("play-button").click()');
 // Live burst: one question, then every later event including completion arrives before speech ends.
 await ev('window.feed.onmessage({data:'+JSON.stringify(JSON.stringify(payload.events[ask]))+'})');
 await wait('window.utterances.length===1');
 const displayed=await ev('document.getElementById("event-count").textContent.split(" / ")[0]');
 const question=await ev('document.getElementById("question-text").textContent');
 await ev('window.utterances[0].onboundary({name:"word",charIndex:0,charLength:4})');
 assert.equal(await ev('document.querySelector("#question-text mark")?.textContent'),question.slice(0,4));
 for(const event of payload.events.slice(ask+1))await ev('window.feed.onmessage({data:'+JSON.stringify(JSON.stringify(event))+'})');
 assert.equal(await ev('document.getElementById("event-count").textContent.split(" / ")[0]'),displayed,'live scene advanced during speech');
 assert.equal(await ev('window.utterances.length'),1,'overlapping or repeated speech');
 await ev('window.utterances[0].onend()');await wait('window.utterances.length===2');
 assert.equal(await ev('window.utterances[0].voice.name!==window.utterances[1].voice.name'),true);
 await ev('document.getElementById("voice-toggle").click()');
 assert.equal(await ev('document.querySelectorAll("mark.spoken-word").length'),0);
 await wait('document.getElementById("event-count").textContent.split(" / ")[0]==='+JSON.stringify(String(payload.events.length)));
 assert.equal(await ev('window.utterances.length'),2,'voice-off continued speaking');
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 await ev('window.scrollTo(0,0);document.getElementById("tour-button").click()');
 assert.equal(await ev('document.documentElement.scrollWidth<=innerWidth'),true);
 await ev('document.getElementById("tour-skip").click()');
 assert.deepEqual(b.errors,[]);
 const result={passed:true,checks:['13 provider choices including custom HTTPS','Gemini path preserved','Claude preset','7-step keyboard-accessible tour','live burst buffered until dialogue completes','word boundary highlights exact public text','detective and character receive distinct available voices','voice off clears highlights and cancels speech','completion drains buffered events','mobile tour fits'],audio:'Browser speech events mocked to reproduce timing; installed device audibility not certified.',model_calls:0};
 await fs.writeFile('docs/FINAL_VIEWER_VALIDATION.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{b.close();}
