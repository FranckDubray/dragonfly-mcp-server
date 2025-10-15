


// Workers Process - UI Replay controls (tape-like)
(function(){
  var SPEED_MS = 1200;
  async function ensureMermaidMaybe(){ try{ if (typeof window.ensureMermaid === 'function') await window.ensureMermaid(); }catch(_){ } }

  function atTail(){
    // Vrai si l'index du replay est sur le dernier élément (fin de séquence)
    return WP.replaySeq && WP.replaySeq.length && WP.replayIx >= (WP.replaySeq.length - 1);
  }

  function wpReplayToggle(){
    if (!WP.replaySeq || WP.replaySeq.length===0) return;
    WP.replayActive = !WP.replayActive;
    if (WP.replayActive){ if (WP.replayTimer) clearInterval(WP.replayTimer); WP.replayTimer = setInterval(wpReplayStepForward, SPEED_MS); }
    else { if (WP.replayTimer) clearInterval(WP.replayTimer), WP.replayTimer=null; }
  }
  function wpReplayStepForward(){ if (!WP.replaySeq || WP.replaySeq.length===0) return; var node = WP.replaySeq[WP.replayIx] || ''; renderOne(node); WP.replayIx = Math.min(WP.replaySeq.length-1, WP.replayIx+1); if (WP.replayIx >= WP.replaySeq.length-1){ if (WP.replayTimer) clearInterval(WP.replayTimer), WP.replayTimer=null; WP.replayActive=false; WP.atTail = true; } }
  function wpReplayStepBack(){ if (!WP.replaySeq || WP.replaySeq.length===0) return; WP.replayIx = Math.max(0, WP.replayIx-1); var node = WP.replaySeq[WP.replayIx] || ''; renderOne(node); WP.atTail = atTail(); }
  function wpReplayRewind(){ if (!WP.replaySeq || WP.replaySeq.length===0) return; WP.replayIx = 0; renderOne(WP.replaySeq[0] || ''); WP.atTail = atTail(); }
  function wpReplayForwardEnd(){ if (!WP.replaySeq || WP.replaySeq.length===0) return; WP.replayIx = WP.replaySeq.length-1; renderOne(WP.replaySeq[WP.replayIx] || ''); WP.atTail = true; }

  async function renderOne(node){ try{ await ensureMermaidMaybe(); var graphEl = document.getElementById('processGraph'); if (!graphEl) return; if (!window.DFMermaid && typeof window.renderMermaid !== 'function') return; if (!window.DFMermaid && typeof window.renderMermaid === 'function') { await window.renderMermaid(MERMAID_CACHE, graphEl, node||''); } else { await DFMermaid.renderMermaid(graphEl, MERMAID_CACHE, node||''); } highlightTimelineNode(node||''); }catch(_){ }}

  window.wpReplayToggle = wpReplayToggle;
  window.wpReplayStepForward = wpReplayStepForward;
  window.wpReplayStepBack = wpReplayStepBack;
  window.wpReplayRewind = wpReplayRewind;
  window.wpReplayForwardEnd = wpReplayForwardEnd;
})();

 
 
 
 
 