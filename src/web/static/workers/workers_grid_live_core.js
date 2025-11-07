
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

  // Import split modules (UMD globals)
  const Tools = global.WGLiveTools || {};
  const Helpers = global.WGLiveHelpers || {};
  // IMPORTANT: do NOT capture Prefill at module load (race). Always re-read from global.
  function _Prefill(){ return global.WGLivePrefill || {}; }

  // Re-export selected helpers for other live modules
  async function populateTools(card, list){
    try{
      dbg('populateTools IN', card?.getAttribute?.('data-worker'), list);
      const toolsRow = card && card.querySelector && card.querySelector('.tools');
      if (!toolsRow) { dbg('populateTools: toolsRow missing'); return; }

      // Clear existing chips first
      Array.from(toolsRow.querySelectorAll('.tool')).forEach(el=> el.remove());
      const names = Array.from(new Set((Array.isArray(list)? list : []).map(x=> String(x||'').trim()).filter(Boolean)));
      dbg('populateTools names', names);

      let idx = null;
      try{ idx = await Tools.ensureToolsIndex(); }catch{}

      // If registry not ready -> raw chips now + refine later
      if (!idx || idx.size===0){
        dbg('populateTools: tools idx not ready; render raw and schedule refine');
        for (const n of names){ addToolChip(toolsRow, n); }
        setTimeout(()=>{ try{ Tools.refineChipsAfterRegistry && Tools.refineChipsAfterRegistry(); }catch{} }, 1200);
        return;
      }

      // Registry is ready: resolve label/tooltip via resolveToolLabel (handles base/op and kind filter)
      for (const n of names){
        try{
          const res = await Tools.resolveToolLabel(n);
          const kind = String(res && res.kind || '').toLowerCase();
          if (kind && kind !== 'tool'){
            // Skip non-tools
            dbg('populateTools skip non-tool', n, res);
            continue;
          }
          const chip = document.createElement('div');
          chip.className = 'tool tooltip';
          chip.setAttribute('data-tool', n);
          const text = (res && res.text) || n;
          const tip  = (res && res.tip)  || '';
          chip.textContent = text;
          if (tip){ chip.setAttribute('data-tip', tip); }
          toolsRow.appendChild(chip);
          dbg('populateTools add chip', n, '=>', text);
        }catch(e){
          dbg('populateTools resolve error', e);
          addToolChip(toolsRow, n);
        }
      }
    }catch(e){ dbg('populateTools error', e); }
  }

  async function prefillToolsFromIdentity(wn){ const P=_Prefill(); return P.prefillToolsFromIdentity? P.prefillToolsFromIdentity(Core, wn) : []; }
  async function prefillToolsFromStatus(wn){ const P=_Prefill(); return P.prefillToolsFromStatus? P.prefillToolsFromStatus(wn) : []; }
  async function prefillToolsFromGraph(wn){ const P=_Prefill(); return P.prefillToolsFromGraph? P.prefillToolsFromGraph(wn) : []; }
  async function prefillToolsFromGraphMermaid(wn){ const P=_Prefill(); return P.prefillToolsFromGraphMermaid? P.prefillToolsFromGraphMermaid(Tools.ensureToolsIndex, wn) : []; }
  async function prefillToolsFromReplay(wn, limit=200){ const P=_Prefill(); return P.prefillToolsFromReplay? P.prefillToolsFromReplay(wn, limit) : []; }

  function addToolChip(toolsRow, name){
    try{
      if (!toolsRow || !name) return;
      const n = String(name).trim(); if (!n) return;
      if (toolsRow.querySelector(`.tool[data-tool="${CSS.escape(n)}"]`)) { dbg('tool chip exists', n); return; }
      const chip = document.createElement('div');
      chip.className = 'tool tooltip';
      chip.setAttribute('data-tool', n);
      chip.textContent = n;
      toolsRow.appendChild(chip);
      // Try to refine asynchronously if registry becomes available
      Tools.ensureToolsIndex().then(async idx=>{
        try{ const res = await Tools.resolveToolLabel(n); if (res.text) chip.textContent = res.text; if (res.tip) chip.setAttribute('data-tip', res.tip); dbg('chip refined', n, '->', res.text); }catch{}
      }).catch(()=>{});
      dbg('tool chip created', n);
    }catch(e){ dbg('addToolChip error', e); }
  }

  // Keep debug & chrono tick here for grid
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
    prefillToolsFromStatus,
    prefillToolsFromGraph,
    prefillToolsFromGraphMermaid,
    prefillToolsFromReplay,
    ensureChronoTick,
    // expose label helpers for live observe
    resolveToolLabel: Tools.resolveToolLabel,
    deriveToolName: Helpers.deriveToolName,
    isToolName: Tools.isToolName,
    refineChipsAfterRegistry: Tools.refineChipsAfterRegistry,
  };
})(window);
