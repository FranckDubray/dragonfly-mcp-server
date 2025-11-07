
(function(global){
  const { dbg, deriveToolName, collectNamesFromAny, containsWordish } = global.WGLiveHelpers || {};

  async function prefillToolsFromCode(Core, wn){
    try{
      const url = new URL('/workers/api/tools_from_code', location.origin);
      url.searchParams.set('worker', wn);
      const r = await fetch(url.toString());
      const js = await r.json().catch(()=>({}));
      const items = Array.isArray(js?.tools) ? js.tools : [];
      const names = items.map(t => String(t && t.name || '').trim()).filter(Boolean);
      dbg && dbg('prefill(code)', wn, names);
      return names;
    }catch(e){ dbg && dbg('prefill(code) error', e); return []; }
  }

  async function prefillToolsFromIdentity(Core, wn){
    try{
      const idj = await Core.apiIdentity(wn).catch(()=>null);
      const ident = idj && idj.identity || {};
      const tools = Array.isArray(ident.tools)? ident.tools : [];
      dbg && dbg('prefill(identity)', wn, tools);
      return tools;
    }catch(e){ dbg && dbg('prefill(identity) error', e); return []; }
  }

  async function prefillToolsFromStatus(wn){
    try{
      const payload = { tool:'py_orchestrator', params:{ operation:'status', worker_name: wn, include_metrics: true } };
      const r = await fetch('/execute', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
      const js = await r.json().catch(()=>({}));
      const res = js && (js.result || js) || {};
      const steps = Array.isArray(res.recent_steps) ? res.recent_steps : [];
      const out = new Set();
      steps.forEach(st=>{
        try{
          const call = st && st.io && st.io.in || null;
          const n1 = deriveToolName && deriveToolName(call); if (n1) out.add(n1);
          let dj = st && st.details_json; if (typeof dj === 'string'){ try{ dj = JSON.parse(dj); }catch{ dj=null; } }
          if (dj && typeof dj==='object') collectNamesFromAny && collectNamesFromAny(dj, out);
          collectNamesFromAny && collectNamesFromAny(st, out);
        }catch{}
      });
      const arr = Array.from(out).filter(Boolean);
      dbg && dbg('prefill(status)', wn, arr);
      return arr;
    }catch(e){ dbg && dbg('prefill(status) error', e); return []; }
  }

  async function prefillToolsFromReplay(wn, limit=200){
    try{
      const url = new URL('/workers/api/replay/steps', location.origin);
      url.searchParams.set('worker', wn);
      url.searchParams.set('limit', String(limit));
      const r = await fetch(url.toString());
      const js = await r.json().catch(()=>({}));
      const steps = Array.isArray(js?.steps) ? js.steps : [];
      const out = new Set();
      steps.forEach(st => {
        try{
          const call = st && st.io && st.io.in || {};
          const name = deriveToolName && deriveToolName(call);
          if (name) out.add(name);
        }catch{}
      });
      const arr = Array.from(out);
      dbg && dbg('prefill(replay)', wn, arr, 'steps=', steps.length);
      return arr;
    }catch(e){ dbg && dbg('prefill(replay) error', e); return []; }
  }

  // Graph-based prefill removed on purpose: do not use graphs to identify tools.

  global.WGLivePrefill = { prefillToolsFromCode, prefillToolsFromIdentity, prefillToolsFromStatus, prefillToolsFromReplay };
})(window);
