






(function(global){
  const Core = global.WorkersGridCore || {};
  const LiveCore = {};

  // Debug bootstrap (visible logs; can force on via ?wgdebug=1 or WG_DEBUG=1)
  try{
    const qs = new URLSearchParams(location.search);
    const qdbg = qs.get('wgdebug') || qs.get('debug') || qs.get('workersdebug');
    const ldbg = localStorage.getItem('WG_DEBUG')||sessionStorage.getItem('WG_DEBUG');
    const on = (qdbg==='1') || (ldbg==='1');
    if (on) global.__WG_DEBUG = true;
    global.__WG_SET_DEBUG = (b)=>{ try{ global.__WG_DEBUG=!!b; localStorage.setItem('WG_DEBUG', b?'1':''); }catch{} };
  }catch{}
  function dbg(){ try{ console.log('[WG]', ...arguments); }catch{} }

  // Tools chips helpers
  function addToolChip(toolsRow, name){
    try{
      if (!toolsRow || !name) return;
      const n = String(name).trim(); if (!n) return;
      if (toolsRow.querySelector(`.tool[data-tool="${CSS.escape(n)}"]`)) { dbg('tool chip exists', n); return; }
      const chip = document.createElement('div');
      chip.className = 'tool';
      chip.setAttribute('data-tool', n);
      chip.textContent = n;
      toolsRow.appendChild(chip);
      dbg('tool chip created', n);
    }catch(e){ dbg('addToolChip error', e); }
  }
  function populateTools(card, list){
    try{
      const toolsRow = card && card.querySelector && card.querySelector('.tools');
      if (!toolsRow) { dbg('populateTools: toolsRow missing'); return; }
      Array.from(toolsRow.querySelectorAll('.tool')).forEach(el=> el.remove());
      const names = Array.from(new Set((Array.isArray(list)? list : []).map(x=> String(x||'').trim()).filter(Boolean)));
      dbg('populateTools with', names);
      names.forEach(n => addToolChip(toolsRow, n));
    }catch(e){ dbg('populateTools error', e); }
  }

  // Prefill from identity.tools
  async function prefillToolsFromIdentity(wn){
    try{
      const idj = await Core.apiIdentity(wn).catch(()=>null);
      const ident = idj && idj.identity || {};
      const tools = Array.isArray(ident.tools)? ident.tools : [];
      dbg('prefill(identity)', wn, tools);
      return tools;
    }catch(e){ dbg('prefill(identity) error', e); return []; }
  }

  // Prefill from graph JSON (mermaid:false)
  async function prefillToolsFromGraph(wn){
    try{
      const payload = {
        tool: 'py_orchestrator',
        params: {
          operation: 'graph',
          worker_name: wn,
          graph: { kind: 'process', include: { shapes:true, emojis:true, labels:true }, render: { mermaid:false } }
        }
      };
      const r = await fetch('/execute', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
      const js = await r.json().catch(()=>({}));
      const res = (js && js.result) ? js.result : js;
      const out = new Set();
      function visit(obj, depth){
        if (!obj || depth>4) return;
        if (Array.isArray(obj)) { obj.forEach(v=>visit(v, depth+1)); return; }
        if (typeof obj==='object'){
          for (const [k,v] of Object.entries(obj)){
            const kl = String(k||'').toLowerCase();
            if ((kl==='tool' || kl==='tool_name') && typeof v==='string'){
              const s = v.trim(); if (s) out.add(s);
            }
            if (typeof v==='object') visit(v, depth+1);
          }
        }
      }
      if (res && typeof res==='object'){
        if (Array.isArray(res.nodes)) visit(res.nodes, 1);
        if (Array.isArray(res.steps)) visit(res.steps, 1);
        visit(res, 0);
      }
      const arr = Array.from(out);
      dbg('prefill(graph)', wn, arr);
      return arr;
    }catch(e){ dbg('prefill(graph) error', e); return []; }
  }

  // Prefill from replay steps (io.in)
  async function prefillToolsFromReplay(wn, limit=200){
    try{
      const url = new URL('/workers/api/replay/steps', location.origin);
      url.searchParams.set('worker', wn);
      url.searchParams.set('limit', String(limit));
      const r = await fetch(url.toString());
      const js = await r.json().catch(()=>({}));
      const steps = Array.isArray(js?.steps) ? js.steps : [];
      const out = new Set();
      for (const st of steps){
        try{
          const call = st && st.io && st.io.in || {};
          const name = String(call.tool || call.tool_name || '').trim();
          if (name) out.add(name);
        }catch{}
      }
      const arr = Array.from(out);
      dbg('prefill(replay)', wn, arr);
      return arr;
    }catch(e){ dbg('prefill(replay) error', e); return []; }
  }

  // Chrono tick for running tools
  let CHRONO_TICK = null;
  function ensureChronoTick(){
    if (CHRONO_TICK) return;
    CHRONO_TICK = setInterval(() => {
      try{
        document.querySelectorAll('.card').forEach(card => {
          const startedIso = card.dataset.toolStarted || '';
          if (!startedIso) return;
          const started = Date.parse(startedIso);
          if (!Number.isFinite(started)) return;
          const elapsed = Math.max(0, Math.floor((Date.now() - started)/1000));
          const mm = Math.floor(elapsed/60), ss = String(elapsed%60).padStart(2,'0');
          const chrono = card.querySelector('.tools .tool.running .chrono');
          if (chrono) chrono.textContent = `${mm}:${ss}`;
        });
      }catch(e){ dbg('chrono tick error', e); }
    }, 500);
    dbg('chrono tick started');
  }

  global.WorkersGridLiveCore = {
    dbg,
    addToolChip,
    populateTools,
    prefillToolsFromIdentity,
    prefillToolsFromGraph,
    prefillToolsFromReplay,
    ensureChronoTick,
  };
})(window);

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
