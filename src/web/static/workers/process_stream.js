
// SSE + poll observe for process modal
import { startObservePoll } from './observe_poll.js';

export function startSSE(worker, {onEvent, onTerminal, onConnected, signal}){
  return (async ()=>{
    const url = new URL('/workers/api/observe/stream', location.origin);
    url.searchParams.set('worker', worker);
    url.searchParams.set('timeout_sec', '30');
    url.searchParams.set('max_events', '200');
    const ctrl = new AbortController();
    if (signal) signal.addEventListener('abort', ()=>ctrl.abort(), {once:true});
    const r = await fetch(url.toString(), { signal: ctrl.signal });
    if (!r.ok || !r.body) throw new Error('SSE not available');
    onConnected && onConnected();
    const reader = r.body.getReader(); const dec = new TextDecoder(); let buf='';
    while(true){
      const {value, done} = await reader.read();
      if (done) break;
      buf += dec.decode(value, {stream:true});
      let idx;
      while((idx=buf.indexOf('\n'))>=0){
        const line = buf.slice(0,idx); buf = buf.slice(idx+1);
        if(!line.trim()) continue;
        try{
          const ev = JSON.parse(line);
          const ch = String(ev?.chunk_type||'');
          if (ch==='terminal' || (ch==='status' && ['completed','failed','canceled'].includes(String(ev?.phase||'').toLowerCase()))) {
            onTerminal && onTerminal(ev);
            try{ ctrl.abort(); }catch{}
            return;
          }
          onEvent && onEvent(ev);
        }catch{}
      }
    }
  })();
}

export function startPoll(worker, {onEvent, onTerminal}){
  return startObservePoll(worker, onEvent, onTerminal);
}
