// Authoring-only Chrome DevTools helper; no browser packages or runtime dependency.
export async function browser(port=9224) {
 const tab=await(await fetch(`http://localhost:${port}/json/new?about:blank`,{method:'PUT'})).json();
 const socket=new WebSocket(tab.webSocketDebuggerUrl);await new Promise(r=>socket.addEventListener('open',r,{once:true}));
 let seq=0;const pending=new Map(),errors=[];
 socket.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id){const j=pending.get(m.id);pending.delete(m.id);m.error?j?.reject(new Error(JSON.stringify(m.error))):j?.resolve(m.result);}else if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);});
 const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
 const ev=async expression=>{const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result?.value;};
 const wait=async expression=>{for(let i=0;i<400;i++){if(await ev(expression))return;await new Promise(r=>setTimeout(r,100));}throw new Error('Timed out: '+expression);};
 await call('Page.enable');await call('Runtime.enable');
 return {call,ev,wait,errors,close:()=>socket.close()};
}
