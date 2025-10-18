










// Workers Process - UI Side panel helpers + timeline rebuild
(function(){
  function escapeHtml(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  window.escapeHtml = window.escapeHtml || escapeHtml;

  // Parse timestamp assuming: if NO explicit offset, it's UTC in DB
  function robustParseTsUTC(ts){
    try{
      if (!ts) return null;
      const raw = String(ts).trim();
      // If explicit timezone/offset: let Date handle it
      if (/Z|[+\-]\d{2}:?\d{2}$/.test(raw)){
        const dIso = new Date(raw);
        if (!isNaN(dIso)) return dIso;
      }
      // Detect common SQLite naive form → parse as UTC
      const m = raw.match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?$/);
      if (m){
        const date = m[1];
        const hms = m[2];
        let frac = m[3] ? ('.'+m[3]) : '';
        if (frac.length > 4) frac = frac.slice(0,4); // keep ms precision
        const iso = `${date}T${hms}${frac}Z`; // assume UTC if no offset provided
        const d = new Date(iso);
        if (!isNaN(d)) return d;
      }
      // Fallback: try native parse (last resort)
      const d2 = new Date(raw);
      if (!isNaN(d2)) return d2;
    }catch(_){ }
    return null;
  }

  function fmtTsLocal(ts){
    try{
      var d = robustParseTsUTC(ts);
      var lang = (typeof navigator !== 'undefined' && navigator.language) ? navigator.language : 'fr-FR';
      var out = d? d.toLocaleString(lang, { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit' }) : String(ts||'');
      return out;
    }catch(_){ }
    return String(ts||'');
  }

  async function updateProcessSide(rangeKey, currentArgs, preloadedHistory){
    var sideEl = document.getElementById('processSide'); if (!sideEl) return;
    var argsStr = String(currentArgs||'');
    var history = preloadedHistory || (window.WPData && typeof WPData.fetchHistory==='function' ? await WPData.fetchHistory(rangeKey) : []);

    // Build signatures to avoid useless reflows
    var len = (history||[]).length;
    var firstId = len? history[0].id: 0;
    var lastId = len? history[len-1].id: 0;
    var histSig = [len, firstId, lastId].join(':');
    var argsSig = String(argsStr).length + ':' + (argsStr? argsStr.charCodeAt(0): 0);
    var globalSig = histSig + '|' + argsSig;
    if (window.WP && WP.timelineSig === globalSig){
      if (window.WP.currentNodeSelected && typeof window.highlightTimelineNode==='function') highlightTimelineNode(WP.currentNodeSelected, /*smooth=*/false);
      return;
    }
    if (window.WP) WP.timelineSig = globalSig;

    // Build history panel
    var histItems = (history||[]).map(function(h){
      var ts = String(h.ts||'');
      var tsLocal = fmtTsLocal(ts);
      var node = escapeHtml(h.node||'');
      var status = escapeHtml(h.status||'');
      var tsAttr = ts; // raw for precise matching; parse happens when displaying clock
      return '<div class="tl-item" data-id="'+h.id+'" data-node="'+node+'" data-ts="'+escapeHtml(tsAttr)+'">'
             + '  <div class="tl-when">'+escapeHtml(tsLocal)+'</div>'
             + '  <div class="tl-node">'+node+'</div>'
             + '  <div class="tl-status '+status+'">'+status+'</div>'
             + '</div>';
    }).join('');

    var histHtml = '<div class="panel"><div class="panel-title">Historique</div><div class="timeline" id="timelineBox">'+(histItems||'<div class="empty">Aucun événement</div>')+'</div></div>';
    sideEl.innerHTML = histHtml + '<div class="panel" id="stepDetails"><div class="panel-title">Détails</div><div class="code">Cliquez un événement pour voir les détails</div></div>';

    // Apply selection + clock update
    if (window.WP && WP.currentNodeSelected && typeof window.highlightTimelineNode==='function') highlightTimelineNode(WP.currentNodeSelected, /*smooth=*/false);
  }

  window.updateProcessSide = updateProcessSide;
})();

 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
