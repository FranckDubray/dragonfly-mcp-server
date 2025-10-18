








// Workers Process - UI Highlight & Clock helpers
(function(){
  function sanitizeId(s){ return String(s||'').replace(/[^A-Za-z0-9_]/g,'').toLowerCase(); }

  // Parse timestamp assuming: if NO explicit offset, it's UTC in DB
  function robustParseTsUTC(ts){
    try{
      if (!ts) return null;
      const raw = String(ts).trim();
      // If raw already ISO with timezone (Z or ±HH:MM), let Date parse it
      if (/Z|[+\-]\d{2}:?\d{2}$/.test(raw)){
        const dIso = new Date(raw);
        if (!isNaN(dIso)) return dIso;
      }
      // Prefer: naive SQLite format → parse as UTC (avoid native parse as local time)
      const m = raw.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?$/);
      if (m){
        const date = `${m[1]}-${m[2]}-${m[3]}`;
        const hms = `${m[4]}:${m[5]}:${m[6]}`;
        let frac = m[7] ? ('.'+m[7]) : '';
        if (frac.length > 4) frac = frac.slice(0,4); // keep ms precision
        const iso = `${date}T${hms}${frac}Z`; // assume UTC
        const du = new Date(iso);
        if (!isNaN(du)) return du;
      }
      // Fallback: native parse (last resort; browsers may treat as local)
      let d = new Date(raw);
      if (!isNaN(d)) return d;
    }catch(_){ }
    return null;
  }

  function setTmClockISO(iso){
    try{
      var el = document.getElementById('tmClock'); if (!el) return;
      if (!iso){ el.textContent = '🕒 --:--:--'; return; }
      var d = robustParseTsUTC(iso);
      if (!d || isNaN(d)){ el.textContent = '🕒 ' + String(iso); return; }
      var lang = (typeof navigator !== 'undefined' && navigator.language) ? navigator.language : 'fr-FR';
      var time = d.toLocaleTimeString(lang, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      el.textContent = '🕒 ' + time;
      el.title = d.toLocaleString(lang, { dateStyle: 'short', timeStyle: 'medium' });
    }catch(_){ }
  }

  function updateClockFromItem(it){
    try{
      if (!it) return;
      var iso = it.getAttribute('data-ts') || '';
      if (iso){ setTmClockISO(iso); return; }
      var whenText = it.querySelector('.tl-when')?.textContent || '';
      var d = robustParseTsUTC(whenText);
      if (d) setTmClockISO(d.toISOString()); else setTmClockISO(whenText);
    }catch(_){ }
  }

  function highlightTimelineNode(node, smooth){
    try{
      var box = document.getElementById('timelineBox'); if (!box) return;
      var items = box.querySelectorAll('.tl-item');
      var target = null; var needle = String(node||'').trim().toLowerCase();
      var needleSan = sanitizeId(needle);
      // clear previous states (current + trail)
      items.forEach(function(it){ it.classList.remove('selected','selected-1','selected-2'); });
      // find target by exact or sanitized match
      items.forEach(function(it){
        if (target) return;
        var n = (it.getAttribute('data-node')||'').toLowerCase();
        if (!n) return;
        if (n === needle || sanitizeId(n) === needleSan) target = it;
      });
      if (target){
        target.classList.add('selected');
        // add trail highlights to previous two steps in time (next siblings because list is newest→oldest)
        var prev1 = target.nextElementSibling; if (prev1 && prev1.classList.contains('tl-item')) prev1.classList.add('selected-1');
        var prev2 = prev1 && prev1.nextElementSibling; if (prev2 && prev2.classList.contains('tl-item')) prev2.classList.add('selected-2');
        try { target.scrollIntoView({ block:'center', behavior: smooth? 'smooth':'auto' }); } catch(_) { target.scrollIntoView(true); }
        WP.currentNodeSelected = target.getAttribute('data-node')||String(node||'');
        updateClockFromItem(target);
      }
    }catch(_){ }
  }

  function highlightTimelineById(id, smooth){
    try{
      var box = document.getElementById('timelineBox'); if (!box) return;
      var items = box.querySelectorAll('.tl-item');
      items.forEach(function(it){ it.classList.remove('selected','selected-1','selected-2'); });
      var target = box.querySelector('.tl-item[data-id="'+CSS.escape(String(id))+'"]');
      if (target){
        target.classList.add('selected');
        var prev1 = target.nextElementSibling; if (prev1 && prev1.classList.contains('tl-item')) prev1.classList.add('selected-1');
        var prev2 = prev1 && prev1.nextElementSibling; if (prev2 && prev2.classList.contains('tl-item')) prev2.classList.add('selected-2');
        try { target.scrollIntoView({ block:'center', behavior: smooth? 'smooth':'auto' }); } catch(_) { target.scrollIntoView(true); }
        var node = target.getAttribute('data-node')||'';
        WP.currentNodeSelected = node;
        updateClockFromItem(target);
      }
    }catch(_){ }
  }

  function fmtTs(ts){
    var lang = (typeof navigator !== 'undefined' && navigator.language) ? navigator.language : 'fr-FR';
    try{ var d = robustParseTsUTC(ts); if (d) return d.toLocaleString(lang, { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit' }); }catch(_){ }
    return String(ts||'');
  }

  // Bridge: Graph → timeline (user intent → lock)
  window.addEventListener('wp-node-select', function(e){
    try{
      var id = e?.detail?.node || '';
      if (id){ if (typeof window.armUserLock === 'function') window.armUserLock(5000); WP.currentNodeSelected = String(id); highlightTimelineNode(id, /*smooth=*/true); }
    }catch(_){ }
  });

  // Expose
  window.sanitizeId = sanitizeId;
  window.setTmClockISO = setTmClockISO;
  window.updateClockFromItem = updateClockFromItem;
  window.highlightTimelineNode = highlightTimelineNode;
  window.highlightTimelineById = highlightTimelineById;
  window.fmtTs = fmtTs;
})();

 
 
 
 

 
 
 
 
 
 
 
 

 
 
