































// Lightweight API facade (with in-memory cache for /tools)
const __toolsCache = { ts: 0, data: null };
const TOOLS_CACHE_MS = 15 * 60 * 1000; // 15 minutes (augmented)

async function postExecute(payload){
  const r = await fetch('/execute', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
  if (!r.ok) throw 0;
  const js = await r.json();
  return (js && js.result) ? js.result : js;
}

export const api = {
  async list(){ const r=await fetch('/workers/api/list'); if(!r.ok) throw 0; return r.json(); },
  async status(w){
    // MCP /execute (tool: py_orchestrator, operation=status)
    return postExecute({ tool: 'py_orchestrator', params: { operation: 'status', worker_name: w, include_metrics: true } });
  },
  async identityWorker(w){ const r=await fetch(`/workers/api/identity?worker=${encodeURIComponent(w)}`); if(!r.ok) throw 0; return r.json(); },
  // Graph tools (JSON nodes/edges) via MCP /execute (no server /workers/api/graph)
  async graphTools(w){
    return postExecute({
      tool: 'py_orchestrator',
      params: {
        operation: 'graph',
        worker_name: w,
        graph: { kind: 'process', include: { shapes: true, emojis: true, labels: true }, render: { mermaid: false } }
      }
    });
  },
  async kpis(){ try{ const r=await fetch('/workers/api/kpis'); if(!r.ok) throw 0; return r.json(); }catch{ return {accepted:true,status:'ok',workers:null,actifs:null,steps24h:null,tokens24h:null,qualite7j:null}; } },
  async leaderIdentity(name){ const r=await fetch(`/workers/api/leader_identity?name=${encodeURIComponent(name)}`); if(!r.ok) throw 0; return r.json(); },
  async leaderChatHistory(name, limit=20){ const r=await fetch(`/workers/api/leader_chat_global?name=${encodeURIComponent(name)}&limit=${limit}`); if(!r.ok) throw 0; return r.json(); },
  async leaderChatSend(name, message, model='gpt-5-mini', history_limit=20){ const p=new URLSearchParams({name,message,model,history_limit:String(history_limit)}); const r=await fetch(`/workers/api/leader_chat_global?${p.toString()}`,{method:'POST'}); if(!r.ok) throw 0; return r.json(); },

  // START via MCP /execute
  async startDebug(w, wf){
    return postExecute({
      tool: 'py_orchestrator',
      params: {
        operation: 'start',
        worker_name: w,
        worker_file: wf || undefined,
        hot_reload: true,
        debug: { enable_on_start: true, pause_at_start: true, action: 'enable_now' }
      }
    });
  },
  async startObserve(w, wf){
    return postExecute({
      tool: 'py_orchestrator',
      params: {
        operation: 'start',
        worker_name: w,
        worker_file: wf || undefined,
        hot_reload: true
      }
    });
  },

  // Debug controls via MCP /execute
  async step(w){
    return postExecute({ tool: 'py_orchestrator', params: { operation: 'debug', worker_name: w, debug: { action: 'step', timeout_sec: 90 } } });
  },
  async cont(w){
    return postExecute({ tool: 'py_orchestrator', params: { operation: 'debug', worker_name: w, debug: { action: 'continue', timeout_sec: 90 } } });
  },

  // STOP via MCP /execute
  async stop(w){
    return postExecute({ tool: 'py_orchestrator', params: { operation: 'stop', worker_name: w, stop: { mode: 'soft' } } });
  },

  async toolsRegistry(){
    const now = Date.now();
    if (__toolsCache.data && (now - __toolsCache.ts) < TOOLS_CACHE_MS){
      return __toolsCache.data;
    }
    // Try straight /tools first
    let r = await fetch('/tools');
    let js;
    try{ js = await r.json(); }catch{ js = null; }
    // If failed or empty, try reload fallback once
    if (!r.ok || !js || (Array.isArray(js.tools) && js.tools.length===0)){
      try{
        const rr = await fetch('/tools?reload=1&list=1');
        const js2 = await rr.json();
        if (rr.ok && js2) js = js2;
      }catch{}
    }
    if (!js) throw 0;
    __toolsCache.ts = now; __toolsCache.data = js;
    return js;
  },

  // ===== Replay (runs & steps) =====
  async replayRuns(worker){
    const r = await fetch(`/workers/api/replay/runs?worker=${encodeURIComponent(worker)}&limit=30`);
    if (!r.ok) throw 0;
    const js = await r.json();
    // Prefer runs_meta if available
    const meta = Array.isArray(js.runs_meta)
      ? js.runs_meta
      : (Array.isArray(js.runs) ? js.runs.map(id=>({id, started_at:'', finished_at:'', steps:null})) : []);
    return meta;
  },
  async replaySteps(worker, run_id, limit=500){
    const r = await fetch(`/workers/api/replay/steps?worker=${encodeURIComponent(worker)}&run_id=${encodeURIComponent(run_id)}&limit=${limit}`);
    if (!r.ok) throw 0;
    const js = await r.json();
    return (js && Array.isArray(js.steps)) ? js.steps : [];
  }
};

 

 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
