
// Workers Process - UI Replay controls (tape-like) + verbose debug
(function(){
  var SPEED_MS_DEFAULT = 600; // accéléré (avant: 1200ms)
  function getSpeed(){
    try{ var v = Number(WP?.replaySpeed||SPEED_MS_DEFAULT); return Math.max(200, Math.min(5000, v)); }catch(_){ return SPEED_MS_DEFAULT; }
  }
  async function ensureMermaidMaybe(){ try{ if (typeof window.ensureMermaid === 'function') await window.ensureMermaid(); }catch(_){ } }

  function atTail(){
    return WP.replaySeq && WP.replaySeq.length && WP.replayIx >= (WP.replaySeq.length - 1);
  }

  function syncTimelineHighlight(ix){
    try{
      if (!Array.isArray(WP.replayMeta) || !WP.replayMeta.length) return;
      var hi = Math.max(0, Math.min(ix, WP.replayMeta.length-1));
      var stepId = WP.replayMeta[hi]?.id;
      if (stepId){
        WP.desiredHighlightStepId = stepId; // persist across refresh
        if (typeof window.highlightTimelineById === 'function') window.highlightTimelineById(String(stepId), /*smooth=*/false);
      } else {
        // fallback by node label
        var node = WP.replaySeq?.[hi] || '';
        if (node && typeof window.highlightTimelineNode === 'function') window.highlightTimelineNode(String(node), /*smooth=*/false);
      }
    }catch(_){ }
  }

  async function highlightTrailOrRender(node){
    try{
      var trail = [];
      if (Array.isArray(WP.replaySeq)){
        var ix = Math.max(0, Math.min(WP.replayIx, WP.replaySeq.length-1));
        var cur = WP.replaySeq[ix] || node || '';
        trail.push(cur);
        var n = Math.max(1, Math.min(10, WP.trailN || 3));
        for (let k=1;k<n;k++){ const v = WP.replaySeq[ix-k]; if (v) trail.push(v); }
        WP.hlTrail = trail;
      } else {
        WP.hlTrail = node ? [node] : [];
      }
      var ok = (typeof window.tryGraphInlineHighlight === 'function') ? window.tryGraphInlineHighlight(WP.hlTrail) : false;
      if (!ok){
        await ensureMermaidMaybe();
        var graphEl = document.getElementById('processGraph'); if (!graphEl) return;
        var src = window.MERMAID_CACHE || window.__MERMAID_CACHE__ || '';
        if (!src) return;
        if (window.DFMermaid && typeof DFMermaid.renderMermaid === 'function') {
          await DFMermaid.renderMermaid(graphEl, src, trail[0]||node||'');
          try{ window.tryGraphInlineHighlight(trail); }catch(_){ }
        }
      }
    }catch(e){ console.warn('[REPLAY] highlightTrailOrRender error', e); }
  }

  function wpReplayStart(){
    if (!Array.isArray(WP.replaySeq) || WP.replaySeq.length===0) { console.info('[REPLAY] start: no sequence'); return; }
    if (WP.replayActive) { console.info('[REPLAY] already running'); return; }
    WP.replayActive = true;
    if (WP.replayTimer) clearInterval(WP.replayTimer);
    console.info('[REPLAY] start', { ix: WP.replayIx, len: WP.replaySeq.length, speed_ms: getSpeed() });
    WP.replayTimer = setInterval(wpReplayStepForward, getSpeed());
  }

  function wpReplayToggle(){
    if (!Array.isArray(WP.replaySeq) || WP.replaySeq.length===0) return;
    WP.replayActive = !WP.replayActive;
    if (WP.replayActive){
      if (WP.replayTimer) clearInterval(WP.replayTimer);
      console.info('[REPLAY] resume', { ix: WP.replayIx, len: WP.replaySeq.length, speed_ms: getSpeed() });
      WP.replayTimer = setInterval(wpReplayStepForward, getSpeed());
    } else {
      if (WP.replayTimer) { clearInterval(WP.replayTimer); WP.replayTimer=null; }
      console.info('[REPLAY] pause', { ix: WP.replayIx, len: WP.replaySeq.length });
    }
  }

  async function wpReplayStepForward(){
    // Ne pas lancer un pas si une animation est en cours
    if (window.WP?.animating) { return; }

    if (!Array.isArray(WP.replaySeq) || WP.replaySeq.length===0) { console.info('[REPLAY] step: no seq'); return; }
    var maxIx = WP.replaySeq.length - 1;
    WP.replayIx = Math.min(maxIx, Math.max(0, WP.replayIx||0));

    // Compute highlight index in timeline: previous step (completed) when advancing
    var histIx = Math.max(0, WP.replayIx - 1);
    syncTimelineHighlight(histIx);

    var node = WP.replaySeq[WP.replayIx] || '';
    var next = WP.replaySeq[Math.min(WP.replayIx+1, maxIx)] || '';
    // Petit train: animer le pas courant si un "next" existe
    try{
      if (next && window.RenderHighlight?.animateStep){
        await window.RenderHighlight.animateStep(node, next, WP.trailN);
      } else {
        await highlightTrailOrRender(node);
      }
    }catch(_){ await highlightTrailOrRender(node); }

    if (WP.replayIx < maxIx) {
      WP.replayIx = Math.min(maxIx, WP.replayIx+1);
      WP.atTail = (WP.replayIx >= maxIx);
    } else {
      WP.atTail = true;
      if (WP.replayTimer){ clearInterval(WP.replayTimer); WP.replayTimer=null; }
      WP.replayActive = false;
      console.info('[REPLAY] done', { ix: WP.replayIx, len: WP.replaySeq.length });
    }
  }

  async function wpReplayStepBack(){
    if (!Array.isArray(WP.replaySeq) || WP.replaySeq.length===0) return;
    WP.replayIx = Math.max(0, (WP.replayIx||0)-1);
    var node = WP.replaySeq[WP.replayIx] || '';
    syncTimelineHighlight(WP.replayIx);
    console.info('[REPLAY] back', { ix: WP.replayIx, node });
    await highlightTrailOrRender(node);
    WP.atTail = atTail();
  }

  async function wpReplayRewind(){
    if (!Array.isArray(WP.replaySeq) || WP.replaySeq.length===0) return;
    WP.replayIx = 0;
    syncTimelineHighlight(WP.replayIx);
    console.info('[REPLAY] rewind');
    await highlightTrailOrRender(WP.replaySeq[0] || '');
    WP.atTail = atTail();
  }

  async function wpReplayForwardEnd(){
    if (!Array.isArray(WP.replaySeq) || WP.replaySeq.length===0) return;
    var last = WP.replaySeq.length-1;
    WP.replayIx = last;
    syncTimelineHighlight(WP.replayIx);
    console.info('[REPLAY] toEnd');
    await highlightTrailOrRender(WP.replaySeq[last] || '');
    WP.atTail = true;
    if (WP.replayTimer){ clearInterval(WP.replayTimer); WP.replayTimer=null; }
    WP.replayActive = false;
  }

  function clearReplayTimer(){ if (WP.replayTimer){ clearInterval(WP.replayTimer); WP.replayTimer=null; } }
  function wpReplayPause(){ if (WP.replayTimer){ clearInterval(WP.replayTimer); WP.replayTimer = null; } WP.replayActive = false; console.info('[REPLAY] pause() called'); }
  async function wpReplayRenderCurrent(){
    if (!Array.isArray(WP.replaySeq) || WP.replaySeq.length===0) return;
    var maxIx = WP.replaySeq.length - 1;
    WP.replayIx = Math.max(0, Math.min(WP.replayIx || 0, maxIx));
    var node = WP.replaySeq[WP.replayIx] || '';
    syncTimelineHighlight(Math.max(0, WP.replayIx - 1));
    console.info('[REPLAY] renderCurrent', { ix: WP.replayIx, node });
    await highlightTrailOrRender(node);
    WP.atTail = (WP.replayIx >= maxIx);
  }

  // API pour changer la vitesse à chaud (ex depuis la console): setReplaySpeed(400)
  function setReplaySpeed(ms){
    try{
      var v = Number(ms); if (!isFinite(v)) return;
      WP.replaySpeed = Math.max(200, Math.min(5000, v));
      console.info('[REPLAY] speed set', { speed_ms: WP.replaySpeed });
      if (WP.replayActive){
        if (WP.replayTimer) clearInterval(WP.replayTimer);
        WP.replayTimer = setInterval(wpReplayStepForward, getSpeed());
      }
    }catch(_){ }
  }

  // Expose
  window.wpReplayStart = wpReplayStart;
  window.wpReplayToggle = wpReplayToggle;
  window.wpReplayStepForward = wpReplayStepForward;
  window.wpReplayStepBack = wpReplayStepBack;
  window.wpReplayRewind = wpReplayRewind;
  window.wpReplayForwardEnd = wpReplayForwardEnd;
  window.clearReplayTimer = clearReplayTimer;
  window.wpReplayPause = wpReplayPause;
  window.wpReplayRenderCurrent = wpReplayRenderCurrent;
  window.setReplaySpeed = setReplaySpeed;
})();
