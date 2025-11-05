// Process Modal Graph — streaming (SSE + poll)
import { startSSE, startPoll } from './process_stream.js';

export async function startObserveStream(worker, onEvent, onTerminal){
  // Try SSE first
  try{
    await startSSE(worker, {
      onConnected: ()=>{},
      onEvent: (ev)=>{ try{ onEvent && onEvent(ev); }catch{} },
      onTerminal: ()=>{ try{ onTerminal && onTerminal(); }catch{} }
    });
    return ()=>{}; // caller can ignore for SSE
  }catch(e){ /* fall back to poll */ }

  // Poll fallback
  let stop = null;
  try{
    stop = startPoll(worker, {
      onEvent: (ev)=>{ try{ onEvent && onEvent(ev); }catch{} },
      onTerminal: ()=>{ try{ onTerminal && onTerminal(); }catch{} }
    });
  }catch{}
  return ()=>{ try{ stop && stop(); }catch{} };
}
