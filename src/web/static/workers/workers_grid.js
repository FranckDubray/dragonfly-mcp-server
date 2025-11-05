









(function(global){
  // Loader that composes core, card, live modules with cache-busting
  async function buildWorkersGrid(root, selectedLeader){
    try{
      const bust = `v=${Date.now()}`;
      await import(`./workers_grid_core.js?${bust}`);
      await import(`./workers_grid_card.js?${bust}`);
      await import(`./workers_grid_live.js?${bust}`);
    }catch(e){
      try{ console.error('[WG] dynamic import error', e); }catch{}
      // Fallback without busting
      await import('./workers_grid_core.js');
      await import('./workers_grid_card.js');
      await import('./workers_grid_live.js');
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

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
