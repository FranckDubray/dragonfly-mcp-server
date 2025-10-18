
// Workers Process - Render Core (render orchestration + cadence 1Hz)
(function(){
  const TARGET_MS = 1000; // 1Hz
  let __renderInFlight = false;
  let __lastStart = 0;
  let __pending = null;

  function cleanupOldGraph(container){
    try{
      const oldSvg = container.querySelector('.mermaid-graph svg');
      if (oldSvg && oldSvg.__df_pz){
        try{ oldSvg.__df_pz.destroy(); }catch(_){ }
        try{ oldSvg.__df_pz = null; }catch(_){ }
      }
    }catch(_){ }
  }

  async function doRender(container, source){
    if (!window.mermaid?.render) { await RenderUtils.ensureMermaid(); }
    if (!window.mermaid?.render) throw new Error('Mermaid non chargé');
    const id = 'mmd-' + Math.random().toString(36).slice(2);
    const { svg } = await window.mermaid.render(id, source);

    // Cleanup ancien SVG + panzoom avant remplacement
    cleanupOldGraph(container);

    const slot = document.createElement('div');
    slot.className = 'mermaid-graph';
    slot.style.height = '100%';
    slot.style.width = '100%';
    slot.innerHTML = svg;
    container.innerHTML = '';
    container.appendChild(slot);
    const svgEl = slot.querySelector('svg');

    // Debug: compter noeuds/arrêtes + viewBox
    try {
      const n = svgEl.querySelectorAll('g.node[id]').length;
      const e = svgEl.querySelectorAll('g.edgePath path, g.edgePaths path').length;
      const vb = svgEl.getAttribute('viewBox');
      console.info('[MMD:NODES]', { nodes: n, edges: e, viewBox: vb });
    } catch(_) {}

    RenderFit.ensureSvgFullsize(svgEl);
    RenderFit.fitViewBoxToVisible(svgEl, 4);
    try{ RenderUtils.attachNodeClickBridge(container); }catch(_){ }
    try{ RenderUtils.logGraphNodeIds(slot); }catch(_){ }
    RenderFit.logMermaidSizes('after doRender (fit)');
    await RenderPanZoom.loadSvgPanZoom();
    RenderPanZoom.ensurePanZoom(svgEl);
  }

  async function renderMermaid(container, source, currentNode){
    if (__renderInFlight){ __pending = { container, source, currentNode }; return; }
    __renderInFlight = true; __lastStart = performance.now();

    await RenderUtils.ensureMermaid();
    if (!container){ __renderInFlight=false; return; }
    const prevSrc = container.getAttribute('data-src') || '';
    const prevNode = container.getAttribute('data-node') || '';
    const prevTrailStr = container.getAttribute('data-trail') || '';
    const normalized = RenderUtils.normalizeMermaidSource(source);

    const trail = (window.WP && Array.isArray(WP.hlTrail) && WP.hlTrail.length)
      ? WP.hlTrail.slice(0, Math.max(1, Math.min(10, window.WP?.trailN||3)))
      : RenderUtils.trailFromReplay(currentNode);
    const trailStr = JSON.stringify(trail.map(RenderUtils.sanitizeId));

    const srcChanged = prevSrc !== normalized;
    const nodeChanged = prevNode !== String(currentNode||'');
    const trailChanged = prevTrailStr !== trailStr;

    if (!srcChanged && (nodeChanged || trailChanged)){
      try{
        container.setAttribute('data-node', String(currentNode||''));
        container.setAttribute('data-trail', trailStr);
        const ok = window.RenderHighlight?.tryGraphInlineHighlight?.(trail);
        if (ok){ __renderInFlight = false; return; }
      }catch(_){ }
    }

    if (!(srcChanged || nodeChanged || trailChanged)){
      try { window.RenderHighlight?.tryGraphInlineHighlight(trail); } catch(_){ }
      __renderInFlight = false; return;
    }

    const withHL = RenderUtils.applyTrailHighlights(normalized, trail);

    try { await doRender(container, withHL); }
    catch (err) { console.error('[MMD] error', err); try { RenderUtils.renderError(container, err); } catch(_){} }
    finally {
      container.setAttribute('data-src', normalized);
      const elapsed = performance.now() - __lastStart; const rest = Math.max(0, TARGET_MS - elapsed);
      await RenderUtils.sleep(rest);
      __renderInFlight = false;
      if (__pending){ const p = __pending; __pending = null; try{ await renderMermaid(p.container, p.source, p.currentNode); }catch(_){ } }
    }
  }

  async function renderMermaidLegacy(mermaidText, containerEl, currentNode){ return renderMermaid(containerEl, mermaidText, currentNode); }

  window.DFMermaid = { renderMermaid, normalizeMermaidSource: RenderUtils.normalizeMermaidSource };
  window.renderMermaid = renderMermaidLegacy;
  window.tryGraphInlineHighlight = (trail)=>window.RenderHighlight?.tryGraphInlineHighlight(trail);
})();
