













(function(global){
  // Loader that composes core, card, live modules with cache-busting
  async function buildWorkersGrid(root, selectedLeader){
    try{
      const bust = `v=${Date.now()}`;
      await import(`./workers_grid_core.js?${bust}`);
      await import(`./workers_grid_card.js?${bust}`);
      // Load helpers and tools registry BEFORE core live uses them
      try{ await import(`./workers_grid_live_helpers.js?${bust}`); }catch(e){ /* best-effort */ }
      try{ await import(`./workers_grid_live_tools.js?${bust}`); }catch(e){ /* best-effort */ }
      // Ensure prefill is available BEFORE live_core grabs the global
      try{ await import(`./workers_grid_live_prefill.js?${bust}`); }catch(e){ /* best-effort */ }
      // Load split live modules (core/observe/boot)
      await import(`./workers_grid_live_core.js?${bust}`);
      await import(`./workers_grid_live_observe.js?${bust}`);
      await import(`./workers_grid_live_boot.js?${bust}`);
    }catch(e){
      try{ console.error('[WG] dynamic import error', e); }catch{}
      // Fallback without busting
      await import('./workers_grid_core.js');
      await import('./workers_grid_card.js');
      try{ await import('./workers_grid_live_helpers.js'); }catch{}
      try{ await import('./workers_grid_live_tools.js'); }catch{}
      try{ await import('./workers_grid_live_prefill.js'); }catch{}
      await import('./workers_grid_live_core.js');
      await import('./workers_grid_live_observe.js');
      await import('./workers_grid_live_boot.js');
    }
    // Delegate to live builder
    if (global.WorkersGridLive && typeof global.WorkersGridLive.buildWorkersGrid === 'function'){
      try{ console.log('[WG] buildWorkersGrid call'); }catch{}
      return global.WorkersGridLive.buildWorkersGrid(root, selectedLeader);
    }
    try{ console.error('[WG] WorkersGridLive.buildWorkersGrid not found'); }catch{}
    return null;
  }
  global.WorkersGrid = { buildWorkersGrid };
})(window);
