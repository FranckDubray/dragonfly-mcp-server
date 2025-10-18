

// Workers Process - Overlay Events (bindings + scroll persistence + click handling)
(function(){
  function bindControls(el){
    var q = function(id, fn){ var b = el.querySelector(id); if (!b) return; b.addEventListener('click', function(){ if (typeof window[fn] === 'function') window[fn](); }); };
    q('#btnRw', 'wpReplayRewind');
    q('#btnStepBack', 'wpReplayStepBack');
    // Toggle Play/Stop behavior for #btnStop
    var btnStop = el.querySelector('#btnStop');
    if (btnStop) {
      btnStop.addEventListener('click', function(){
        if (WP.replayActive) {
          if (typeof window.wpReplayPause === 'function') wpReplayPause();
        } else {
          if (typeof window.wpReplayStart === 'function') wpReplayStart();
        }
        try { updatePlayStopButton(el); } catch(_){ }
      });
    }
    q('#btnStepFwd', 'wpReplayStepForward');
    q('#btnFf', 'wpReplayForwardEnd');
    var btnClose = el.querySelector('#btnCloseProcess'); if (btnClose) btnClose.addEventListener('click', closeProcess);
  }

  function applyClickHandler(el){
    el.addEventListener('click', async function(e){
      var it = e.target.closest('.tl-item');
      if (!it) return;
      var stepId = it.getAttribute('data-id');
      var node = it.getAttribute('data-node') || '';
      var stepTs = it.getAttribute('data-ts') || '';
      var stepMs = it.getAttribute('data-ts-ms') || '';
      console.info('[CLICK] timeline item', { stepId, node, stepTs, stepMs });

      function _sanitize(s){ return String(s||'').replace(/[^A-Za-z0-9_]/g,''); }
      function resolveReplayIndex(nodeLabel, stepId, stepTs, stepMs){
        try{
          const nodes = Array.isArray(WP.replaySeq) ? WP.replaySeq : [];
          const meta  = Array.isArray(WP.replayMeta) ? WP.replayMeta : [];
          // 1) id exact
          if (stepId && meta.length){
            const wanted = String(stepId);
            const ixById = meta.findIndex(m => String(m?.id) === wanted);
            if (ixById >= 0) return ixById;
          }
          // 2) ts_ms exact
          if (stepMs && meta.length){
            const tms = Number(stepMs)||0;
            const ixByMs = meta.findIndex(m => Number(m?.ts_ms||0) === tms);
            if (ixByMs >= 0) return ixByMs;
          }
          // 3) node + ts_precise
          if (meta.length && nodeLabel && stepTs){
            const ixByNodeTs = meta.findIndex(m => String(m?.node||'')===String(nodeLabel) && String(m?.ts_precise||'')===String(stepTs));
            if (ixByNodeTs >= 0) return ixByNodeTs;
          }
          // 4) ts precise seul
          if (meta.length && stepTs){
            const ixByTs = meta.findIndex(m => String(m?.ts_precise||'')===String(stepTs));
            if (ixByTs >= 0) return ixByTs;
          }
          // 5) label heuristiques
          if (nodes.length && nodeLabel){
            const ixByLabel = nodes.lastIndexOf(String(nodeLabel));
            if (ixByLabel >= 0) return ixByLabel;
            const needle = _sanitize(nodeLabel);
            if (needle){
              for (let i = nodes.length-1; i>=0; i--){ if (_sanitize(nodes[i]) === needle) return i; }
            }
          }
        }catch(_){ }
        return Math.max(0, (Array.isArray(WP.replaySeq) ? WP.replaySeq.length-1 : 0));
      }

      const wasPlaying = !!WP.replayActive;
      var lastIx = Math.max(0, (Array.isArray(WP.replaySeq)? WP.replaySeq.length-1 : 0));
      WP.replayIx = resolveReplayIndex(node, stepId, stepTs, stepMs);
      WP.atTail = (WP.replayIx >= lastIx);

      // Force a full render on selection to ensure SVG exists and sizing is correct
      try{
        var src = window.MERMAID_CACHE || window.__MERMAID_CACHE__ || '';
        if (!src && typeof WPData?.fetchMermaid === 'function'){ src = await WPData.fetchMermaid(); window.MERMAID_CACHE = src; }
        if (src && window.DFMermaid){ await DFMermaid.renderMermaid(document.getElementById('processGraph'), src, node||''); }
      }catch(_){ }

      // Recompute trail (head + (trailN-1) mids) and inline highlight
      try{
        const n = Math.max(1, Math.min(10, (WP.trailN||3)));
        const lits = Math.max(1, n - 1);
        const seq = Array.isArray(WP.replaySeq) ? WP.replaySeq : [];
        const out = [];
        out.push(seq[WP.replayIx] || node || '');
        for (let k=1;k<=(lits-1);k++){ const v = seq[WP.replayIx - k]; if (v) out.push(v); }
        WP.hlTrail = out;
        window.tryGraphInlineHighlight?.(WP.hlTrail);
      }catch(_){ }

      // Highlight timeline and details
      try{
        if (typeof highlightTimelineById === 'function' && stepId){
          highlightTimelineById(String(stepId), /*smooth=*/true);
        } else if (typeof highlightTimelineNode === 'function') {
          highlightTimelineNode(String(node||''), /*smooth=*/true);
        }
      }catch(_){ }

      if (stepId) try{ await loadAndShowStepDetails(WP.processWorkerId, stepId); }catch(_){ }

      if (wasPlaying && !WP.replayActive && typeof window.wpReplayStart === 'function') {
        wpReplayStart();
      }
    });
  }

  function persistScrollStart(){
    var box = document.getElementById('timelineBox');
    if (!box) return 0; return box.scrollTop || 0;
  }
  function persistScrollRestore(pos){
    try{
      var box = document.getElementById('timelineBox');
      if (!box) return; box.scrollTop = pos;
    }catch(_){ }
  }

  function updatePlayStopButton(el){
    try{
      const btn = el.querySelector('#btnStop');
      if (!btn) return;
      if (WP.replayActive) {
        btn.textContent = '\u23f9'; // Stop
        btn.title = 'Stop';
      } else {
        btn.textContent = '\u25b6\ufe0f'; // Play
        btn.title = 'Play';
      }
    }catch(_){ }
  }

  async function openProcess(workerId){
    WP.processWorkerId = String(workerId||'');
    var overlay = window.__WPOverlay?.ensureProcessOverlay?.();
    try{
      overlay.classList.add('open');
      document.documentElement.style.overflow = 'hidden';
      document.body.style.overflow = 'hidden';
    }catch(_){ }

    if (typeof window.ensureMermaid === 'function') { await window.ensureMermaid(); }

    // Force a render on every open to guarantee SVG and correct sizing
    try{
      var src = window.MERMAID_CACHE || window.__MERMAID_CACHE__ || '';
      if (!src && typeof WPData?.fetchMermaid === 'function'){ src = await WPData.fetchMermaid(); window.MERMAID_CACHE = src; }
      if (src && window.DFMermaid){ await DFMermaid.renderMermaid(document.getElementById('processGraph'), src, WP.currentNodeSelected||''); }
    }catch(_){ }

    // Then normal refresh
    var st = persistScrollStart();
    if (typeof window.refreshProcessView === 'function') { await window.refreshProcessView(); }
    persistScrollRestore(st);

    // Keep autoplay armed by default (if inactive)
    try{ if (!WP.replayActive && typeof window.wpReplayStart === 'function') window.wpReplayStart(); }catch(_){ }

    clearInterval(WP.processRefreshTimer);
    WP.processRefreshTimer = setInterval(async function(){
      var open = document.getElementById('processOverlay')?.classList.contains('open');
      if (!open){ clearInterval(WP.processRefreshTimer); return; }
      var st = persistScrollStart();
      if (typeof window.refreshProcessView === 'function') { await window.refreshProcessView(); }
      persistScrollRestore(st);
    }, 10000);

    // Bindings
    bindControls(overlay);
    applyClickHandler(overlay);
    updatePlayStopButton(overlay);

    // Bind trail range
    try{ window.__WPOverlay?.bindTrailRange?.(); }catch(_){ }
  }

  function closeProcess(){
    clearInterval(WP.processRefreshTimer); WP.processRefreshTimer=null;
    try{ if (typeof window.wpReplayPause === 'function') wpReplayPause(); }catch(_){ }
    try{ if (typeof window.clearReplayTimer === 'function') clearReplayTimer(); }catch(_){ }
    var el = document.getElementById('processOverlay'); if (el) {
      el.classList.remove('open');
    }
    try{ document.documentElement.style.overflow = ''; document.body.style.overflow = ''; }catch(_){ }
  }

  window.openProcess = openProcess;
  window.closeProcess = closeProcess;
})();
