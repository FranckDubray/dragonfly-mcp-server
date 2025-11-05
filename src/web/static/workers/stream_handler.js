import { delay } from './utils.js';

export async function streamNdjson(url, {onChunk, onDone, onError, signal}={}){
  let backoff = 1000;
  while(!signal?.aborted){
    try{
      const r = await fetch(url, {signal});
      if (!r.ok) throw new Error('http '+r.status);
      const reader = r.body.getReader();
      const dec = new TextDecoder();
      let buf = '';
      while(true){
        const {value, done} = await reader.read();
        if (done) break;
        buf += dec.decode(value, {stream:true});
        let idx;
        while((idx=buf.indexOf('\n'))>=0){
          const line = buf.slice(0,idx); buf = buf.slice(idx+1);
          if(!line.trim()) continue;
          try{ const js = JSON.parse(line); onChunk && onChunk(js); }catch{}
        }
      }
      onDone && onDone();
      backoff = 1000;
      if (!signal) break; // single-shot
    }catch(e){ onError && onError(e); await delay(backoff); backoff = Math.min(30000, backoff*2); }
  }
}
