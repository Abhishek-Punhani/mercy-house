// Browser form failure path: invalid HTTPS endpoint is rejected before any run.
import fs from 'node:fs/promises';
const tab=await(await fetch('http://localhost:9224/json/new?'+encodeURIComponent('http://localhost:8787'),{method:'PUT'})).json();
const socket=new WebSocket(tab.webSocketDebuggerUrl);await new Promise(r=>socket.addEventListener('open',r,{once:true}));let seq=0;const jobs=new Map();
socket.addEventListener('message',e=>{const value=JSON.parse(e.data);if(value.id){jobs.get(value.id)?.(value);jobs.delete(value.id);}});
const call=(method,params={})=>new Promise(r=>{jobs.set(++seq,r);socket.send(JSON.stringify({id:seq,method,params}));});
const evaluate=async expression=>(await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true})).result.result.value;
try{
 for(let i=0;i<80;i++){if(await evaluate('document.getElementById("event-count")?.textContent!=="0 / 0"&&document.getElementById("task-input")?.options.length===5'))break;await new Promise(r=>setTimeout(r,100));}
 const before=await evaluate('(async()=>{return (await(await fetch("/api/runs")).json()).runs.length})()');
 await evaluate('(()=>{document.getElementById("new-button").click();let box=document.getElementById("configured-key-input");box.checked=false;box.dispatchEvent(new Event("change"));document.getElementById("key-input").value="browser-only-test-credential";document.getElementById("endpoint-input").value="http://insecure.invalid";document.getElementById("start-button").click();})()');
 for(let i=0;i<60;i++){if(await evaluate('document.getElementById("form-error").textContent.length>0'))break;await new Promise(r=>setTimeout(r,100));}
 const result=await evaluate('(async()=>({message:document.getElementById("form-error").textContent,cleared:document.getElementById("key-input").value==="",runs:(await(await fetch("/api/runs")).json()).runs.length,stored:localStorage.length===0&&sessionStorage.length===0}))()');
 if(!result.message.includes('HTTPS')||!result.cleared||result.runs!==before||!result.stored)throw new Error(JSON.stringify(result));
 await fs.writeFile('logs/viewer-form-checks.json',JSON.stringify({passed:true,checks:['form submission reaches backend validation','invalid endpoint creates no run','typed key cleared after rejection','no browser storage of keys']},null,2)+'\n');
 console.log(JSON.stringify({passed:true,model_calls:0}));
}finally{socket.close();}
