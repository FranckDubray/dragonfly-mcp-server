
// Workers Process - Render Highlight (core public API)
(function(){
  const SH = window.__RenderHLShared || {};

  function clearNodeLevels(svg){
    try{
      svg.querySelectorAll([
        'g.node.node-hl-0','g.node.node-hl-1','g.node.node-hl-2','g.node.node-hl-3','g.node.node-hl-4',
        'g.node.node-hl-5','g.node.node-hl-6','g.node.node-hl-7','g.node.node-hl-8','g.node.node-hl-9'
      ].join(',')).forEach(n => { n.classList.remove('node-hl-0','node-hl-1','node-hl-2','node-hl-3','node-hl-4','node-hl-5','node-hl-6','node-hl-7','node-hl-8','node-hl-9'); });
    }catch(_){ }
  }

  function nodesLitCount(totalTrailSetting){
    // Interprétation: trail inclut la flèche; nombre de boîtes visibles = trail - 1 (min 1)
    try{ const t = Number(totalTrailSetting||3); return Math.max(1, t - 1); }catch(_){ return 2; }
  }

  // Only update node classes (no edges). Apply node-hl-0 to head, node-hl-1 to 1..nodesLit-1
  function setNodeHighlightsOnly(trail){
    try{
      const container = document.getElementById('processGraph');
      const svg = container?.querySelector('svg');
      if (!svg) return false;
      SH.ensureHighlightStyle?.(svg);
      clearNodeLevels(svg);
      const t = Array.isArray(trail) ? trail : [];
      if (!t.length) return true;
      const litMax = nodesLitCount(window.WP?.trailN);
      // head
      const head = SH.findNodeByLabel?.(svg, String(t[0]||''));
      if (head && head.g) head.g.classList.add('node-hl-0');
      // mid up to litMax-1 others
      for (let i=1;i<Math.min(litMax, t.length);i++){
        const mid = SH.findNodeByLabel?.(svg, String(t[i]||''));
        if (mid && mid.g) mid.g.classList.add('node-hl-1');
      }
      return true;
    }catch(_){ return false; }
  }

  function tryGraphInlineHighlight(trail){
    try{
      const container = document.getElementById('processGraph');
      if (!container) return false;
      const svg = container.querySelector('svg');
      if (!svg) return false;
      const okNodes = setNodeHighlightsOnly(trail);
      try{ window.RenderHighlight?.styleHeadEdge?.(trail); }catch(_){ }
      return !!okNodes;
    }catch(_){ return false; }
  }

  // ---- Animated step ("petit train") ----
  async function animateStep(prevNode, nextNode, trailN, opts){
    try{
      if (window.WP?.animating) return false;
      window.WP = window.WP || {}; WP.animating = true;
      const container = document.getElementById('processGraph');
      const svg = container?.querySelector('svg'); if (!svg) { WP.animating=false; return false; }
      const sleep = (ms)=> new Promise(r=>setTimeout(r, ms));
      const getSpeed = ()=>{ try{ return Math.max(200, Math.min(5000, Number(WP?.replaySpeed||600))); }catch(_){ return 600; } };
      const tempo = getSpeed();
      const p = Math.max(120, Math.round(tempo/3)); // pauses plus visibles

      const cur = String(prevNode||'');
      const nxt = String(nextNode||'');
      const N = nodesLitCount(trailN||WP?.trailN||3);

      // working trail = [nxt, cur, ... anciens]
      const oldTrail = Array.isArray(WP?.hlTrail) ? WP.hlTrail.slice() : [];
      const working = [nxt, cur].concat(oldTrail.slice(1));

      // 1) flèche suivante (head)
      if (cur && nxt){ try{ window.RenderHighlight?.setEdgeLevel?.(cur, nxt, 'head'); }catch(_){ } }
      await sleep(p);

      // 2) boîte suivante (head)
      try{ setNodeClass(svg, nxt, 'node-hl-0'); }catch(_){ }
      await sleep(p);

      // 3) boîte courante head -> mid
      try{ setNodeClass(svg, cur, 'node-hl-1'); }catch(_){ }
      await sleep(p);

      // 4) flèche précédente head -> mid
      const prevPrev = oldTrail[1] || '';
      if (prevPrev && cur){ try{ window.RenderHighlight?.setEdgeLevel?.(prevPrev, cur, 'mid'); }catch(_){ } }
      await sleep(p);

      // 5) itérer le trail (toutes les arêtes en mid), puis réaffirmer la head
      try{ window.RenderHighlight?.styleTrailEdges?.(working); }catch(_){ }
      await sleep(Math.max(60, Math.round(p/2)));
      if (cur && nxt){ try{ window.RenderHighlight?.setEdgeLevel?.(cur, nxt, 'head'); }catch(_){ } }

      // 6) suppression de la queue si dépassement
      if (working.length > N){
        const tail = working[N];
        const newTailPrev = (N-1)>=0 ? working[N-1] : '';
        try{ clearNode(svg, tail); }catch(_){ }
        await sleep(p);
        if (newTailPrev && tail){ try{ window.RenderHighlight?.setEdgeLevel?.(newTailPrev, tail, null); }catch(_){ }
          await sleep(Math.max(60, Math.round(p/2)));
        }
      }

      // Mettre à jour le trail conservé
      WP.hlTrail = working.slice(0, Math.min(N, working.length));

      return true;
    }catch(e){ return false; }
    finally { try{ WP.animating = false; }catch(_){ } }
  }

  function setNodeClass(svg, label, cls){
    if (!label) return;
    const m = SH.findNodeByLabel?.(svg, String(label));
    if (!m || !m.g) return;
    // Clean existing hl classes, keep others
    m.g.classList.remove('node-hl-0','node-hl-1','node-hl-2','node-hl-3','node-hl-4','node-hl-5','node-hl-6','node-hl-7','node-hl-8','node-hl-9');
    if (cls) m.g.classList.add(cls);
  }
  function clearNode(svg, label){ setNodeClass(svg, label, null); }

  // Back-compat exports
  window.RenderHighlight = Object.assign(window.RenderHighlight || {}, { tryGraphInlineHighlight, setNodeHighlightsOnly, animateStep });
})();
