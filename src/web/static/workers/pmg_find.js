// Process Modal Graph — find helpers (IDs and text matching)

export function sanitizeId(id){
  return String(id||'').replace(/[^A-Za-z0-9_]/g,'_');
}

export function splitNode(node){
  const s = String(node||'');
  const p = s.split('::');
  return { sg: p[0]||'', step: p[1]||'' };
}

export function isSymbolic(node){
  if (!node) return true;
  if (node === 'START' || node === 'END') return true;
  if (node.includes('::')){
    const step = (node.split('::')[1]||'').toLowerCase();
    if (['success','fail','retry','retry_exhausted'].includes(step)) return true;
  }
  return false;
}

function normText(x){
  return String(x||'')
    .toLowerCase().trim()
    .replace(/^step[\s_\-]+/,'')
    .replace(/[\s_\-]+/g,'_');
}

// Tolerant search of the <g> group corresponding to a node ID
export function findNodeG(svg, node){
  try{
    if (!svg || !node) return null;

    // Mermaid v10 pattern: flowchart-<diagramId>-<nodeId>
    const diag = svg.getAttribute('data-mermaid-id') || '';
    const nodeSan = sanitizeId(node);
    if (diag){
      const fullId = `flowchart-${diag}-${nodeSan}`;
      const strict = svg.getElementById?.(fullId) || (typeof document!=='undefined' && document.getElementById(fullId));
      if (strict) return strict.closest('g') || strict;
    }

    // Fallbacks (older pattern or unknown diag)
    const idSan = nodeSan;
    let g = svg.getElementById?.(idSan) || svg.getElementById?.(node);
    if (g) return g.closest('g');

    const { step } = splitNode(node);
    if (step){
      const stepSan = sanitizeId(step);
      // try suffix and contains matches on id
      g = svg.querySelector(`g[id$="_${stepSan}"]`)
        || svg.querySelector(`g[id$="${stepSan}"]`)
        || svg.querySelector(`g[id*="_${stepSan}"]`)
        || svg.querySelector(`g[id*="${stepSan}"]`);
      if (g) return g.closest('g');

      // broader text search: text and tspan (normalized)
      const texts = svg.querySelectorAll('g text, g tspan');
      const needle = normText(step);
      for (const t of texts){
        try{
          const v = normText(t.textContent||'');
          if (!v) continue;
          if (v.includes(needle) || v.endsWith(needle)){
            const gp = t.closest('g');
            if (gp && gp.getAttribute('id')) return gp;
          }
        }catch{}
      }
    }
    return null;
  }catch{ return null; }
}
