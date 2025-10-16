

// Mermaid rendering helper with robust normalization and legacy signature support + node click bridge
(() => {
  const loadMermaidFromCdn = () => new Promise((resolve, reject) => {
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

  const ensureMermaid = async () => {
    if (window.mermaid?.render) return;
    if (typeof window.ensureMermaid === 'function') {
      try { await window.ensureMermaid(); } catch(_){}
      return;
    }
    await loadMermaidFromCdn().catch(()=>{});
  };

  function normalizeMermaidSource(src) {
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

  function applyHighlight(source, nodeId) {
    const nid = String(nodeId || '').trim();
    if (!nid) return source;
    const safe = nid.replace(/[^A-Za-z0-9_]/g, '');
    if (!safe) return source;
    const extra = `\n%% highlight current node\nclassDef __hl stroke:#2563eb,stroke-width:3px,fill:#dbeafe;\nclass ${safe} __hl;`;
    return source + extra;
  }

  function renderError(container, err) {
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
      // Mermaid uses node ids as <g id="nodeId" class="node"> …
      svg.querySelectorAll('g.node[id]').forEach((g) => {
        const id = g.getAttribute('id');
        g.style.cursor = 'pointer';
        g.addEventListener('click', (e) => {
          window.dispatchEvent(new CustomEvent('wp-node-select', { detail: { node: id } }));
          // Synchronise timeline highlight when clicking in the graph
          try{ if (typeof highlightTimelineNode === 'function') highlightTimelineNode(String(id||''), /*smooth=*/true); }catch(_){ }
        });
      });
    }catch(_){ }
  }

  async function renderMermaidNew(container, source, currentNode) {
    await ensureMermaid();
    if (!container) return;
    // Avoid re-render when nothing changed (source + node)
    const prevSrc = container.getAttribute('data-src') || '';
    const prevNode = container.getAttribute('data-node') || '';
    const normalized = normalizeMermaidSource(source);
    const withHL = applyHighlight(normalized, currentNode);
    if (prevSrc === normalized && prevNode === String(currentNode||'')){
      return; // no-op
    }
    container.setAttribute('data-src', normalized);
    container.setAttribute('data-node', String(currentNode||''));

    container.innerHTML = '';
    try {
      if (!window.mermaid?.render) {
        // Retry once after a tiny delay if mermaid is still booting
        await new Promise(r => setTimeout(r, 150));
        if (!window.mermaid?.render) throw new Error('Mermaid non chargé');
      }
      const id = 'mmd-' + Math.random().toString(36).slice(2);
      const { svg } = await window.mermaid.render(id, withHL);
      const slot = document.createElement('div');
      slot.className = 'mermaid-graph';
      slot.innerHTML = svg;
      container.appendChild(slot);
      attachNodeClickBridge(container);
    } catch (err) {
      console.error('[Mermaid] render failed:', err);
      renderError(container, err);
    }
  }

  async function renderMermaidLegacy(mermaidText, containerEl, currentNode){
    return renderMermaidNew(containerEl, mermaidText, currentNode);
  }

  window.DFMermaid = { renderMermaid: renderMermaidNew, normalizeMermaidSource };
  window.renderMermaid = renderMermaidLegacy;
})();
