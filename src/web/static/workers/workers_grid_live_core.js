




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

  // ===== Tools registry cache (/tools) + helpers =====
  let __toolsIdx = null, __toolsTs = 0;
  const TOOLS_TTL = 15*60*1000;

  async function ensureToolsIndex(){
    const now = Date.now();
    if (__toolsIdx && (now - __toolsTs) < TOOLS_TTL) { dbg('tools idx cache hit', __toolsIdx.size); return __toolsIdx; }
    try{
      const r = await fetch('/tools');
      const js = await r.json().catch(()=>({}));
      const arr = Array.isArray(js?.tools) ? js.tools : [];
      const idx = new Map();
      for (const t of arr){
        const key = String(t.name||'').trim().toLowerCase();
        if (!key) continue;
        const label = String(t.display_name || t.title || t.name || key).trim();
        const desc  = String(t.description || '').trim();
        idx.set(key, { label, desc });
      }
      __toolsIdx = idx; __toolsTs = now;
      dbg('tools index loaded', idx.size);
    }catch(e){ dbg('tools index error', e); __toolsIdx = new Map(); __toolsTs = now; }
    return __toolsIdx;
  }

  function resolveToolLabelSync(raw, idx){
    try{
      const s = String(raw||'').trim(); if (!s) return { text:'', tip:'' };
      const [base, op] = s.split(':', 2);
      const rec = idx && idx.get(String(base||'').toLowerCase());
      if (!rec) return { text: s, tip: '' };
      const text = op ? `${rec.label}` : rec.label;
      const tip  = op ? `${rec.desc||''}${rec.desc?'\n':''}operation: ${op}` : (rec.desc||'');
      return { text, tip };
    }catch{ return { text:String(raw||''), tip:'' }; }
  }

  async function resolveToolLabel(raw){
    const idx = await ensureToolsIndex();
    const res = resolveToolLabelSync(raw, idx);
    dbg('resolveToolLabel', raw, '=>', res.text);
    return res;
  }

  // Normalisation du nom de tool à partir d'un call
  function deriveToolName(call){
    try{
      if (!call || typeof call !== 'object') return '';
      const t  = String(call.tool || call.tool_name || '').trim();
      const op = String(call.operation || '').trim();
      const name = (t && op) ? `${t}:${op}` : (t || (op ? `py_orchestrator:${op}` : ''));
      dbg('deriveToolName', {t, op, name});
      return name;
    }catch{ return ''; }
  }

  // Tools chips helpers
  function addToolChip(toolsRow, name){
    try{
      if (!toolsRow || !name) return;
      const n = String(name).trim(); if (!n) return;
      if (toolsRow.querySelector(`.tool[data-tool="${CSS.escape(n)}"]`)) { dbg('tool chip exists', n); return; }
      const chip = document.createElement('div');
      chip.className = 'tool tooltip';
      chip.setAttribute('data-tool', n);
      // Temporary text until we resolve labels
      chip.textContent = n;
      toolsRow.appendChild(chip);
      // Async resolve displayName + tooltip (non bloquant)
      ensureToolsIndex().then(idx=>{
        try{ const res = resolveToolLabelSync(n, idx); if (res.text) chip.textContent = res.text; if (res.tip) chip.setAttribute('data-tip', res.tip); dbg('chip resolved', n, '->', res.text); }catch{}
      }).catch(()=>{});
      dbg('tool chip created', n);
    }catch(e){ dbg('addToolChip error', e); }
  }

  async function populateTools(card, list){
    try{
      dbg('populateTools IN', card?.getAttribute?.('data-worker'), list);
      const toolsRow = card && card.querySelector && card.querySelector('.tools');
      if (!toolsRow) { dbg('populateTools: toolsRow missing'); return; }
      Array.from(toolsRow.querySelectorAll('.tool')).forEach(el=> el.remove());
      const names = Array.from(new Set((Array.isArray(list)? list : []).map(x=> String(x||'').trim()).filter(Boolean)));
      dbg('populateTools names', names);
      // Load tools index once (non fatal if fails)
      const idx = await ensureToolsIndex().catch(()=>null);
      dbg('populateTools idx', idx && idx.size);
      for (const n of names){
        const chip = document.createElement('div');
        chip.className = 'tool tooltip';
        chip.setAttribute('data-tool', n);
        if (idx){
          const { text, tip } = resolveToolLabelSync(n, idx);
          chip.textContent = text || n;
          if (tip) chip.setAttribute('data-tip', tip);
        } else {
          chip.textContent = n;
        }
        toolsRow.appendChild(chip);
        dbg('populateTools add chip', n, '=>', chip.textContent);
      }
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
      let scanned = 0;
      function visit(obj, depth){
        if (!obj || depth>6) return;
        if (Array.isArray(obj)) { obj.forEach(v=>visit(v, depth+1)); return; }
        if (typeof obj==='object'){
          scanned++;
          try{
            const t  = String(obj.tool || obj.tool_name || '').trim();
            const op = String(obj.operation || '').trim();
            if (t || op){
              const name = (t && op) ? `${t}:${op}` : (t || (op ? `py_orchestrator:${op}` : ''));
              if (name) out.add(name);
            }
          }catch{}
          for (const v of Object.values(obj)){ if (v && typeof v==='object') visit(v, depth+1); }
        }
      }
      if (res && typeof res==='object'){
        if (Array.isArray(res.nodes)) visit(res.nodes, 1);
        if (Array.isArray(res.steps)) visit(res.steps, 1);
        visit(res, 0);
      }
      const arr = Array.from(out);
      dbg('prefill(graph)', wn, arr, 'scanned=', scanned);
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
      let countCalls = 0;
      for (const st of steps){
        try{
          const call = st && st.io && st.io.in || {};
          const name = deriveToolName(call);
          if (name) out.add(name);
          countCalls++;
        }catch{}
      }
      const arr = Array.from(out);
      dbg('prefill(replay)', wn, arr, 'calls=', countCalls, 'steps=', steps.length);
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
    // helpers
    addToolChip,
    populateTools,
    prefillToolsFromIdentity,
    prefillToolsFromGraph,
    prefillToolsFromReplay,
    ensureChronoTick,
    // expose label helpers for live observe
    resolveToolLabel,
    deriveToolName,
  };
})(window);

 
 
 
 
 
 
 
 
 
 
 
 
