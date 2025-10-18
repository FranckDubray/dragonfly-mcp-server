

// Workers Process - Overlay Core (DOM creation + minimal helpers)
(function(){
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

  function showProcessAlert(msg){ ensureProcessAlert(); var el = document.getElementById('processAlert'); if (!el) return; el.textContent = msg; el.style.display = 'block'; }
  function hideProcessAlert(){ var el = document.getElementById('processAlert'); if (!el) return; el.style.display = 'none'; el.textContent = ''; }

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
      '      <div class="tm-clock" id="tmClock" title="Heure de la tâche sélectionnée">🕒 --:--:--</div>'+
      '      <div class="replay-controls" style="display:inline-flex; gap:6px; align-items:center;">'+
      '        <button class="btn btn-ghost" id="btnRw" title="Rewind">⏮</button>'+
      '        <button class="btn btn-ghost" id="btnStepBack" title="Step back">⏪</button>'+
      '        <button class="btn btn-ghost" id="btnStop" title="Stop">⏹</button>'+
      '        <button class="btn btn-ghost" id="btnStepFwd" title="Step forward">⏩</button>'+
      '        <button class="btn btn-ghost" id="btnFf" title="Forward to end">⏭</button>'+
      '        <div class="trail-ctl" style="margin-left:10px; display:inline-flex; align-items:center; gap:6px;">'+
      '          <label for="trailRange" style="font-size:12px; color:#374151;">Trail</label>'+
      '          <input id="trailRange" type="range" min="1" max="5" step="1" value="3" style="width:120px;">'+
      '          <span id="trailVal" style="font-size:12px; color:#111827; font-variant-numeric:tabular-nums; width:24px; display:inline-block; text-align:center;">3</span>'+
      '        </div>'+
      '        <div class="speed-ctl" style="margin-left:10px; display:inline-flex; align-items:center; gap:6px;">'+
      '          <label style="font-size:12px; color:#374151;">Vitesse</label>'+
      '          <button class="btn btn-ghost" id="speedX4" title="x4">x4</button>'+
      '          <button class="btn btn-ghost" id="speedX2" title="x2">x2</button>'+
      '          <button class="btn btn-ghost" id="speed1" title="1x">1x</button>'+
      '          <button class="btn btn-ghost" id="speedD2" title="/2">/2</button>'+
      '          <button class="btn btn-ghost" id="speedD4" title="/4">/4</button>'+
      '        </div>'+
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

    // Minimal fallback styles ONLY (no layout override)
    try{
      var sid = 'processInlineStyle';
      if (!document.getElementById(sid)){
        var st = document.createElement('style');
        st.id = sid;
        st.textContent = [
          '#processOverlay{display:none; position:fixed; inset:0; z-index:1000;}',
          '#processOverlay.open{display:block;}',
          // ensure full viewport width + height, avoid generic container max-width
          '#processOverlay .process-content{display:flex; flex-direction:column; height:100vh; width:100vw; max-width:none; margin:0; box-sizing:border-box;}',
          '#processOverlay .process-body{display:flex; gap:16px; flex:1 1 auto; min-height:0; width:100%; box-sizing:border-box;}',
          // Graph pane: fill remaining space
          '#processOverlay .process-graph{flex:1 1 0; min-height:0; min-width:0; overflow:hidden; padding:0;}',
          '#processOverlay .process-graph .mermaid-graph{height:100% !important; margin:0 !important;}',
          '#processOverlay .process-graph svg{display:block; width:100% !important; height:100% !important; max-height:100% !important; max-width:100% !important;}',
          // Side pane: FIXED width (no 40vw max)
          '#processOverlay .process-side{flex:0 0 320px; width:320px; min-width:320px; max-width:320px; overflow:auto; box-sizing:border-box; scrollbar-gutter: stable both-edges;}',
          '#processOverlay .process-side .code{white-space:pre-wrap; word-break:break-word; overflow:auto; max-width:100%;}',
          '#processOverlay .timeline{min-width:0; width:100%;}',
          '#processOverlay .timeline .tl-item{box-sizing:border-box;}',
          '#processOverlay .trail-ctl input[type=range]{ accent-color:#10b981; }'
        ].join('\n');
        document.head.appendChild(st);
      }
    }catch(_){ }

    window.__WPOverlay = window.__WPOverlay || {};
    window.__WPOverlay.overlayEl = el;
    return el;
  }

  // expose + trail UI wiring
  function bindTrailRange(){
    try{
      const el = document.getElementById('processOverlay');
      const range = el?.querySelector('#trailRange');
      const out = el?.querySelector('#trailVal');
      if (!range || !out) return;
      if (typeof WP.trailN === 'undefined'){ WP.trailN = 3; }
      range.value = String(Math.max(1, Math.min(5, WP.trailN)));
      out.textContent = String(range.value);

      const apply = () => {
        const n = Math.max(1, Math.min(5, parseInt(range.value||'3',10)||3));
        WP.trailN = n;
        out.textContent = String(n);
        try{
          const cur = WP.replaySeq?.[WP.replayIx] || WP.currentNodeSelected || '';
          // Rebuild WP.hlTrail from current replay position (no render)
          const seq = Array.isArray(WP.replaySeq)? WP.replaySeq: [];
          let ix = (typeof WP.replayIx==='number' && WP.replayIx>=0)? WP.replayIx : (seq.length? seq.length-1: -1);
          const trail = [];
          for (let k=0;k<n;k++){ const v = seq[ix-k]; if (v) trail.push(v); }
          WP.hlTrail = trail.length? trail: (cur? [cur] : []);
          // Inline highlight only (no Mermaid render here)
          const ok = window.tryGraphInlineHighlight?.(WP.hlTrail);
          if (!ok){ /* fallback very rare: keep silent */ }
        }catch(_){ }
      };
      range.addEventListener('input', apply);

      // Speed factor buttons: x4, x2, 1x, /2, /4
      function bindFactor(btn, factor){ const b = el?.querySelector(btn); if (!b) return; b.addEventListener('click', function(){ try{ if (typeof window.setReplaySpeed === 'function'){ const base=200; window.setReplaySpeed(base / factor); } }catch(_){ } }); }
      bindFactor('#speedX4', 4);
      bindFactor('#speedX2', 2);
      bindFactor('#speed1', 1);
      bindFactor('#speedD2', 0.5);
      bindFactor('#speedD4', 0.25);
    }catch(_){ }
  }

  window.__WPOverlay = Object.assign(window.__WPOverlay||{}, {
    ensureProcessOverlay,
    showProcessAlert,
    hideProcessAlert,
    bindTrailRange
  });
})();
