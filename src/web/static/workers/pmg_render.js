




















// Process Modal Graph — render & wiring
import { renderMermaid } from './svg_map.js';
import { t } from './i18n.js';
import { skeleton } from './process_utils.js';
import { sanitizeId, findNodeG } from './pmg_find.js';
import { swapGraph } from './animations.js';

export async function loadGraph({ worker, dom, hl, state, onStatusKind }){
  const { currentKind, currentSubgraph } = state;
  let skel = null;
  try{
    // placeholder while loading (ne PAS supprimer l'ancien SVG, on laisse swapGraph gérer la transition)
    if (dom.status) dom.status.textContent = '';
    try{ skel = skeleton(); skel.className += ' pmg-skel'; dom.stage.appendChild(skel); }catch{}

    const include = { shapes: true, emojis: true, labels: true };
    const render = { mermaid: true, hide_start: false, hide_end: false };
    const graphReq = { kind: 'process', include, render };

    if (currentKind === 'overview'){
      graphReq.render.overview_subgraphs = true;
    } else if (currentKind === 'subgraph'){
      graphReq.kind = 'subgraph';
      const sg = String(currentSubgraph||'').trim();
      if (sg) graphReq.subgraphs = [sg];
    }
    if (window.__GV_DEBUG){ try{ console.debug('[PM RENDER] build graphReq', {kind: currentKind, subgraph: currentSubgraph, graphReq}); }catch{} }

    const payload = { tool: 'py_orchestrator', params: { operation: 'graph', worker_name: worker, graph: graphReq } };
    const r = await fetch('/execute', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    const js = await r.json();
    const res = (js && js.result) ? js.result : js;
    const mm = res && res.mermaid || '';

    if (!mm){
      // Erreur: nettoyer le skeleton et montrer le message (on retire le voile au prochain swap)
      try{ skel && skel.remove(); }catch{}
      if (dom.status){
        dom.status.className='error-text';
        dom.status.textContent = `${t('graph.mermaid_error_prefix','Mermaid — ')}${res && res.message || t('graph.unavailable','Graphe indisponible')}.`;
      }
      if (window.__GV_DEBUG){ try{ console.warn('[PM RENDER] empty mermaid', {status:res?.status, message:res?.message}); }catch{} }
      return null;
    }

    const svg = await renderMermaid(mm);
    // Désactiver toute transition locale du SVG (on gère via voile blanc)
    try{
      svg.classList.remove('enter','enter-active','exit','exit-active');
      svg.style.opacity = '1';
      svg.style.transform = 'none';
      svg.style.transition = 'none';
    }catch{}

    // Par défaut: occuper toute la hauteur disponible et laisser JS ajuster la largeur CSS
    svg.style.height = '100%';
    svg.style.display = 'block';
    svg.style.maxWidth = 'none';
    svg.style.margin = '0 auto'; // centrer si plus petit que la zone visible
    try{ svg.style.cursor = (currentKind==='overview') ? 'pointer' : 'default'; }catch{}

    // swap via voile blanc
    await swapGraph(dom.stage, svg);

    // retirer le skeleton une fois le swap fait
    try{ skel && skel.remove(); }catch{}

    // Mémoriser le viewBox initial pour les zooms manuels
    try{
      const vb = svg.viewBox && svg.viewBox.baseVal;
      if (vb && !svg.__initialViewBox){
        svg.__initialViewBox = { x: vb.x, y: vb.y, width: vb.width, height: vb.height };
      }
    }catch{}

    // Ajuster la largeur CSS de l'SVG en fonction du zoom (viewBox) et des dimensions du stage
    adjustSvgCssSize(dom.stage, svg);

    // Activer le drag-pan à la souris
    try{ modalEnablePan(dom.stage, svg); }catch{}

    // Reset scroll horizontal si le diagramme est plus petit que la zone visible
    try{
      const bb = svg.getBoundingClientRect();
      const st = dom.stage.getBoundingClientRect();
      if (bb.width <= st.width) dom.stage.scrollLeft = 0;
    }catch{}

    // Attach highlighter with tolerant getter powered by findNodeG (uses Mermaid v10 id pattern)
    hl.attach(svg, {
      get: (id)=> findNodeG(svg, id),
      has: (id)=> !!findNodeG(svg, id)
    });

    if (window.__GV_DEBUG){ try{ console.debug('[PM RENDER] attach HL', { diagramId: svg.getAttribute('data-mermaid-id')||'', kind: currentKind, subgraph: currentSubgraph }); }catch{} }

    // Back button
    try{
      if (dom.backBtn){
        if (currentKind === 'subgraph'){
          dom.backBtn.style.display = '';
          dom.backBtn.onclick = () => { onStatusKind('back'); };
        } else {
          dom.backBtn.style.display = 'none';
          dom.backBtn.onclick = null;
        }
      }
    }catch{}

    return svg;
  }catch(e){
    try{ skel && skel.remove(); }catch{}
    if (dom.status){
      dom.status.className='error-text';
      dom.status.textContent = `${t('graph.mermaid_error_prefix','Mermaid — ')}${(e && e.message) || t('graph.render_error','render error')}`;
    }
    if (window.__GV_DEBUG){ try{ console.warn('[PM RENDER] error', e); }catch{} }
    return null;
  }
}

function adjustSvgCssSize(stageEl, svg){
  try{
    const vb = svg.viewBox && svg.viewBox.baseVal; if (!vb) return;
    const ivb = svg.__initialViewBox || vb;
    const stH = stageEl.clientHeight || stageEl.offsetHeight || 0;
    const stW = stageEl.clientWidth || stageEl.offsetWidth || 0;
    if (!stH) return;

    // Base width from initial aspect ratio (fit-height)
    const baseWidth = Math.max(1, Math.round(stH * (ivb.width / Math.max(1, ivb.height))));
    // Zoom factor from viewBox (smaller vb.width => bigger factor)
    const factor = (ivb.width && vb.width) ? (ivb.width / vb.width) : 1;
    let pxWidth = Math.max(1, Math.round(baseWidth * factor));

    // Ne jamais laisser le SVG plus étroit que la zone visible: exploiter toute la largeur disponible
    if (stW) pxWidth = Math.max(pxWidth, stW);

    svg.style.width = pxWidth + 'px';
  }catch{}
}

export function wireSvgClicks(svg, state, goToSubgraph){
  svg.addEventListener('click', (e)=>{
    try{
      const g = e.target && e.target.closest && e.target.closest('g[id]');
      const gid = g && g.getAttribute && g.getAttribute('id');
      let label = '';
      try{ const tl = g && g.querySelector && (g.querySelector('text') || g.querySelector('tspan')); label = tl && tl.textContent ? String(tl.textContent).trim() : ''; }catch{}
      let derived = '';
      try{ if (!label && gid){ derived = gid.replace(/^.*?-/,'').replace(/-\d+$/,''); } }catch{}
      const candidate = label && !label.includes('::') ? label : (derived || '');
      if (window.__GV_DEBUG){ try{ console.debug('[PM CLICK]', {gid, label, derived, candidate, currentKind: state.currentKind}); }catch{} }
      if (state.currentKind === 'overview' && candidate){ goToSubgraph(candidate); }
    }catch(err){ try{ console.warn('[PROCESS MODAL] click handler error', err); }catch{} }
  });
}

// ====== Modal pan & zoom helpers ======
export function modalZoom(stageEl, delta){
  try{
    const svg = stageEl.querySelector('svg'); if (!svg) return;
    const vb = svg.viewBox && svg.viewBox.baseVal; if (!vb || vb.width<=0 || vb.height<=0) return;
    const factor = (1 + delta); // delta > 0 => zoom in
    const newW = vb.width / factor;
    const newH = vb.height / factor;
    const cx = vb.x + vb.width/2; const cy = vb.y + vb.height/2;
    const nx = cx - newW/2; const ny = cy - newH/2;
    svg.setAttribute('viewBox', `${nx} ${ny} ${newW} ${newH}`);
    // Ajuster la largeur CSS suite au zoom pour permettre le scroll horizontal
    adjustSvgCssSize(stageEl, svg);
  }catch{}
}

export function modalResetZoom(stageEl){
  try{
    const svg = stageEl.querySelector('svg'); if (!svg) return;
    const ivb = svg.__initialViewBox; const vb = svg.viewBox && svg.viewBox.baseVal;
    const base = ivb || (vb && {x:vb.x,y:vb.y,width:vb.width,height:vb.height});
    if (!base) return;
    svg.setAttribute('viewBox', `${base.x} ${base.y} ${base.width} ${base.height}`);
    adjustSvgCssSize(stageEl, svg);
  }catch{}
}

export function modalEnablePan(stageEl, svg){
  try{
    svg = svg || stageEl.querySelector('svg'); if (!svg) return;
    let dragging=false; let sx=0, sy=0; let startVb=null;
    const onDown = (e)=>{
      // Only left button
      if (e.button !== 0) return;
      const vb = svg.viewBox && svg.viewBox.baseVal; if (!vb) return;
      dragging=true; sx=e.clientX; sy=e.clientY; startVb={ x: vb.x, y: vb.y, width: vb.width, height: vb.height };
      svg.style.cursor='grabbing';
      e.preventDefault();
    };
    const onMove = (e)=>{
      if (!dragging) return;
      const vb = svg.viewBox && svg.viewBox.baseVal; if (!vb) return;
      const rect = svg.getBoundingClientRect();
      const scaleX = startVb.width / Math.max(1, rect.width);
      const scaleY = startVb.height / Math.max(1, rect.height);
      const dx = (e.clientX - sx) * scaleX;
      const dy = (e.clientY - sy) * scaleY;
      const nx = startVb.x - dx; // drag right => move viewBox left
      const ny = startVb.y - dy;
      svg.setAttribute('viewBox', `${nx} ${ny} ${startVb.width} ${startVb.height}`);
    };
    const onUp = ()=>{ dragging=false; svg.style.cursor='default'; };
    svg.addEventListener('mousedown', onDown);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }catch{}
}
