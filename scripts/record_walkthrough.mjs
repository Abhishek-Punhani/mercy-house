// Records actual browser interactions with labeled, retained public model traces.
// No provider key, hidden case file, speech mock, or model generation is used.
import fs from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import {browser} from './cdp.mjs';
const origin=process.env.MERCY_RECORD_ORIGIN || 'http://localhost:8787';
const output='docs/submission-walkthrough.mp4',folder='logs/submission-video-frames';
await fs.mkdir(folder,{recursive:true});
const b=await browser(),{call,ev,wait}=b;
let recording=false,loop,frames=[],chapters=[],caption='';
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function title(text,seconds=5){caption=text;chapters.push({seconds:frames.length?Number((Date.now()-frames[0].time)/1000).toFixed(2):'0',caption:text});await ev('(()=>{const el=document.getElementById("video-caption");el.textContent='+JSON.stringify(text)+';if(el.matches(":popover-open"))el.hidePopover();el.showPopover();})()');await delay(seconds*1000);}
const click=id=>ev('document.getElementById('+JSON.stringify(id)+').click()');
async function seek(index){await ev('(()=>{let s=document.getElementById("seek");s.value='+index+';s.dispatchEvent(new Event("input"));window.scrollTo({top:0,behavior:"instant"});})()');}
try {
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1050,deviceScaleFactor:1,mobile:false});
 await call('Page.navigate',{url:origin});await wait('document.getElementById("provider-input")?.options.length>10');
 await ev(`(()=>{localStorage.setItem('mercy-tour-v1','seen');document.getElementById('toast').classList.add('hidden');const el=document.createElement('div');el.id='video-caption';el.popover='manual';el.style.cssText='position:fixed;top:auto;right:auto;margin:0;bottom:14px;left:50%;white-space:pre-line;transform:translateX(-50%);width:calc(100% - 100px);max-width:1250px;padding:18px 24px;background:#090f1bf5;color:#edf4ff;border:1px solid #66e6cd;border-radius:12px;z-index:2147483647;font:18px/1.5 system-ui;box-shadow:0 12px 40px #0008;pointer-events:none;';document.body.append(el);})()`);
 recording=true;loop=(async()=>{while(recording){const time=Date.now();const r=await call('Page.captureScreenshot',{format:'jpeg',quality:84});const path=folder+'/'+String(frames.length).padStart(5,'0')+'.jpg';await fs.writeFile(path,Buffer.from(r.data,'base64'));frames.push({path,time});await delay(Math.max(0,250-(Date.now()-time)));}})();
 await title('MERCY HOUSE · Kasukabe Defence Force | Aditya Ahirwar · Abhishek · Tapis Samaiya. A detective environment where every conclusion needs evidence.',6);
 await click('tour-button');await title('New users can take a seven-step guided tour. Watching recorded cases costs no API calls.',5);
 for(let i=0;i<3;i++){await click('tour-next');await delay(1300);}
 await title('Optional browser speech waits for each exchange. Word highlighting follows browser boundary events; installed voices are assigned consistently to characters.',6);
 await click('tour-skip');await click('briefing-button');await title('Begin with the public case briefing. The detective must discover the evidence and interview witnesses during the investigation.',7);
 await ev('document.querySelector("#briefing-dialog .close-dialog").click()');await click('new-button');
 await ev('document.getElementById("provider-input").focus();document.getElementById("provider-input").value="gemini";document.getElementById("provider-input").dispatchEvent(new Event("change"))');
 await ev('document.getElementById("provider-input").scrollIntoView({block:"center"})');
 await title('Bring your provider API key. Presets include OpenAI, Claude, Gemini, OpenRouter and more. Model IDs are entered by the user; compatible custom HTTPS endpoints are also supported.',8);
 await ev('document.getElementById("provider-input").value="anthropic";document.getElementById("provider-input").dispatchEvent(new Event("change"))');
 await title('Claude uses a Messages API adapter. Other presets use compatible chat endpoints. The public host stores no team key. No live run is launched in this recording.',6);
 await ev('document.querySelector("#settings-dialog .close-dialog").click();window.scrollTo(0,0)');
 const runs=(await(await fetch(origin+'/api/runs')).json()).runs;
 const native=runs.find(r=>r.kind==='recorded-model'&&r.task_id==='lantern_room');
 const data=await(await fetch(origin+'/api/runs/'+native.id)).json();
 await click('library-button');await wait('document.getElementById("library-dialog").open');
 await ev('document.querySelector('+JSON.stringify('[data-run-id="'+native.id+'"]')+').click()');
 await wait('!document.getElementById("library-dialog").open');
 const asks=data.events.map((e,i)=>({e,i})).filter(x=>x.e.type==='action'&&x.e.action.tool==='ask');
 await seek(asks[0].i+1);await title('This is an actual retained API detective run, replayed for inspection. The detective asks a witness what they personally saw. It is not a newly running agent.',8);
 if(asks.length>1){await seek(asks[1].i+1);await title('The detective can return, ask follow-ups and show acquired documents. Each character answers from their own released recollections. The full interview notebook preserves the exchanges.',7);}
 const discovery=data.events.findIndex(e=>e.type==='action'&&e.action.tool==='search');
 if(discovery>=0){await seek(discovery+1);await title('Searches expose material through public world tools. Travel, access, interviews and comparisons consume the investigation budget.',6);}
 await click('end-button');await wait('document.getElementById("detail-dialog").open');await ev('document.querySelector("#detail-dialog .close-dialog").click();document.getElementById("report-panel").scrollIntoView({block:"start"})');
 await title('The report stays visible. The rule-based verifier checks acquired support and separates supported, false and unsupported claims. Naming the right killer without proof does not score.',9);
 const source=await ev('!!document.querySelector("#report-panel .report-source")');
 if(source){await ev('document.querySelector("#report-panel .report-source").click()');await title('Click a cited source to inspect the material the detective actually acquired. Private answers and unreleased memories are never included in this observer feed.',6);await ev('document.querySelector("#detail-dialog .close-dialog").click()');}
 const failure=runs.find(r=>r.kind==='recorded-model'&&r.task_id==='mercy_inquest');
 if(failure){await ev('window.scrollTo(0,0)');await click('library-button');await wait('document.getElementById("library-dialog").open');await ev('document.getElementById("library-level").value="all"');await wait('!!document.querySelector('+JSON.stringify('[data-run-id="'+failure.id+'"]')+')');await ev('document.querySelector('+JSON.stringify('[data-run-id="'+failure.id+'"]')+').click()');await wait('!document.getElementById("library-dialog").open');await wait('document.getElementById("case-title").textContent==='+JSON.stringify(failure.label));await click('end-button');await wait('document.getElementById("detail-dialog").open');await ev('document.querySelector("#detail-dialog .close-dialog").click();document.getElementById("report-panel").scrollIntoView({block:"start"})');await title('Failures remain visible. The frozen selector did not solve either of the two elite transfer cases. Stronger results on prepared practice checkpoints are not a claim of full-case mastery.',8);}
 await ev('window.scrollTo(0,0)');
 await title('RL trains a small action selector on CPU: 6,000 practice episodes, 132 coefficients. The API language model stays fixed. The detective still needs to gather evidence and submit a supported report.',8);
 await title('Explore: mercyhouse.abhi07.xyz  |  Source: github.com/Abhishek-Punhani/mercy-house\nThank you. Kasukabe Defence Force · Captioned UI walkthrough; browser audio is not recorded.',7);
 recording=false;await loop;
 const lines=[];for(let i=0;i<frames.length;i++){lines.push("file '"+frames[i].path.split('/').at(-1)+"'");lines.push('duration '+((i+1<frames.length?frames[i+1].time:Date.now())-frames[i].time)/1000);}lines.push("file '"+frames.at(-1).path.split('/').at(-1)+"'");
 await fs.writeFile(folder+'/frames.txt',lines.join('\n'));
 const result=spawnSync('ffmpeg',['-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',folder+'/frames.txt','-vf','fps=24,format=yuv420p','-c:v','libx264','-preset','fast','-crf','24','-movflags','+faststart',output],{encoding:'utf8'});
 if(result.status)throw new Error(result.stderr);
 if(b.errors.length)throw new Error(b.errors.join(';'));
 const manifest={file:output,seconds:(frames.at(-1).time-frames[0].time)/1000,frames:frames.length,resolution:'1440 × 1050',chapters,content:'Actual local viewer interactions with retained public API traces. Recorded replay, not a fresh live model run. Captions; no audio track. No speech mocks used.',model_calls:0,recorded_at:new Date().toISOString()};
 await fs.writeFile('docs/SUBMISSION_VIDEO.json',JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify(manifest));
}finally{recording=false;if(loop)await loop;b.close();}
