
(function(global){
  const Core = global.WorkersGridCore || {};
  const LiveCore = global.WorkersGridLiveCore || {};
  const Observe = global.WorkersGridLiveObserve || {};
  const { h } = Core;

  async function _loadPrefill(){
    try{
      const mod = await import('./workers_grid_live_prefill.js?v=' + Date.now());
      return global.WGLivePrefill || mod.WGLivePrefill || null;
    }catch(e){ LiveCore.dbg('prefill module load error', e); return null; }
  }

  async function _forceRefineOnce(){
    try{
      const Tools = global.WGLiveTools || {};
      const idx = await Tools.ensureToolsIndex();
      if (idx && idx.size){
        LiveCore.refineChipsAfterRegistry && LiveCore.refineChipsAfterRegistry();
        LiveCore.dbg('refineChipsAfterRegistry: forced pass');
      }
    }catch(e){ LiveCore.dbg('refine once error', e); }
  }

  async function buildWorkersGrid(root, selectedLeader){
    const [list] = await Promise.all([ Core.apiList() ]);
    let workers = Core.sanitizeWorkers(list);
    LiveCore.dbg('workers list', workers.length);
    if (selectedLeader && String(selectedLeader).trim()){
      const target = String(selectedLeader).trim();
      workers = workers.filter(w => (String(w?.leader||'').trim() || String((w?.identity||{}).leader||'').trim()) === target);
      LiveCore.dbg('filtered by leader', target, workers.length);
    }

    const grid = h('section',{class:'cards','aria-label':'Workers'}); root.appendChild(grid);
    if (!workers.length){ const msg = h('div',{class:'panel', style:'margin-top:8px;color:#6b7280;font-size:14px'}, 'Aucun worker pour l’instant'); root.appendChild(msg); }

    const known = new Set(workers.map(w=> w.worker_name));
    const inflight = new Set();

    workers.forEach(async (w)=>{
      const display_name = (w.identity||{}).display_name || Core.firstFromSlug(w.worker_name);
      const rec = { worker_name: w.worker_name, display_name, avatar_url: (w.identity||{}).avatar_url || '', phase: w.status || 'unknown', leader: (String(w?.leader||'').trim() || String((w?.identity||{}).leader||'').trim()) };
      const card = global.WorkersGridCard.buildCard(rec);
      grid.appendChild(card);
      try{ Core.setAvatarAura(card, { phase: String(rec.phase||'').toLowerCase(), running_kind:'', sleeping:false }); }catch{}

      const PF = await _loadPrefill();
      if (!PF || !PF.prefillToolsFromCode){ LiveCore.dbg('prefill API missing'); return; }
      try{
        const fromCode = await PF.prefillToolsFromCode(Core, w.worker_name);
        if (fromCode && fromCode.length){
          LiveCore.populateTools(card, fromCode);
        } else {
          LiveCore.dbg('no tools_from_code', w.worker_name);
        }
      }catch(e){ LiveCore.dbg('prefill fromCode error', e); }
    });

    async function ensureCard(wn){
      if (known.has(wn) || inflight.has(wn)) return; inflight.add(wn); LiveCore.dbg('ensureCard start', wn);
      try{
        const [idj, stj] = await Promise.all([ Core.apiIdentity(wn).catch(()=>({})), Core.apiStatusMCP(wn).catch(()=>({})) ]);
        const ident = idj?.identity || {};
        const rec = { worker_name: wn, display_name: ident.display_name || Core.firstFromSlug(wn), avatar_url: ident.avatar_url || '', phase: (stj?.phase || stj?.status || 'unknown'), leader: (ident.leader || '') };
        const card = global.WorkersGridCard.buildCard(rec); grid.appendChild(card); known.add(wn);
        try{ Core.setAvatarAura(card, { phase: String(rec.phase||'').toLowerCase(), running_kind:'', sleeping:false }); }catch{}
        try{
          const PF = await _loadPrefill();
          if (PF && PF.prefillToolsFromCode){
            const fromCode = await PF.prefillToolsFromCode(Core, wn);
            if (fromCode && fromCode.length){
              LiveCore.populateTools(card, fromCode);
            }
          }
        }catch(e){ LiveCore.dbg('ensureCard populate error', e); }
      }catch(e){ LiveCore.dbg('ensureCard error', wn, e); }
      finally{ inflight.delete(wn); }
    }

    try{
      const { startObserveMany } = await import('./observe_many_client.js');
      const stopObserve = startObserveMany(async (ev, helpers)=>{
        try{
          const wn=ev?.worker_name||''; if(!wn) return;
          if (!known.has(wn)) await ensureCard(wn);
          const card=document.querySelector(`.card[data-worker="${CSS.escape(wn)}"]`); if(!card) return;
          await Observe.applyEvent(card, wn, ev, helpers);
        }catch(e){ LiveCore.dbg('observe event error', e); }
      });
      global.__OBS_MANY_STOP__ = stopObserve;
      LiveCore.dbg('observe_many started');
    }catch(e){ LiveCore.dbg('observe_many init error', e); }

    // Force a refine pass once the registry is ready (labels + tooltips)
    _forceRefineOnce();

    return {grid};
  }

  global.WorkersGridLive = { buildWorkersGrid };
})(window);
