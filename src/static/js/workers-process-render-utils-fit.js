// Workers Process - Render Utils (fit + sizing logs) <7KB
(function(){
  function _san(s){ return String(s||'').replace(/[^A-Za-z0-9_]/g,'').toLowerCase(); }

  function logMermaidSizes(label){
    try{
      const graph = document.getElementById('processGraph');
      const overlay = document.getElementById('processOverlay');
      const content = overlay?.querySelector('.process-content');
      const body = overlay?.querySelector('.process-body');
      const wrap = graph?.querySelector('.mermaid-graph');
      const svg = wrap?.querySelector('svg');
      const r = (el)=> el? el.getBoundingClientRect(): {width:0,height:0};
      const cs = (el)=> el? window.getComputedStyle(el): null;
      const out = { label,
        overlay: r(overlay), content: r(content), body: r(body),
        processGraph: r(graph), mermaidGraph: r(wrap), svg: r(svg),
        svgAttrs: svg? { widthAttr: svg.getAttribute('width'), heightAttr: svg.getAttribute('height'), viewBox: svg.getAttribute('viewBox'), preserveAspectRatio: svg.getAttribute('preserveAspectRatio') }: null,
        svgStyle: svg? { width: cs(svg)?.width, height: cs(svg)?.height, maxHeight: cs(svg)?.maxHeight, maxWidth: cs(svg)?.maxWidth }: null };
      console.info('[MMD:SIZE]', out);
    }catch(e){ console.warn('[MMD:SIZE] failed', e); }
  }

  function fitViewBoxToVisible(svgEl, pad = 4){
    try{
      if (!svgEl) return;
      // Collect targets
      const nodes = Array.from(svgEl.querySelectorAll('g.node[id]'));
      const edges = Array.from(svgEl.querySelectorAll('g.edgePath path, g.edgePaths path, path[marker-end], path[class*="flowchart-link"], path[class*="edge" ]'));
      let targets = nodes.concat(edges);

      let minX=Infinity, minY=Infinity, maxX=-Infinity, maxY=-Infinity, count=0;
      function acc(bb){ if (!bb || !isFinite(bb.width) || !isFinite(bb.height) || bb.width<=0 || bb.height<=0) return; if (bb.x < minX) minX = bb.x; if (bb.y < minY) minY = bb.y; if (bb.x + bb.width > maxX) maxX = bb.x + bb.width; if (bb.y + bb.height > maxY) maxY = bb.y + bb.height; count++; }

      // Main pass
      targets.forEach(el => { try{ acc(el.getBBox()); }catch(_){ } });

      // Fallback 1: try group containers
      if (!count){
        try{
          const gs = Array.from(svgEl.querySelectorAll('svg > g, g'));
          for (let i=0;i<gs.length;i++){ try{ acc(gs[i].getBBox()); }catch(_){ } }
        }catch(_){ }
      }

      if (!count || !isFinite(minX) || !isFinite(minY) || !isFinite(maxX) || !isFinite(maxY)){
        console.warn('[MMD:FIT2] no targets found; skipping viewBox fit');
        return;
      }

      const x = Math.max(0, minX - pad);
      const y = Math.max(0, minY - pad);
      const w = Math.max(1, (maxX - minX) + pad*2);
      const h = Math.max(1, (maxY - minY) + pad*2);
      svgEl.setAttribute('viewBox', `${x} ${y} ${w} ${h}`);
      // Align left to avoid central blank margins
      svgEl.setAttribute('preserveAspectRatio', 'xMinYMid meet');
      console.info('[MMD:FIT2]', { countNodes: nodes.length, countEdges: edges.length, fitted:{x,y,w,h}, pad });
    }catch(e){ console.warn('[MMD:FIT2] failed', e); }
  }

  function ensureSvgFullsize(svgEl){
    try{
      if (!svgEl) return;
      // Force size to fill container
      svgEl.setAttribute('width','100%');
      svgEl.setAttribute('height','100%');
      svgEl.setAttribute('preserveAspectRatio','xMidYMid meet');
      svgEl.style.width = '100%'; svgEl.style.height = '100%';
      svgEl.style.maxHeight = '100%'; svgEl.style.maxWidth = '100%';
      const wrap = svgEl.closest('.mermaid-graph');
      if (wrap){ wrap.style.height = '100%'; wrap.style.width = '100%'; wrap.style.position = wrap.style.position || 'relative'; }
      logMermaidSizes('after ensureSvgFullsize');
    }catch(_){ }
  }

  window.RenderFit = { _san, logMermaidSizes, fitViewBoxToVisible, ensureSvgFullsize };
})();
