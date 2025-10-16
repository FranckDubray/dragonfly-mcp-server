

// Workers Process - UI Core (mermaid ensure, refresh, side panel)
(function(){
  var MERMAID_CACHE = '';

  async function ensureMermaid(){
    if (WP.mermaidReady && window.mermaid) return;
    var existing = document.querySelector('script[data-mermaid]');
    if (existing && window.mermaid){ WP.mermaidReady = true; return; }
    var s = document.createElement('script');
    s.src = 'https://unpkg.com/mermaid@10/dist/mermaid.min.js';
    s.async = true; s.defer = true; s.setAttribute('data-mermaid','1');
    s.onload = function(){ try{ window.mermaid.initialize({ startOnLoad:false, theme:'neutral', securityLevel:'loose' }); WP.mermaidReady = true; }catch(_){} };
    document.head.appendChild(s);
  }

  function pickLatestCompleted(history){
    if (!Array.isArray(history) || history.length===0) return null;
    for (var i=0;i<history.length;i++){ if (String(history[i].status||'').toLowerCase()==='succeeded') return history[i]; }
    for (var j=0;j<history.length;j++){ if (String(history[j].status||'').toLowerCase()==='failed') return history[j]; }
    return history[0];
  }

  async function refreshProcessView(){
    var graphEl = document.getElementById('processGraph');
    var sideEl = document.getElementById('processSide');
    var rangeSelect = document.getElementById('replayRange');
    if (!graphEl || !sideEl || !rangeSelect) return;
    try {
      MERMAID_CACHE = await WPData.fetchMermaid();
      // Expose cache globally for other modules (overlay click)
      window.MERMAID_CACHE = MERMAID_CACHE;

      var current = await WPData.fetchCurrentState();
      var historyOpen = await WPData.fetchHistory(rangeSelect.value);
      var latestCompleted = pickLatestCompleted(historyOpen);

      // Node à afficher/mettre en évidence
      var openNode = '';
      if (WP.atTail === true || !WP.currentNodeSelected){
        openNode = latestCompleted ? (latestCompleted.node||'') : (current.node||'');
        WP.currentNodeSelected = openNode || WP.currentNodeSelected || '';
      } else {
        openNode = WP.currentNodeSelected || (latestCompleted ? (latestCompleted.node||'') : (current.node||''));
      }

      // Render graph (no-op inside if nothing changed)
      if (MERMAID_CACHE){ await renderMermaid(MERMAID_CACHE, graphEl, openNode); }
      else { graphEl.innerHTML = '<p style="padding:10px;">Graph non disponible</p>'; }

      // Update side panel only if data changed
      await updateProcessSide(rangeSelect.value, current.args, historyOpen);

      // Rebuild replaySeq (based on visible window) and maintain tail semantics
      var wasAtTail = (WP.atTail === true);
      WP.replaySeq = await buildReplaySequence(rangeSelect.value);
      if (wasAtTail) { WP.replayIx = Math.max(0, WP.replaySeq.length - 1); }
      else { WP.replayIx = Math.min(WP.replayIx || 0, Math.max(0, WP.replaySeq.length - 1)); }
      WP.atTail = (WP.replayIx >= (WP.replaySeq.length - 1));

      // KPIs (only update if changed) + Consistency + Highlight timeline (no smooth at init)
      await renderKpis(sideEl);
      await WPConsistency.checkConsistency(MERMAID_CACHE, openNode);

      // Synchronize highlight BOTH: timeline + mermaid already rendered with openNode
      var initialSmooth = false;
      // If we know the exact latestCompleted id and we are at tail, use id highlight; else fallback node
      if (latestCompleted && (WP.atTail === true)) highlightTimelineById(String(latestCompleted.id), /*smooth=*/initialSmooth);
      else if (openNode) highlightTimelineNode(openNode, /*smooth=*/initialSmooth);

    } catch (e) {
      console.error('[Mermaid] render error:', e);
      graphEl.innerHTML = '<p style="padding:10px;color:var(--danger);">Erreur Mermaid: '+escapeHtml(e.message||e)+'</p>';
    }
  }

  async function renderKpis(sideEl){
    try{
      var k = await WPData.fetchStatsLastHour();
      var sig = [k.tasks||0, k.llm_calls||0, k.cycles||0].join('|');
      if (WP.kpisSig === sig) return; // no change
      WP.kpisSig = sig;

      var panel = document.createElement('div');
      panel.className = 'panel';
      panel.innerHTML = ''+
        '<div class="panel-title">Activité (dernière heure)</div>'+
        '<div class="kpis" style="display:grid; grid-template-columns: repeat(3, 1fr); gap:8px;">'+
          '<div class="kpi"><div class="stat-value">'+(Number(k.tasks)||0)+'</div><div class="stat-label">Tâches</div></div>'+
          '<div class="kpi"><div class="stat-value">'+(Number(k.llm_calls)||0)+'</div><div class="stat-label">Appels call_llm</div></div>'+
          '<div class="kpi"><div class="stat-value">'+(Number(k.cycles)||0)+'</div><div class="stat-label">Cycles</div></div>'+
        '</div>';
      var old = sideEl.querySelector('.panel .panel-title')?.textContent?.includes('Activité (dernière heure)') ? sideEl.querySelector('.panel') : null;
      if (old && old.parentElement === sideEl) {
        sideEl.replaceChild(panel, old.closest('.panel'));
      } else {
        sideEl.prepend(panel);
      }
    }catch(_){ }
  }

  async function buildReplaySequence(rangeKey){
    var hist = await WPData.fetchHistory(rangeKey);
    var nodes = [];
    for (var i=hist.length-1; i>=0; i--){ var n = String(hist[i].node||'').trim(); if (n && nodes[nodes.length-1]!==n) nodes.push(n); }
    return nodes;
  }

  function highlightTimelineNode(node, smooth){
    try{
      var box = document.getElementById('timelineBox'); if (!box) return;
      var items = box.querySelectorAll('.tl-item');
      var target = null; var needle = String(node||'').trim().toLowerCase();
      items.forEach(function(it){ it.classList.remove('selected'); if (!target){ var n = (it.getAttribute('data-node')||'').toLowerCase(); if (n === needle) target = it; } });
      if (target){
        target.classList.add('selected');
        try { target.scrollIntoView({ block:'center', behavior: smooth? 'smooth':'auto' }); } catch(_) { target.scrollIntoView(true); }
      }
      // Persist selected node
      WP.currentNodeSelected = String(node||'');
    }catch(_){ }
  }

  function highlightTimelineById(id, smooth){
    try{
      var box = document.getElementById('timelineBox'); if (!box) return;
      var items = box.querySelectorAll('.tl-item');
      items.forEach(function(it){ it.classList.remove('selected'); });
      var target = box.querySelector('.tl-item[data-id="'+CSS.escape(String(id))+'"]');
      if (target){
        target.classList.add('selected');
        try { target.scrollIntoView({ block:'center', behavior: smooth? 'smooth':'auto' }); } catch(_) { target.scrollIntoView(true); }
        // Persist node from element
        var node = target.getAttribute('data-node')||'';
        WP.currentNodeSelected = node;
      }
    }catch(_){ }
  }

  function safePreviewText(s, max){ var t = String(s||''); if (t.length>max) return t.slice(0,max)+'…'; return t; }

  async function updateProcessSide(rangeKey, currentArgs, preloadedHistory){
    var sideEl = document.getElementById('processSide');
    var argsStr = String(currentArgs||'');
    // Compute signatures to avoid needless redraws
    var history = preloadedHistory || await WPData.fetchHistory(rangeKey);
    var len = history.length;
    var firstId = len? history[0].id: 0;
    var lastId = len? history[len-1].id: 0;
    var histSig = [len, firstId, lastId].join(':');
    var argsSig = String(argsStr).length + ':' + (argsStr? argsStr.charCodeAt(0): 0);
    var globalSig = histSig + '|' + argsSig;

    if (WP.timelineSig === globalSig){
      // Nothing changed → ensure selection highlight stays consistent
      if (WP.currentNodeSelected){ highlightTimelineNode(WP.currentNodeSelected, /*smooth=*/false); }
      return;
    }
    WP.timelineSig = globalSig;

    var preview = safePreviewText(argsStr, 240);
    var argsPanel = '';
    if (argsStr){
      var escapedPreview = escapeHtml(preview);
      var escapedFull = escapeHtml(argsStr);
      argsPanel = ''+
        '<div class="panel">'+
        '  <div class="panel-title">Arguments</div>'+
        '  <pre class="code code-wrap" id="argsPre" data-full="'+escapedFull+'" data-trunc="'+escapedPreview+'">'+escapedPreview+'</pre>'+
        '  <div class="panel-actions" style="margin-top:6px; display:flex; gap:8px;">'+
        (argsStr.length>240? '    <button class="btn btn-ghost" id="btnArgsToggle" style="padding:4px 8px; font-size:12px;">Afficher tout</button>' : '')+
        '    <button class="btn btn-ghost" id="btnArgsCopy" style="padding:4px 8px; font-size:12px;">Copier</button>'+
        '  </div>'+
        '</div>';
    }

    var histItems = (history||[]).map(function(h){
      var ts = fmtTs(h.ts||'');
      var node = escapeHtml(h.node||'');
      var status = escapeHtml(h.status||'');
      return '<div class="tl-item" data-id="'+h.id+'" data-node="'+node+'">'+
             '  <div class="tl-when">'+escapeHtml(ts)+'</div>'+
             '  <div class="tl-node">'+node+'</div>'+
             '  <div class="tl-status '+status+'">'+status+'</div>'+
             '</div>';
    }).join('');
    var histHtml = '<div class="panel"><div class="panel-title">Historique ('+rangeKey+')</div><div class="timeline" id="timelineBox">'+(histItems||'<div class="empty">Aucun événement</div>')+'</div></div>';
    sideEl.innerHTML = (argsPanel||'') + histHtml + '<div class="panel" id="stepDetails"><div class="panel-title">Détails</div><div class="code">Cliquez un événement pour voir les détails</div></div>';
  }

  function fmtTs(ts){
    try{
      var d = new Date(ts);
      if (!isNaN(d)) return d.toLocaleString('fr-FR', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit' });
    }catch(_){ }
    return String(ts||'');
  }

  // Expose
  window.ensureMermaid = ensureMermaid;
  window.refreshProcessView = refreshProcessView;
  window.highlightTimelineNode = highlightTimelineNode;
  window.updateProcessSide = updateProcessSide;
})();
