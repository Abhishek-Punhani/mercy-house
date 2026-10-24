// Record one fresh public-site investigation, including the real start form.
// Provider credentials stay in memory and a password field; never in artifacts.
import fs from 'node:fs/promises';
import {spawnSync,execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {browser} from './cdp.mjs';
const origin=process.env.MERCY_RECORD_ORIGIN || 'https://mercyhouse.abhi07.xyz';
const output='docs/investigation-end-to-end.mp4';
const folder='logs/live-investigation-video-'+Date.now();
await fs.mkdir(folder,{recursive:true});
const config=Object.fromEntries((await fs.readFile('.env','utf8')).split('\n').flatMap(line=>{
 const m=line.match(/^\s*(?:export\s+)?([A-Z_]+)=(.*)$/);if(!m)return [];
 return [[m[1],m[2].trim().replace(/^(['"])(.*)\1$/,'$2')]];
}));
let apiKey=process.env.API_KEY || config.API_KEY;
if(!apiKey)throw new Error('Configure the development API key in the ignored .env first.');
const model=process.env.MODEL || config.MODEL,base=process.env.BASE_URL || config.BASE_URL;
const seed=Number(process.env.MERCY_RECORD_SEED || 7);
const existing=(await(await fetch(origin+'/api/runs')).json()).runs;
if(existing.some(r=>['starting','building','running','stopping'].includes(r.status)))throw new Error('An investigation is active; record after it finishes.');
const b=await browser(),{call,ev,wait}=b;
let recording=false,loop,frames=[],chapters=[],startedAt=Date.now(),runId=null,final=null;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function caption(text,seconds=0){
 const time=(Date.now()-startedAt)/1000;chapters.push({seconds:Number(time.toFixed(3)),caption:text});
 await ev('(()=>{const el=document.getElementById("video-caption");el.textContent='+JSON.stringify(text)+';if(el.matches(":popover-open"))el.hidePopover();el.showPopover();})()');
 if(seconds)await delay(seconds*1000);
}
const click=id=>ev('document.getElementById('+JSON.stringify(id)+').click()');
const set=(id,value)=>ev('(()=>{const el=document.getElementById('+JSON.stringify(id)+');el.value='+JSON.stringify(value)+';el.dispatchEvent(new Event("change",{bubbles:true}));})()');
try {
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1050,deviceScaleFactor:1,mobile:false});
 await call('Page.addScriptToEvaluateOnNewDocument',{source:`
 localStorage.setItem('mercy-tour-v1','seen');
 const realFetch=window.fetch.bind(window);
 window.fetch=async(input,options)=>{const response=await realFetch(input,options);if(input==='/api/runs'&&options?.method==='POST'){const value=await response.clone().json();if(value.id)window.recordingRunId=value.id;}return response;};
 `});
 await call('Page.navigate',{url:origin});await wait('document.getElementById("provider-input")?.options.length===13');
 await ev(`(()=>{document.getElementById('voice-toggle').checked=false;const el=document.createElement('div');el.id='video-caption';el.popover='manual';el.style.cssText='position:fixed;top:auto;right:auto;margin:0;bottom:14px;left:50%;white-space:pre-line;transform:translateX(-50%);width:calc(100% - 100px);max-width:1250px;padding:18px 24px;background:#090f1bf5;color:#edf4ff;border:1px solid #66e6cd;border-radius:12px;font:18px/1.5 system-ui;box-shadow:0 12px 40px #0008;pointer-events:none;';document.body.append(el);})()`);
 startedAt=Date.now();recording=true;
 loop=(async()=>{while(recording){const time=Date.now();const shot=await call('Page.captureScreenshot',{format:'jpeg',quality:86});const path=folder+'/'+String(frames.length).padStart(6,'0')+'.jpg';await fs.writeFile(path,Buffer.from(shot.data,'base64'));frames.push({path,time});await delay(Math.max(0,250-(Date.now()-time)));}})();
 await caption('How to start an investigation in Mercy House\nA fresh live API run, from setup to final report. Captions only; voice mode is off.',6);
 await click('new-button');await wait('document.getElementById("settings-dialog").open');
 await caption('1. Click New investigation. Choose a case.\nStart with The Lantern Room for an introductory investigation.',6);
 await set('task-input','lantern_room');await ev('document.getElementById("briefing-preview-title").scrollIntoView({block:"start"})');
 await caption('2. Read the case briefing before starting.\nIt describes your assignment; evidence and witness accounts must be discovered during the case.',8);
 await set('provider-input','configured');await set('model-input',model);await set('endpoint-input',base);await set('seed-input',String(seed));
 await ev('document.getElementById("provider-input").scrollIntoView({block:"start"})');
 await caption('3. Choose your provider, model ID and case seed.\nThis demonstration uses the organizer’s configured endpoint. Other providers are available in the selector.',8);
 const password=await ev('document.getElementById("key-input").type');if(password!=='password')throw new Error('Credential field is not masked.');
 await ev('document.getElementById("key-input").focus()');await call('Input.insertText',{text:apiKey});apiKey='';config.API_KEY='';
 await ev('document.getElementById("start-button").scrollIntoView({block:"center"})');
 await caption('4. Enter your provider API key in the masked field.\nOn the public demo, your key powers both the detective and the town’s character agents for this run.',7);
 await caption('5. Click Begin live investigation.\nThe system prepares isolated containers and checks that the selected case has a valid reference solution.',3);
 const submittedAt=Date.now();await click('start-button');
 await wait('!!window.recordingRunId || !!document.getElementById("form-error").textContent');
 runId=await ev('window.recordingRunId');if(!runId)throw new Error('The start form rejected the run; no investigation was created.');
 await wait('!document.getElementById("settings-dialog").open');
 console.log(JSON.stringify({started_run:runId,task_id:'lantern_room',seed,origin,frames_folder:folder}));
 await caption('The live investigation is starting.\nContainer preparation and model response times are shown as they happen; this is not a prerecorded replay.');
 const seen=new Set();let lastCaption=Date.now(),lastNotice=Date.now(),latest=null;
 const messages={
  ask:'The detective is interviewing a character.\nQuestions, answers and any shown documents appear as the model investigates.',
  search:'The detective is searching the current location.\nNewly acquired material appears in the evidence tray on the right.',
  collect:'The detective is collecting a discovered item.\nEvidence must be acquired through the world tools before it can support a report.',
  go:'The detective is travelling to another location.\nThe background and people present follow the actual world state.',
  compare:'The detective is comparing acquired sources.\nStatements and physical records must be checked before drawing a conclusion.',
  submit_report:'The detective is submitting its report.\nThe verifier checks its claims against the evidence acquired during this investigation.'
 };
 const deadline=Date.now()+950000;
 while(Date.now()<deadline){
  const response=await fetch(origin+'/api/runs/'+runId);if(!response.ok)throw new Error('Could not read the public live run.');latest=await response.json();
  final=[...latest.events].reverse().find(e=>['finished','run_error','stopped'].includes(e.type));
  if(final)break;
  const pending=latest.events.filter(e=>e.type==='action'&&messages[e.action?.tool]&&!seen.has(e.action.tool));
  if(pending.length&&Date.now()-lastCaption>7500){const action=pending[0].action.tool;seen.add(action);lastCaption=Date.now();await caption(messages[action]);}
  if(Date.now()-lastNotice>20000){console.log(JSON.stringify({run:runId,status:latest.status,public_events:latest.events.length,elapsed_seconds:Math.round((Date.now()-submittedAt)/1000)}));lastNotice=Date.now();}
  await delay(1000);
 }
 if(!final)throw new Error('Investigation still active at the recording deadline; no final result is inferred.');
 await caption('The investigation has ended.\nWe will inspect the actual submitted report and verifier outcome, including any unsupported findings.',5);
 await wait('!document.getElementById("report-panel").classList.contains("hidden")');
 await ev('document.getElementById("report-panel").scrollIntoView({block:"start"})');
 const score=final.result?.score;
 await caption('6. Read the final report and verifier result.\n'+(typeof score==='number'?'This run scored '+score.toFixed(2)+'. ':'')+'Supported, false and unsupported findings are listed separately. Guessing a name alone earns no proof.',10);
 const source=await ev('!!document.querySelector("#report-panel .report-source")');
 if(source){await ev('document.querySelector("#report-panel .report-source").click()');await caption('Click a cited source to inspect the evidence behind a conclusion.\nThe viewer exposes acquired public records; private world files and unreleased character memories stay hidden.',7);await ev('document.querySelector("#detail-dialog .close-dialog").click()');}
 const interviews=await ev('!document.getElementById("interview-panel").classList.contains("hidden")');
 if(interviews){await ev('document.getElementById("interview-panel").scrollIntoView({block:"start"});document.querySelector("#interview-list details")?.setAttribute("open","")');await caption('The interview notebook preserves the questions and answers already observed.\nUse it to review follow-ups and documents shown during questioning.',8);}
 await ev('window.scrollTo({top:0,behavior:"instant"})');
 await caption('Start your own investigation at mercyhouse.abhi07.xyz\nNew investigation → case → provider and model → masked API key → Begin. Recorded cases remain free to watch.',8);
 recording=false;await loop;
 const finishedAt=Date.now(),lines=[];
 for(let i=0;i<frames.length;i++){lines.push("file '"+frames[i].path.split('/').at(-1)+"'");lines.push('duration '+((i+1<frames.length?frames[i+1].time:finishedAt)-frames[i].time)/1000);}
 lines.push("file '"+frames.at(-1).path.split('/').at(-1)+"'");await fs.writeFile(folder+'/frames.txt',lines.join('\n'));
 const encoded=spawnSync('ffmpeg',['-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',folder+'/frames.txt','-vf','fps=24,format=yuv420p','-an','-c:v','libx264','-preset','fast','-crf','23','-movflags','+faststart',output],{encoding:'utf8'});
 if(encoded.status)throw new Error(encoded.stderr);
 const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-show_entries','format=duration,size:stream=codec_type,width,height','-of','json',output],{encoding:'utf8'}));
 if(probe.streams.some(s=>s.codec_type==='audio'))throw new Error('An unexpected audio stream was created.');
 const posterTime=Math.max(0,Number(probe.format.duration)-4);
 execFileSync('ffmpeg',['-y','-hide_banner','-loglevel','error','-ss',String(posterTime),'-i',output,'-frames:v','1','-q:v','3','docs/investigation-video-poster.jpg']);
 const srtTime=t=>{const ms=Math.max(0,Math.round(t*1000));return String(Math.floor(ms/3600000)).padStart(2,'0')+':'+String(Math.floor(ms/60000)%60).padStart(2,'0')+':'+String(Math.floor(ms/1000)%60).padStart(2,'0')+','+String(ms%1000).padStart(3,'0');};
 await fs.writeFile('docs/investigation-end-to-end.srt',chapters.map((c,i)=>(i+1)+'\n'+srtTime(c.seconds)+' --> '+srtTime(chapters[i+1]?.seconds??Number(probe.format.duration))+'\n'+c.caption+'\n').join('\n'));
 const manifest={file:output,origin,run_id:runId,task_id:'lantern_room',seed,model,recorded_at:new Date().toISOString(),duration_seconds:Number(probe.format.duration),bytes:Number(probe.format.size),sha256:createHash('sha256').update(await fs.readFile(output)).digest('hex'),audio_track:false,captions:'Burned into video; separate SRT included.',recording:'One fresh live public-site investigation started through the real form. Continuous screen capture at normal time, no replay substitution, no favorable reroll.',credential_handling:'Entered from ignored local environment directly into password input; no plaintext key recorded or written into artifacts.',final_result:final,chapters,public_events:latest.events.length,javascript_errors:b.errors};
 await fs.writeFile('docs/INVESTIGATION_VIDEO.json',JSON.stringify(manifest,null,2)+'\n');
 console.log(JSON.stringify({file:output,run_id:runId,seconds:manifest.duration_seconds,score,public_events:latest.events.length,javascript_errors:b.errors}));
 if(b.errors.length)throw new Error('Browser reported JavaScript errors; inspect recording manifest.');
}finally{recording=false;if(loop)await loop;b.close();}
