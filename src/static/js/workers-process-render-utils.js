
// Workers Process - Render Utils (ensure, normalize, helpers)
(function(){
  function sleep(ms){ return new Promise(r=>setTimeout(r, ms)); }

  function loadMermaidFromCdn(){
    return new Promise((resolve, reject)=>{
      try {
        const existing = document.querySelector('script[data-mermaid]');
        if (existing && window.mermaid) return resolve();
        const s = document.createElement('script');
        s.src = 'https://unpkg.com/mermaid@10/dist/mermaid.min.js';
        s.async = true; s.defer = true; s.setAttribute('data-mermaid','1');
        s.onload = () => { try { window.mermaid.initialize({ startOnLoad:false, theme:'neutral', securityLevel:'loose' }); } catch(_){} resolve(); };
        s.onerror = reject;
        document.head.appendChild(s);
      } catch (e) { reject(e); }
    });
  }

  async function ensureMermaid(){
    if (window.mermaid?.render) return;
    if (typeof window.ensureMermaid === 'function'){
      try { await window.ensureMermaid(); } catch(_){ }
    }
    for (let i=0;i<10 && !window.mermaid?.render;i++){ await sleep(50); }
    if (!window.mermaid?.render){
      try { await loadMermaidFromCdn(); } catch(_){ }
      for (let i=0;i<10 && !window.mermaid?.render;i++){ await sleep(50); }
    }
  }

  function normalizeMermaidSource(src){
    if (!src) return '';
    let out = String(src)
      .replace(/\r\n?/g, '\n')
      .replace(/\\n/g, '\n')
      .replace(/\\t/g, ' ')
      .trim();
    if (!/^\s*(flowchart|graph)\s/i.test(out)) out = 'flowchart TD\n' + out;
    out = out.replace(/(\S)\s-\s(\S)/g, (_, a, b) => `${a} --> ${b}`);
    out = out.replace(/\s*-\s*$/gm, '');
    out = out.replace(/\s*--\>\s*$/gm, '');
    out = out.replace(/-\s*-\s*>/g, '-->');
    out = out.replace(/(\[[^\]]*\"[^\]]*\])|(\([^\)]*\"[^\)]*\))|(\{[^\}]*\"[^\}]*\})/g, m => m.replace(/"/g, "'"));
    return out;
  }

  function sanitizeId(s){ return String(s||'').replace(/[^A-Za-z0-9_]/g,''); }

  function clamp(n, a, b){ n = Number(n)||0; return Math.max(a, Math.min(b, n)); }

  function currentTrailCount(){
    try{ return clamp(window.WP?.trailN ?? 3, 1, 10); } catch(_){ return 3; }
  }

  function trailFromReplay(currentNode){
    try{
      const seq = (window.WP && Array.isArray(WP.replaySeq)) ? WP.replaySeq : [];
      const count = currentTrailCount();
      if (!seq.length) return currentNode ? [currentNode] : [];
      let ix = (typeof WP.replayIx === 'number' && WP.replayIx >= 0) ? WP.replayIx : -1;
      const needle = String(currentNode||'');
      if (ix < 0) {
        ix = needle ? seq.lastIndexOf(needle) : (seq.length - 1);
        if (ix < 0) ix = seq.length - 1;
      }
      const out = [];
      for (let k=0; k<count; k++){ const v = seq[ix-k]; if (v) out.push(v); }
      return out.length ? out : (needle ? [needle] : []);
    }catch(_){ return currentNode ? [currentNode] : []; }
  }

  function injectCommonStyles(svg){
    try{
      if (!svg) return;
      let st = svg.querySelector('#mmd-common-style');
      if (!st){
        st = document.createElement('style');
        st.id = 'mmd-common-style';
        // IMPORTANT: ne force plus la couleur des flèches; laisse le thème Mermaid décider.
        // On peut néanmoins s'assurer d'un rendu propre des labels si besoin.
        st.textContent = [
          // 'g.edgePath path { vector-effect: non-scaling-stroke; }', // optionnel
          'g.edgeLabel text { fill: currentColor; }'
        ].join('\n');
        svg.appendChild(st);
      }
    }catch(_){ }
  }

  function renderError(container, err){
    if (!container) return;
    container.innerHTML = '';
    const wrap = document.createElement('div');
    wrap.className = 'mermaid-error';
    wrap.style.cssText = 'background:#2b2b2b;color:#ffd2d2;border:1px solid #7a2a2a;border-radius:8px;padding:12px;font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;font-size:12px;';
    const title = document.createElement('div');
    title.textContent = 'Diagramme indisponible';
    title.style.cssText = 'font-weight:600;margin-bottom:6px;color:#fff;';
    const msg = document.createElement('div');
    const detail = (err && (err.message || err.toString())) || 'Erreur Mermaid';
    msg.textContent = detail;
    msg.style.cssText = 'opacity:.9;';
    wrap.append(title, msg);
    container.appendChild(wrap);
  }

  function attachNodeClickBridge(container){
    try{
      const svg = container.querySelector('svg');
      if (!svg) return;
      svg.querySelectorAll('g.node[id]').forEach((g) => {
        const id = g.getAttribute('id');
        g.style.cursor = 'pointer';
        g.addEventListener('click', () => {
          window.dispatchEvent(new CustomEvent('wp-node-select', { detail: { node: id } }));
          try{ if (typeof highlightTimelineNode === 'function') highlightTimelineNode(String(id||''), /*smooth=*/true); }catch(_){ }
        });
      });
    }catch(_){ }
  }

  function logGraphNodeIds(svgRoot){
    try{
      const svg = svgRoot && (svgRoot.tagName==='svg' ? svgRoot : svgRoot.querySelector('svg'));
      if (!svg) return;
      const ids = Array.from(svg.querySelectorAll('g.node[id]')).map(n => n.getAttribute('id')||'');
      console.info('[MMD] graph node ids', ids.slice(0,20), ids.length>20?`(+${ids.length-20} more)`: '');
    }catch(_){ }
  }

  // NO-OP highlighter preprocessor: keep source unchanged, highlight done inline later
  function applyTrailHighlights(src, trail){ return String(src||''); }

  window.RenderUtils = {
    sleep,
    ensureMermaid,
    loadMermaidFromCdn,
    normalizeMermaidSource,
    sanitizeId,
    trailFromReplay,
    injectCommonStyles,
    renderError,
    attachNodeClickBridge,
    logGraphNodeIds,
    clamp,
    currentTrailCount,
    applyTrailHighlights
  };
})();
