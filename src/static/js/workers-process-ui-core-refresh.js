
// Workers Process UI Core - refresh orchestration (mermaid ensure, replay init, side panel)
(function(){
  var MERMAID_CACHE = '';

  async function ensureMermaid(){
    if (WP.mermaidReady && window.mermaid) return;
    var existing = document.querySelector('script[data-mermaid]');
    if (!existing){
      var s = document.createElement('script');
      s.src = 'https://unpkg.com/mermaid@10/dist/mermaid.min.js';
      s.async = true; s.defer = true; s.setAttribute('data-mermaid','1');
      document.head.appendChild(s);
    }
    var tries = 0;
    (function initWhenReady(){
      tries++;
      if (window.mermaid && typeof window.mermaid.initialize === 'function'){
        try{
          var seed = 'process-' + (window.WP?.processWorkerId || 'default');
          window.mermaid.initialize({
            startOnLoad:false,
            theme:'neutral',
            securityLevel:'loose',
            deterministicIds:true,
            deterministicIDSeed: seed,
            flowchart: {
              defaultRenderer: 'elk',
              curve: 'linear',
              nodeSpacing: 90,
              rankSpacing: 140,
              diagramPadding: 16,
              useMaxWidth: true,
              elk: {
                'elk.direction': 'DOWN',
                'spacing.nodeNodeBetweenLayers': 140
              }
            }
          });
          WP.mermaidReady = true;
          return;
        }catch(_){ }
      }
      if (tries < 50) setTimeout(initWhenReady, 100);
    })();
  }

  function pickLatestCompleted(history){
    if (!Array.isArray(history) || history.length===0) return null;
    for (var i=0;i<history.length;i++){ if (String(history[i].status||'').toLowerCase()==='succeeded') return history[i]; }
    for (var j=0;j<history.length;j++){ if (String(history[j].status||'').toLowerCase()==='failed') return history[j]; }
    return history[0];
  }

  // Helper: remap current replayIx onto new meta after a refresh, preserving progress
  function remapReplayIxPreserveProgress(oldMeta, newMeta, curIx){
    try{
      if (!Array.isArray(oldMeta) || !Array.isArray(newMeta)) return Math.max(0, Math.min(curIx||0, (newMeta.length||1)-1));
      var cur = oldMeta[curIx];
      if (!cur) return Math.max(0, Math.min(curIx||0, (newMeta.length||1)-1));
      // Priority 1: id exact
      var ix = newMeta.findIndex(function(m){ return String(m?.id||'') === String(cur.id||''); });
      if (ix >= 0) return ix;
      // Priority 2: ts_ms exact
      ix = newMeta.findIndex(function(m){ return Number(m?.ts_ms||0) === Number(cur.ts_ms||0); });
      if (ix >= 0) return ix;
      // Priority 3: node + ts_precise
      ix = newMeta.findIndex(function(m){ return String(m?.node||'')===String(cur.node||'') && String(m?.ts_precise||'')===String(cur.ts_precise||''); });
      if (ix >= 0) return ix;
      // Fallback: clamp to bounds
      return Math.max(0, Math.min(curIx||0, (newMeta.length||1)-1));
    }catch(_){ return Math.max(0, Math.min(curIx||0, (newMeta.length||1)-1)); }
  }

  function computeRetryDelays(history){
    try{
      const rows = Array.isArray(history) ? history.slice().reverse() : []; // ascending by time
      const map = {}; // key: corePrev|coreCurr => label like '15s'
      function coreName(name){ return String(name||'').trim(); }
      for (let i=1;i<rows.length;i++){
        const prev = rows[i-1], curr = rows[i];
        const a = coreName(prev.node||'');
        const b = coreName(curr.node||'');
        // Only record retries from explicit sleep/retry nodes to next node
        if (/sleep|retry/i.test(a)){
          const dt = Math.max(0, Number(curr.ts_ms||0) - Number(prev.ts_ms||0));
          let label = dt >= 1000 ? Math.round(dt/1000)+'s' : dt+'ms';
          map[a+'|'+b] = label;
        }
      }
      return map;
    }catch(_){ return {}; }
  }

  function annotateRetryDelaysOnEdges(){
    try{
      const svg = document.querySelector('#processGraph svg');
      if (!svg) return;
      const map = WP.retryDelaysMap || {};
      const keys = Object.keys(map);
      if (!keys.length) return;
      keys.forEach(k => {
        const label = map[k];
        // k is "A|B" with core names; we use our enrichment classes df-e-<san(A)>__<san(B)>
        try{
          const core = k.split('|');
          const aSan = (window.RenderUtils?.sanitizeId(core[0])||core[0]).toLowerCase();
          const bSan = (window.RenderUtils?.sanitizeId(core[1])||core[1]).toLowerCase();
          const cls = `df-e-${aSan}__${bSan}`;
          const paths = svg.querySelectorAll(`path.${cls}`);
          paths.forEach(p => {
            // Find or create an edgeLabel near this path's group
            const group = p.closest('g.edgePath, g.edgePaths');
            if (!group) return;
            // Try to find existing edgeLabel sibling
            let lab = group.querySelector('g.edgeLabel text');
            if (!lab){
              // Create a simple label box
              const wrap = document.createElementNS('http://www.w3.org/2000/svg', 'g');
              wrap.setAttribute('class', 'edgeLabel');
              const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
              t.setAttribute('text-anchor','middle');
              t.setAttribute('style','font-size:10px; fill:#065f46;');
              wrap.appendChild(t);
              group.appendChild(wrap);
              lab = t;
            }
            lab.textContent = label; // show delay like '15s'
          });
        }catch(_){ }
      });
    }catch(_){ }
  }

  async function refreshProcessView(){
    var graphEl = document.getElementById('processGraph');
    var sideEl = document.getElementById('processSide');
    if (!graphEl || !sideEl) return;
    const rangeKey = 'all';
    try {
      MERMAID_CACHE = await WPData.fetchMermaid();
      window.MERMAID_CACHE = MERMAID_CACHE;

      var current = await WPData.fetchCurrentState();
      var historyOpen = await WPData.fetchHistory(rangeKey);

      // Expose retry delays map for edge annotation after render
      try{ WP.retryDelaysMap = computeRetryDelays(historyOpen); }catch(_){ WP.retryDelaysMap = {}; }

      // Build new replay sequence/meta from DB
      var replayData = await buildReplaySequence(rangeKey);
      var newNodes = replayData.nodes || [];
      var newMeta  = replayData.meta  || [];

      // Detect if we are in the middle of a replay (busy) => do NOT reset progress
      var replayBusy = !!(WP.replayActive && WP.atTail===false);
      var userLocked = !!(window.WPCoreUtils && typeof WPCoreUtils.isUserLocked==='function' && WPCoreUtils.isUserLocked());

      // Replace sequences
      var oldMeta = WP.replayMeta || [];
      WP.replaySeq = newNodes;
      WP.replayMeta = newMeta;

      // If busy, remap current index to new meta to preserve progress
      if (replayBusy){
        var curIx = typeof WP.replayIx==='number' ? WP.replayIx : 0;
        var mapped = remapReplayIxPreserveProgress(oldMeta, newMeta, curIx);
        WP.replayIx = mapped;
      }

      var latestCompleted = pickLatestCompleted(historyOpen);
      var newestNode = historyOpen && historyOpen.length ? (historyOpen[0].node||'') : '';

      var openNode = '';
      var followingTail = (WP.atTail === true);

      // If replay is running and not at tail, do not auto-follow tail
      if (replayBusy){ followingTail = false; }

      if (userLocked && WP.currentNodeSelected){
        openNode = WP.currentNodeSelected;
      } else if (followingTail) {
        openNode = newestNode || (latestCompleted? latestCompleted.node: '');
      } else if (current && current.node){
        openNode = current.node;
      } else if (WP.currentNodeSelected){
        openNode = WP.currentNodeSelected;
      }
      if (!userLocked) WP.currentNodeSelected = String(openNode||'');

      try {
        const seq = Array.isArray(WP.replaySeq) ? WP.replaySeq : [];
        const maxIx = Math.max(0, seq.length - 1);
        if (!seq.length) {
          if (!userLocked) WP.hlTrail = openNode ? [openNode] : [];
        } else {
          if (!replayBusy && !userLocked){
            // Recompute highlight trail relative to openNode when not busy and not user-locked
            let ix = maxIx;
            if (openNode){ const k = seq.lastIndexOf(String(openNode)); if (k >= 0) ix = k; }
            const cur = seq[ix] || '';
            const p1 = seq[ix-1] || '';
            const p2 = seq[ix-2] || '';
            WP.hlTrail = [cur, p1, p2].filter(Boolean);
          } else if (replayBusy) {
            // Busy: trail from current replayIx (do not disturb progression)
            const ix = Math.max(0, Math.min(WP.replayIx||0, maxIx));
            const cur = seq[ix] || '';
            const p1 = seq[ix-1] || '';
            const p2 = seq[ix-2] || '';
            WP.hlTrail = [cur, p1, p2].filter(Boolean);
          } // if userLocked and not busy: keep WP.hlTrail as-is
        }
      } catch(_){ }

      // Render graph or just update inline depending on lock/busy
      if (MERMAID_CACHE){
        if (replayBusy || userLocked){
          try{ window.tryGraphInlineHighlight?.(WP.hlTrail); }catch(_){ }
          try{ annotateRetryDelaysOnEdges(); }catch(_){ }
        } else {
          await window.DFMermaid.renderMermaid(graphEl, MERMAID_CACHE, WP.currentNodeSelected);
          try{ annotateRetryDelaysOnEdges(); }catch(_){ }
        }
      } else {
        graphEl.innerHTML = '<p style="padding:10px;">Graph non disponible</p>';
      }

      // Side panel (timeline) always refresh (lightweight)
      await updateProcessSide(rangeKey, current.args, historyOpen);
      if (WP.currentNodeSelected){ highlightTimelineNode(WP.currentNodeSelected, /*smooth=*/false); }

      // Manage replay progression
      var prevLen = Number(WP.prevReplayLen||0);
      var newLen = Array.isArray(WP.replaySeq) ? WP.replaySeq.length : 0;
      var maxIx = Math.max(0, newLen - 1);

      if (replayBusy){
        WP.replayIx = Math.max(0, Math.min(WP.replayIx||0, maxIx));
        if (typeof window.wpReplayRenderCurrent === 'function') window.wpReplayRenderCurrent();
      } else if (followingTail) {
        if (!WP._initDone) {
          WP.replayIx = maxIx;
          if (!WP.replayActive && typeof window.wpReplayStart === 'function') window.wpReplayStart();
          WP.prevReplayLen = newLen;
          WP.atTail = true;
          WP._initDone = true;
        } else if (newLen > prevLen) {
          var startIx = Math.max(0, Math.min(prevLen, maxIx));
          WP.replayIx = startIx;
          if (!WP.replayActive && typeof window.wpReplayStart === 'function') window.wpReplayStart();
          WP.atTail = true;
          WP.prevReplayLen = newLen;
        } else {
          WP.replayIx = maxIx;
          if (!WP.replayActive && typeof window.wpReplayStart === 'function') window.wpReplayStart();
          WP.atTail = true;
          WP.prevReplayLen = newLen;
        }
      } else {
        WP.replayIx = Math.max(0, Math.min(WP.replayIx || 0, maxIx));
        if (!WP.replayActive && WP.replayIx < maxIx && typeof window.wpReplayStart === 'function') window.wpReplayStart();
        else if (typeof window.wpReplayRenderCurrent === 'function') window.wpReplayRenderCurrent();
      }

    } catch (e) {
      console.error('[Mermaid] render error:', e);
      graphEl.innerHTML = '<p style="padding:10px;color:var(--danger);">Erreur Mermaid: '+escapeHtml(e.message||e)+'</p>';
    }
  }

  window.ensureMermaid = ensureMermaid;
  window.refreshProcessView = refreshProcessView;
  window.pickLatestCompleted = pickLatestCompleted;
})();
