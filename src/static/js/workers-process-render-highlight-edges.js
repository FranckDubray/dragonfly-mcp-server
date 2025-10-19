
// Workers Process - Render Highlight (edges styling and index, <7KB)
(function(){
  const SH = window.__RenderHLShared || {};

  function selectAllEdgePaths(svg){
    return Array.from(svg.querySelectorAll('g.edgePath path, g.edgePaths path, path[marker-end], path[class*="flowchart-link"], path[class*="edge"]'));
  }

  function resetEdgesToDefault(svg){
    try{
      selectAllEdgePaths(svg).forEach(p => {
        try{ p.style.removeProperty('stroke'); }catch(_){ }
        try{ p.style.removeProperty('stroke-width'); }catch(_){ }
        try{ p.style.removeProperty('stroke-opacity'); }catch(_){ }
        try{ p.style.removeProperty('vector-effect'); }catch(_){ }
        try{ p.removeAttribute('stroke'); }catch(_){ }
        try{ p.removeAttribute('stroke-width'); }catch(_){ }
        try{ p.removeAttribute('stroke-opacity'); }catch(_){ }
      });
    }catch(_){ }
  }

  function buildEdgeIndex(svg){
    const idx = new Map();
    try{
      const pathEls = selectAllEdgePaths(svg);
      const nodeGs = Array.from(svg.querySelectorAll('g.node[id]'));
      const nodesMeta = nodeGs.map(g => ({ id: g.id, idSan: (SH.sanitizeNoUnderscore?.(g.id)||g.id.replace(/[^A-Za-z0-9]/g,'')).toLowerCase(), el: g }));
      function resolveNodeIdFromToken(tok){
        const tSan = (SH.sanitizeNoUnderscore?.(tok) || String(tok||'').replace(/[^A-Za-z0-9]/g,'')).toLowerCase();
        if (!tSan) return '';
        const cand = nodesMeta.find(n => n.idSan === tSan) || nodesMeta.find(n => n.id.toLowerCase().endsWith(String(tok||'').toLowerCase()));
        return cand ? cand.id : '';
      }
      function nodeCenters(){
        return nodeGs.map(g => { try{ const bb=g.getBBox(); return { id:g.id, cx: bb.x + bb.width/2, cy: bb.y + bb.height/2 }; } catch(_){ return null; } }).filter(Boolean);
      }
      const centers = nodeCenters();
      function nearestId(pt){ let best=null,bd=1e18; for (const c of centers){ const dx=c.cx-pt.x, dy=c.cy-pt.y, d=dx*dx+dy*dy; if (d<bd){ bd=d; best=c; } } return best? best.id: ''; }

      pathEls.forEach((p) => {
        const g = p.closest('g.edgePath, g.edgePaths');
        const cls = [g?.getAttribute('class')||'', p.getAttribute('class')||''].join(' ').trim();
        let a='', b='';
        try{
          const mS = cls.match(/\bLS-([^\s]+)/); const mE = cls.match(/\bLE-([^\s]+)/);
          const tS = mS?mS[1]:''; const tE = mE?mE[1]:'';
          if (tS && tE){ const rS = resolveNodeIdFromToken(tS); const rE = resolveNodeIdFromToken(tE); if (rS && rE){ a=rS; b=rE; } }
        }catch(_){ }
        if (!(a && b)){
          try{ const len=p.getTotalLength(); const p0=p.getPointAtLength(Math.max(0, Math.min(2,len))); const p1=p.getPointAtLength(Math.max(0,len-2)); const r0=nearestId(p0), r1=nearestId(p1); if (r0 && r1 && r0!==r1){ a=r0; b=r1; } }catch(_){ }
        }
        if (a && b){
          const key = `${a}=>${b}`;
          (idx.get(key)||idx.set(key,[]).get(key)).push(p);
          // NEW: annotate path with a stable df-e-<aSan>__<bSan> class for later selection (retry labels, etc.)
          try{
            const aSan = ((window.RenderUtils && typeof RenderUtils.sanitizeId==='function') ? RenderUtils.sanitizeId(a) : String(a)).toLowerCase();
            const bSan = ((window.RenderUtils && typeof RenderUtils.sanitizeId==='function') ? RenderUtils.sanitizeId(b) : String(b)).toLowerCase();
            if (aSan && bSan){ p.classList.add(`df-e-${aSan}__${bSan}`); }
          }catch(_){ }
        }
      });
    }catch(_){ }
    return idx;
  }

  function getEdgePathsDirected(svg, fromLabel, toLabel){
    try{
      const from = (SH.findNodeByLabel?.(svg, String(fromLabel))||{}).g?.id; if (!from) return [];
      const to   = (SH.findNodeByLabel?.(svg, String(toLabel))||{}).g?.id; if (!to) return [];
      const idx = buildEdgeIndex(svg);
      return idx.get(`${from}=>${to}`) || [];
    }catch(_){ return []; }
  }

  function setEdgeLevel(fromLabel, toLabel, level){
    try{
      const svg = document.querySelector('#processGraph svg'); if (!svg) return 0;
      const paths = getEdgePathsDirected(svg, fromLabel, toLabel);
      if (!paths.length) return 0;
      const cfg = (lvl)=>{
        if (lvl==='head') return { color:'#059669', width:6 };
        if (lvl==='mid')  return { color:'#10b981', width:3 };
        if (lvl==='tail') return { color:'#a7f3d0', width:2 };
        return null; // clear
      };
      const c = cfg(level);
      let n=0;
      if (c){ paths.forEach(p => { SH.styleOnePathAndMarker?.(svg, p, c.color, c.width); n++; }); }
      else { // clear
        paths.forEach(p => {
          try{ p.style.removeProperty('stroke'); p.style.removeProperty('stroke-width'); p.style.removeProperty('stroke-opacity'); p.removeAttribute('stroke'); p.removeAttribute('stroke-width'); p.removeAttribute('stroke-opacity'); }catch(_){ }
        });
      }
      return n;
    }catch(_){ return 0; }
  }

  function styleHeadEdge(trail){
    try{
      const svg = document.querySelector('#processGraph svg'); if (!svg) return 0;
      if (!Array.isArray(trail) || trail.length<2){ return 0; }
      const fromLbl = String(trail[0]||'');
      const toLbl   = String(trail[1]||'');
      return setEdgeLevel(fromLbl, toLbl, 'head');
    }catch(_){ return 0; }
  }

  function styleTrailEdges(trail){
    try{
      const svg = document.querySelector('#processGraph svg'); if (!svg) return 0;
      if (!Array.isArray(trail) || trail.length<2) return 0;
      let count=0;
      for (let i=0;i<trail.length-1;i++){
        count += setEdgeLevel(trail[i], trail[i+1], 'mid') || 0;
      }
      return count;
    }catch(_){ return 0; }
  }

  window.RenderHighlight = Object.assign(window.RenderHighlight || {}, { styleHeadEdge, setEdgeLevel, getEdgePathsDirected, resetEdgesToDefault, styleTrailEdges });
})();
