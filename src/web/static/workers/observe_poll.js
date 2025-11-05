















// Observe (polling via /execute tool API)
// Calls the py_orchestrator tool with operation=observe (passive), repeats until stopped.
export function startObservePoll(worker, onEvent, onTerminal){
  let abort = false;
  let timer = 0;
  let lastRowId = 0; // resume cursor

  const TERMINALS = new Set(['completed','failed','canceled','terminal']);

  function isTerminalResponse(js){
    try{
      const status = String(js && js.status || '').toLowerCase();
      const phase  = String(js && js.phase  || '').toLowerCase();
      if (TERMINALS.has(status) || TERMINALS.has(phase)) return true;
      if (js && (js.terminal === true || js.done === true || js.completed === true)) return true;
    }catch{}
    return false;
  }

  async function loop(){
    while(!abort){
      try{
        const payload = {
          tool: 'py_orchestrator',
          params: {
            operation: 'observe',
            worker_name: worker,
            observe: { timeout_sec: 30, max_events: 200, ...(lastRowId>0? {from_rowid: lastRowId} : {}) },
          }
        };
        if (window.__OBSERVE_DEBUG) console.log('[OBSERVE][poll] → fetch /execute', payload);

        const r = await fetch('/execute', { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        if (window.__OBSERVE_DEBUG) console.log('[OBSERVE][poll] HTTP', r.status, r.ok);
        if (!r.ok){
          const txt = await r.text().catch(()=> '');
          console.error('[OBSERVE][poll] HTTP error', r.status, txt);
          await sleep(1200);
          continue;
        }

        const js = await r.json().catch(()=>({}));
        if (window.__OBSERVE_DEBUG) console.log('[OBSERVE][poll] response', js);

        // Update resume cursor if provided
        try{ if (Number.isFinite(Number(js?.last_rowid))) lastRowId = Number(js.last_rowid); }catch{}

        if (Array.isArray(js?.events)){
          for (const ev of js.events){
            try{ if (lastRowId>0 && typeof ev==='object' && ev) ev.last_rowid = lastRowId; }catch{}
            try{ onEvent && onEvent(ev); }catch{}
          }
        }

        if (isTerminalResponse(js)){
          if (window.__OBSERVE_DEBUG) console.log('[OBSERVE][poll] terminal detected → stop');
          try{ onTerminal && onTerminal(js); }catch{}
          abort = true;
          break;
        }
      }catch(e){
        console.error('[OBSERVE][poll] network/error', e);
        await sleep(1200);
      }
    }
  }
  loop();
  return ()=>{ abort = true; if (timer) clearTimeout(timer); };
}

function sleep(ms){ return new Promise(r=>setTimeout(r, ms)); }

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
