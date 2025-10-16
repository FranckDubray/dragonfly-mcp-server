

// Workers Process - UI Replay controls (tape-like)
(function(){
  var SPEED_MS = 1200;
  async function ensureMermaidMaybe(){ try{ if (typeof window.ensureMermaid === 'function') await window.ensureMermaid(); }catch(_){ } }

  function atTail(){
    return WP.replaySeq && WP.replaySeq.length && WP.replayIx >= (WP.replaySeq.length - 1);
  }

  async function renderOne(node){
    try{
      await ensureMermaidMaybe();
      var graphEl = document.getElementById('processGraph'); if (!graphEl) return;
      var src = window.MERMAID_CACHE || window.__MERMAID_CACHE__ || '';
      if (!src) return;
      if (window.DFMermaid && typeof DFMermaid.renderMermaid === 'function') {
        await DFMermaid.renderMermaid(graphEl, src, node||'');
      } else if (typeof window.renderMermaid === 'function') {
        await window.renderMermaid(src, graphEl, node||'');
      }
      // Highlight timeline (no smooth during replay)
      if (typeof highlightTimelineNode === 'function') highlightTimelineNode(node||'', /*smooth=*/false);
      WP.currentNodeSelected = String(node||'');
    }catch(_){ }
  }

  function wpReplayToggle(){
    if (!Array.isArray(WP.replaySeq) || WP.replaySeq.length===0) return;
    // Si on est en bout, repartir du début pour voir un replay utile
    if (WP.replayIx >= WP.replaySeq.length-1) WP.replayIx = 0;
    WP.replayActive = !WP.replayActive;
    if (WP.replayActive){
      if (WP.replayTimer) clearInterval(WP.replayTimer);
      WP.replayTimer = setInterval(wpReplayStepForward, SPEED_MS);
    } else {
      if (WP.replayTimer) { clearInterval(WP.replayTimer); WP.replayTimer=null; }
    }
  }

  async function wpReplayStepForward(){
    if (!Array.isArray(WP.replaySeq) || WP.replaySeq.length===0) return;
    var node = WP.replaySeq[Math.max(0, Math.min(WP.replayIx, WP.replaySeq.length-1))] || '';
    await renderOne(node);
    WP.replayIx = Math.min(WP.replaySeq.length-1, WP.replayIx+1);
    WP.atTail = (WP.replayIx >= WP.replaySeq.length-1);
    if (WP.atTail && WP.replayTimer){ clearInterval(WP.replayTimer); WP.replayTimer=null; WP.replayActive=false; }
  }

  async function wpReplayStepBack(){
    if (!Array.isArray(WP.replaySeq) || WP.replaySeq.length===0) return;
    WP.replayIx = Math.max(0, WP.replayIx-1);
    var node = WP.replaySeq[WP.replayIx] || '';
    await renderOne(node);
    WP.atTail = atTail();
  }

  async function wpReplayRewind(){
    if (!Array.isArray(WP.replaySeq) || WP.replaySeq.length===0) return;
    WP.replayIx = 0;
    await renderOne(WP.replaySeq[0] || '');
    WP.atTail = atTail();
  }

  async function wpReplayForwardEnd(){
    if (!Array.isArray(WP.replaySeq) || WP.replaySeq.length===0) return;
    WP.replayIx = WP.replaySeq.length-1;
    await renderOne(WP.replaySeq[WP.replayIx] || '');
    WP.atTail = true;
  }

  function clearReplayTimer(){ if (WP.replayTimer){ clearInterval(WP.replayTimer); WP.replayTimer=null; } }

  window.wpReplayToggle = wpReplayToggle;
  window.wpReplayStepForward = wpReplayStepForward;
  window.wpReplayStepBack = wpReplayStepBack;
  window.wpReplayRewind = wpReplayRewind;
  window.wpReplayForwardEnd = wpReplayForwardEnd;
  window.clearReplayTimer = clearReplayTimer;
})();
