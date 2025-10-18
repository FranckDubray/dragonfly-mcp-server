// Workers Process - Render Highlight (shared helpers, <7KB)
(function(){
  function sanitizeKeepUnderscore(s){ return String(s||'').trim(); }
  function sanitizeNoUnderscore(s){ return String(s||'').replace(/[^A-Za-z0-9]/g,'').toLowerCase(); }
  function coreFromNodeId(id){
    try{ let s = String(id||''); const ix = s.indexOf('-'); if (ix >= 0) s = s.slice(ix+1); return s.replace(/-\d+$/,''); }
    catch(_){ return String(id||''); }
  }

  function findNodeByLabel(svg, label){
    if (!svg || !label) return null;
    const raw = String(label), wantKeep = sanitizeKeepUnderscore(raw), wantNoUnd = sanitizeNoUnderscore(raw);
    let g = svg.querySelector(`g.node[id="${CSS.escape(raw)}"]`); if (g) return { g, mode: 'exact-id' };
    const nodes = Array.from(svg.querySelectorAll('g.node[id]'));
    let bySuffix = nodes.find(n => (n.id||'').endsWith(wantKeep)); if (bySuffix) return { g: bySuffix, mode: 'suffix-keep' };
    bySuffix = nodes.find(n => (n.id||'').endsWith(raw)); if (bySuffix) return { g: bySuffix, mode: 'suffix-raw' };
    const wantNoPref = wantKeep.toLowerCase();
    for (const n of nodes){ const core = coreFromNodeId(n.id).toLowerCase(); const coreNoUnd = core.replace(/[^A-Za-z0-9]/g,''); if (core === wantNoPref) return { g: n, mode: 'core' }; if (coreNoUnd === wantNoUnd) return { g: n, mode: 'core-noUnd' }; }
    for (const n of nodes){ const t = n.querySelector('text') || n.querySelector('foreignObject div') || n.querySelector('foreignObject span'); const txt = t && (t.textContent||t.innerText) || ''; if (sanitizeNoUnderscore(txt) === wantNoUnd) return { g: n, mode: 'text' }; }
    return null;
  }

  function ensureHighlightStyle(svg){
    let st = svg.querySelector('#mmd-hl-style');
    if (!st){
      st = document.createElement('style'); st.id = 'mmd-hl-style';
      // Palette verte (trail): niveaux 0..9 du plus contrasté au plus léger
      const lv = [
        { s:'#065f46', f:'#047857', t:'#ffffff', w:3 },  // emerald-800/700
        { s:'#047857', f:'#059669', t:'#ffffff', w:3 },  // emerald-700/600
        { s:'#059669', f:'#10b981', t:'#ffffff', w:2.5 },// emerald-600/500
        { s:'#10b981', f:'#34d399', t:'#064e3b', w:2.5 },// emerald-500/400 + dark text
        { s:'#34d399', f:'#6ee7b7', t:'#064e3b', w:2 },  // emerald-400/300
        { s:'#6ee7b7', f:'#a7f3d0', t:'#064e3b', w:2 },  // emerald-300/200
        { s:'#a7f3d0', f:'#d1fae5', t:'#065f46', w:2 },  // emerald-200/100
        { s:'#bbf7d0', f:'#dcfce7', t:'#065f46', w:2 },  // green-200/100 alt
        { s:'#86efac', f:'#bbf7d0', t:'#065f46', w:2 },  // green-300/200
        { s:'#4ade80', f:'#86efac', t:'#065f46', w:2 }   // green-400/300
      ];
      const rows = [];
      for (let i=0;i<lv.length;i++){
        rows.push(`g.node.node-hl-${i} rect, g.node.node-hl-${i} path, g.node.node-hl-${i} ellipse, g.node.node-hl-${i} polygon, g.node.node-hl-${i} circle { stroke:${lv[i].s} !important; stroke-width:${lv[i].w}px !important; fill:${lv[i].f} !important; }`);
      }
      for (let i=0;i<lv.length;i++){
        rows.push(`g.node.node-hl-${i} text { fill:${lv[i].t} !important; font-weight:700 !important; }`);
      }
      for (let i=0;i<lv.length;i++){
        rows.push(`g.node.node-hl-${i} foreignObject div, g.node.node-hl-${i} foreignObject span { background-color:${lv[i].f} !important; color:${lv[i].t} !important; }`);
      }
      st.textContent = rows.join('\n'); svg.appendChild(st);
    }
  }

  function ensureColoredMarker(svg, baseId, color, width){
    try{ const defs = svg.querySelector('defs'); if (!defs) return baseId; const key = `${baseId}-${String(color).replace('#','')}-${Math.round((Number(width)||1)*10)}`; if (svg.querySelector(`#${CSS.escape(key)}`)) return key; const base = svg.querySelector(`#${CSS.escape(baseId)}`); if (!base) return baseId; const clone = base.cloneNode(true); clone.setAttribute('id', key); try{ clone.setAttribute('markerUnits','strokeWidth'); }catch(_){ } try{ const w = Number(width)||1; const mw = Math.max(6, Math.min(18, Math.round(6+w*2))); clone.setAttribute('markerWidth', String(mw)); clone.setAttribute('markerHeight', String(mw)); }catch(_){ } clone.querySelectorAll('path').forEach(mp=>{ mp.setAttribute('fill', color); mp.setAttribute('stroke', color); mp.style.fill=color; mp.style.stroke=color; }); defs.appendChild(clone); return key; }catch(_){ return baseId; }
  }
  function styleOnePathAndMarker(svg, p, color, width){
    const g = p.closest('g.edgePath, g.edgePaths'); const sig = { gClass:g?.getAttribute('class')||'', gId:g?.id||'', pathId:p.id||'' };
    p.style.setProperty('stroke', color, 'important'); p.style.setProperty('stroke-width', (Number(width)||1)+'px', 'important'); p.style.setProperty('stroke-opacity', '1', 'important'); p.style.setProperty('vector-effect', 'none', 'important');
    p.setAttribute('stroke', color); p.setAttribute('stroke-width', String(width)); p.setAttribute('stroke-opacity', '1');
    const m = (p.getAttribute('marker-end')||'').match(/url\(#(.+?)\)/); if (m && m[1]){ const newId = ensureColoredMarker(svg, m[1], color, width); p.setAttribute('marker-end', `url(#${newId})`); }
    if (window.__DF_DEBUG) console.debug('[EDGE:thickness] changed', sig);
  }

  const shared = { sanitizeKeepUnderscore, sanitizeNoUnderscore, coreFromNodeId, findNodeByLabel, ensureHighlightStyle, ensureColoredMarker, styleOnePathAndMarker };
  window.__RenderHLShared = Object.assign(window.__RenderHLShared || {}, shared);
  window.RenderHighlight = Object.assign(window.RenderHighlight || {}, shared);
})();
