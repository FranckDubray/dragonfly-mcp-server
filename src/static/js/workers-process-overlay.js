

// Workers Process - Overlay & UI wiring (with tape-like controls)
(function(){
  function ensureProcessOverlay(){
    var el = document.getElementById('processOverlay');
    if (el) return el;
    el = document.createElement('div');
    el.id = 'processOverlay'; el.className = 'process-overlay';
    el.innerHTML = ''+
      '<div class="process-content" role="dialog" aria-modal="true" aria-label="Processus">'+
      '  <div class="process-header">'+
      '    <div class="title">Processus</div>'+
      '    <div class="tools">'+
      '      <div class="replay-controls" style="display:inline-flex; gap:6px; align-items:center;">'+
      '        <button class="btn btn-ghost" id="btnRw" title="Rewind">⏮</button>'+
      '        <button class="btn btn-ghost" id="btnStepBack" title="Step back">⏪</button>'+
      '        <button class="btn btn-ghost" id="btnPlay" title="Play/Pause">▶︎</button>'+
      '        <button class="btn btn-ghost" id="btnStepFwd" title="Step forward">⏩</button>'+
      '        <button class="btn btn-ghost" id="btnFf" title="Forward to end">⏭</button>'+
      '      </div>'+
      '      <button class="btn btn-ghost" id="btnCloseProcess" aria-label="Fermer">×</button>'+
      '    </div>'+
      '  </div>'+
      '  <div class="process-body">'+
      '    <div class="process-graph" id="processGraph"></div>'+
      '    <div class="process-side" id="processSide"></div>'+
      '  </div>'+
      '</div>';
    document.body.appendChild(el);
    el.addEventListener('click', function(e){ if (e.target === el) closeProcess(); });
    document.addEventListener('keydown', function(e){ if (e.key==='Escape') closeProcess(); });

    // Close
    el.querySelector('#btnCloseProcess').addEventListener('click', closeProcess);

    // Bind tape-like controls safely (resolve at click time)
    var q = function(id, fn){ var b = el.querySelector(id); if (!b) return; b.addEventListener('click', function(){ if (typeof window[fn] === 'function') window[fn](); }); };
    q('#btnRw', 'wpReplayRewind');
    q('#btnStepBack', 'wpReplayStepBack');
    q('#btnPlay', 'wpReplayToggle');
    q('#btnStepFwd', 'wpReplayStepForward');
    q('#btnFf', 'wpReplayForwardEnd');

    // Click on timeline item → highlight graph + details (two-way sync)
    el.addEventListener('click', async function(e){
      var it = e.target.closest('.tl-item');
      if (!it) return;
      var stepId = it.getAttribute('data-id');
      var node = it.getAttribute('data-node') || '';
      // Sync highlight in timeline (selected class managed by helper)
      try{ if (typeof highlightTimelineNode === 'function') highlightTimelineNode(node, /*smooth=*/true); }catch(_){ }
      // Sync highlight in graph
      try{
        var graphEl = document.getElementById('processGraph');
        if (graphEl && window.DFMermaid && (window.MERMAID_CACHE || window.__MERMAID_CACHE__)){
          var src = window.MERMAID_CACHE || window.__MERMAID_CACHE__;
          await DFMermaid.renderMermaid(graphEl, src, node||'');
        }
      }catch(_){ }
      // Update replay index (best-effort)
      try{
        if (Array.isArray(WP.replaySeq)){
          var ix = WP.replaySeq.lastIndexOf(String(node||''));
          if (ix >= 0){ WP.replayIx = ix; WP.atTail = (ix >= (WP.replaySeq.length-1)); }
        }
      }catch(_){ }
      // Load details
      if (stepId) await loadAndShowStepDetails(WP.processWorkerId, stepId);
    });
    ensureProcessAlert();
    return el;
  }

  function ensureProcessAlert(){
    var content = document.querySelector('#processOverlay .process-content');
    if (!content) return;
    if (!document.getElementById('processAlert')){
      var hdr = content.querySelector('.process-header');
      var alert = document.createElement('div');
      alert.id = 'processAlert';
      alert.className = 'process-alert';
      alert.style.display = 'none';
      hdr.insertAdjacentElement('afterend', alert);
    }
  }

  function showProcessAlert(msg){ var el = document.getElementById('processAlert'); if (!el) return; el.textContent = msg; el.style.display = 'block'; }
  function hideProcessAlert(){ var el = document.getElementById('processAlert'); if (!el) return; el.style.display = 'none'; el.textContent = ''; }

  async function openProcess(workerId){
    WP.processWorkerId = String(workerId||'');
    var overlay = ensureProcessOverlay(); overlay.classList.add('open');
    // Ensure Mermaid loader is available (guarded)
    if (typeof window.ensureMermaid === 'function') { await window.ensureMermaid(); }
    if (typeof window.refreshProcessView === 'function') {
      await window.refreshProcessView();
    }
    clearInterval(WP.processRefreshTimer);
    WP.processRefreshTimer = setInterval(async function(){
      var open = document.getElementById('processOverlay')?.classList.contains('open');
      if (!open){ clearInterval(WP.processRefreshTimer); return; }
      if (typeof window.refreshProcessView === 'function') { await window.refreshProcessView(); }
    }, 10000);
  }
  function closeProcess(){
    clearInterval(WP.processRefreshTimer); WP.processRefreshTimer=null;
    if (typeof window.clearReplayTimer === 'function') { try{ window.clearReplayTimer(); }catch(_){ } }
    var el = document.getElementById('processOverlay'); if (el) el.classList.remove('open');
  }

  window.openProcess = openProcess;
  window.closeProcess = closeProcess;
  window.showProcessAlert = showProcessAlert;
  window.hideProcessAlert = hideProcessAlert;
})();
