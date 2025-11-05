






















// SVG + Mermaid helpers (single source of truth)

// Sanitize ids: keep [A-Za-z0-9_] only
export function sanitizeId(id){
  return String(id||'').replace(/[^A-Za-z0-9_]/g,'_').replace(/_+/g,'_');
}

// Render Mermaid to an <svg> element (Mermaid v10 ESM)
export async function renderMermaid(mermaidText){
  if (!window.mermaid) {
    const mod = await import('https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs');
    const lib = mod && (mod.default || mod);
    if (!lib || typeof lib.initialize !== 'function') {
      const err = document.createElement('div');
      err.className = 'panel';
      const h3 = document.createElement('h3'); h3.textContent = 'Mermaid — load error';
      const pre = document.createElement('pre'); pre.className='io-pre'; pre.textContent = 'Failed to load Mermaid ESM (no initialize)';
      err.append(h3, pre);
      return err;
    }
    window.mermaid = lib;
  }

  const cfg = {
    startOnLoad: false,
    logLevel: 4,
    theme: 'default',
    themeVariables: {
      fontSize: '12px',
      labelFontSize: '12px',
      padding: 10,
      rectPadding: 10,
      nodeSpacing: 20,
      rankSpacing: 28,
      arrowSize: 1,
      borderRadius: 4,
      labelPadding: 5,
    },
    flowchart: {
      curve: 'stepAfter',
      useMaxWidth: false,
      htmlLabels: true,
    }
  };

  try{ window.mermaid.initialize(cfg); }catch{}

  const el = document.createElement('div');
  const id = 'm_'+Math.random().toString(36).slice(2);

  // Parse first for readable errors
  try{ window.mermaid.parse(mermaidText); }
  catch(parseError){
    const err = document.createElement('div');
    err.className = 'panel';
    const h3 = document.createElement('h3'); h3.textContent = 'Mermaid — parse error';
    const pre = document.createElement('pre'); pre.className='io-pre'; pre.textContent = String(parseError && parseError.message || parseError || 'Parse error');
    err.append(h3, pre);
    return err;
  }

  // Render to SVG
  try{
    const { svg } = await window.mermaid.render(id, mermaidText);
    el.innerHTML = svg;
  }catch(renderError){
    const err = document.createElement('div');
    err.className = 'panel';
    const h3 = document.createElement('h3'); h3.textContent = 'Mermaid — render error';
    const pre = document.createElement('pre'); pre.className='io-pre'; pre.textContent = String(renderError && renderError.message || renderError || 'Render error');
    err.append(h3, pre);
    return err;
  }

  const svgEl = el.querySelector('svg');
  // Tag the diagram id for reliable selectors (flowchart-<id>-<node>)
  try{ svgEl.setAttribute('data-mermaid-id', id); }catch{}
  // Fit-to-height: ensure viewBox then let container manage height
  try{
    const wAttr = svgEl.getAttribute('width');
    const hAttr = svgEl.getAttribute('height');
    if (!svgEl.getAttribute('viewBox')){
      const w = (wAttr && parseFloat(wAttr)) || (svgEl.viewBox && svgEl.viewBox.baseVal && svgEl.viewBox.baseVal.width) || 1000;
      const h = (hAttr && parseFloat(hAttr)) || (svgEl.viewBox && svgEl.viewBox.baseVal && svgEl.viewBox.baseVal.height) || 600;
      if (isFinite(w) && isFinite(h)){
        svgEl.setAttribute('viewBox', `0 0 ${w} ${h}`);
      }
    }
    svgEl.removeAttribute('width');
    svgEl.removeAttribute('height');
    svgEl.setAttribute('preserveAspectRatio','xMidYMid meet');
    svgEl.style.height = '100%';
    svgEl.style.width = 'auto';
    svgEl.style.display = 'block';
  }catch{}

  svgEl.classList.add('graph-layer','enter');
  requestAnimationFrame(()=> svgEl.classList.add('enter-active'));
  return svgEl;
}

// Build a quick index of <g id> groups (fallback helper)
export function buildSvgIndex(svgRoot){
  const map = new Map();
  svgRoot.querySelectorAll('g[id]').forEach(g=>{
    const id = g.getAttribute('id')||'';
    if (!id) return;
    map.set(id, g);
  });
  return {
    get: (originalId)=> map.get(sanitizeId(originalId)) || map.get(originalId) || null,
    has: (originalId)=> !!(map.get(sanitizeId(originalId))||map.get(originalId)),
  };
}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
