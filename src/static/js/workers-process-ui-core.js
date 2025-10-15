


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

  async function refreshProcessView(){
    var graphEl = document.getElementById('processGraph');
    var sideEl = document.getElementById('processSide');
    var rangeSelect = document.getElementById('replayRange');
    if (!graphEl || !sideEl || !rangeSelect) return;
    try {
      MERMAID_CACHE = await WPData.fetchMermaid();
      var current = await WPData.fetchCurrentState();
      if (MERMAID_CACHE){ await renderMermaid(MERMAID_CACHE, graphEl, current.node); }
      else { graphEl.innerHTML = '<p style="padding:10px;">Graph non disponible</p>'; }
      await updateProcessSide(rangeSelect.value, current.args);

      // Rebuild replaySeq and maintain tail/auto-advance semantics
      var prevLen = Array.isArray(WP.replaySeq) ? WP.replaySeq.length : 0;
      var wasAtTail = (WP.atTail === true);
      WP.replaySeq = await buildReplaySequence(rangeSelect.value);
      if (wasAtTail) {
        WP.replayIx = Math.max(0, WP.replaySeq.length - 1);
        // si on était en bout (temps réel), on "suit" les nouveaux steps
      } else {
        // si on est dans le passé, on ne bouge pas l'index (autant que possible)
        WP.replayIx = Math.min(WP.replayIx || 0, Math.max(0, WP.replaySeq.length - 1));
      }
      WP.atTail = (WP.replayIx >= (WP.replaySeq.length - 1));

      // KPIs
      await renderKpis(sideEl);
      await WPConsistency.checkConsistency(MERMAID_CACHE, current.node);
      if (current.node) highlightTimelineNode(current.node);
    } catch (e) {
      console.error('[Mermaid] render error:', e);
      graphEl.innerHTML = '<p style="padding:10px;color:var(--danger);">Erreur Mermaid: '+escapeHtml(e.message||e)+'</p>';
    }
  }

  async function renderKpis(sideEl){
    try{
      var k = await WPData.fetchStatsLastHour();
      var panel = document.createElement('div');
      panel.className = 'panel';
      panel.innerHTML = ''+
        '<div class="panel-title">Activité (dernière heure)</div>'+
        '<div class="kpis" style="display:grid; grid-template-columns: repeat(3, 1fr); gap:8px;">'+
          '<div class="kpi"><div class="stat-value">'+(k.tasks||0)+'</div><div class="stat-label">Tâches</div></div>'+
          '<div class="kpi"><div class="stat-value">'+(k.llm_calls||0)+'</div><div class="stat-label">Appels call_llm</div></div>'+
          '<div class="kpi"><div class="stat-value">'+(k.cycles||0)+'</div><div class="stat-label">Cycles</div></div>'+
        '</div>';
      // Insère en tête du côté droit (et remplace l'ancien panneau s'il existe)
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

  function highlightTimelineNode(node){
    try{
      var box = document.getElementById('timelineBox'); if (!box) return;
      var items = box.querySelectorAll('.tl-item');
      var target = null; var needle = String(node||'').trim().toLowerCase();
      items.forEach(function(it){ it.classList.remove('selected'); if (!target){ var n = (it.getAttribute('data-node')||'').toLowerCase(); if (n === needle) target = it; } });
      if (target){ target.classList.add('selected'); target.scrollIntoView({ block:'center', behavior:'smooth' }); }
    }catch(_){ }
  }

  function safePreviewText(s, max){ var t = String(s||''); if (t.length>max) return t.slice(0,max)+'…'; return t; }

  async function updateProcessSide(rangeKey, currentArgs){
    var sideEl = document.getElementById('processSide');
    var argsStr = String(currentArgs||'');
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
    var history = await WPData.fetchHistory(rangeKey);
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

 
 
 
 
 