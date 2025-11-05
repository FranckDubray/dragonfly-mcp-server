






















// Gestion des transitions entre graphes (layers enter/exit)
// Remplacé par un fondu au blanc total ~0.5s pour éviter les à-coups de zoom.
export function swapGraph(stageEl, newSvg){
  return new Promise(resolve=>{
    const prev = stageEl.querySelector('svg.graph-layer');

    // Crée/assure un voile blanc plein écran dans le stage
    let veil = stageEl.querySelector('.graph-veil');
    if (!veil){
      veil = document.createElement('div');
      veil.className = 'graph-veil';
      veil.style.position = 'absolute';
      veil.style.inset = '0';
      veil.style.background = '#fff';
      veil.style.pointerEvents = 'none';
      veil.style.opacity = '0';
      veil.style.transition = 'opacity .25s ease';
      veil.style.zIndex = '5';
      // S'assure que le stage est positionné
      const cs = getComputedStyle(stageEl);
      if (cs.position === 'static'){ stageEl.style.position = 'relative'; }
      stageEl.appendChild(veil);
    }

    // 1) Fade-in du voile (250ms)
    requestAnimationFrame(()=>{ veil.style.opacity = '1'; });

    const phase2 = () => {
      // 2) Swap réel des SVG pendant que le voile est opaque
      try{ if (prev) prev.remove(); }catch{}
      // Toujours marquer le calque mais neutraliser toute transition CSS par styles inline
      newSvg.classList.add('graph-layer');
      try{
        newSvg.removeAttribute('width');
        newSvg.removeAttribute('height');
        newSvg.setAttribute('preserveAspectRatio','xMidYMid meet');
        newSvg.style.height = '100%';
        newSvg.style.width = 'auto';
        newSvg.style.display = 'block';
        // Neutraliser toute animation CSS (enter/exit) et tout translate
        newSvg.style.transition = 'none';
        newSvg.style.opacity = '1';
        newSvg.style.transform = 'none';
      }catch{}
      stageEl.appendChild(newSvg);

      // 3) Fade-out du voile (250ms)
      requestAnimationFrame(()=>{
        // petite latence pour laisser le navigateur poser le nouveau SVG
        setTimeout(()=>{ veil.style.opacity = '0'; }, 16);
      });

      // Cleanup après la transition (max ~300ms)
      const done = ()=>{ resolve(); };
      setTimeout(done, 260);
    };

    // Caler phase2 après ~250ms de fade-in
    setTimeout(phase2, 260);
  });
}

// Motion idle inchangé (léger shimmer visuel)
export function setIdleMotion(stageEl, enabled=true){
  try{
    if (!stageEl) return;
    if (enabled) stageEl.classList.add('idle-motion');
    else stageEl.classList.remove('idle-motion');
  }catch{}
}

// Les helpers de zoom restent disponibles mais ne seront plus utilisés pour la transition
// depuis l'overview → subgraph dans la modale (on passe par le voile).
function _tweenViewBox(svg, from, to, ms=320){
  return new Promise(resolve=>{
    try{
      const start = performance.now();
      const step = (t)=>{
        const p = Math.min(1, (t-start)/ms);
        const lerp = (a,b)=> a + (b-a)*p;
        const x = lerp(from.x, to.x);
        const y = lerp(from.y, to.y);
        const w = lerp(from.width, to.width);
        const h = lerp(from.height, to.height);
        svg.setAttribute('viewBox', `${x} ${y} ${w} ${h}`);
        if (p < 1) requestAnimationFrame(step); else resolve();
      };
      requestAnimationFrame(step);
    }catch{ resolve(); }
  });
}

function _nodeTargetViewBoxFill(svg, g, fill=0.90){
  try{
    const bb = g.getBBox();
    const base = svg.__initialViewBox || (svg.viewBox && svg.viewBox.baseVal);
    if (!base) return null;
    const A = base.width / base.height;
    let targetH = Math.max(40, bb.height / Math.max(0.01, fill));
    let targetW = targetH * A;
    const minW = bb.width / Math.max(0.01, fill);
    if (targetW < minW){ targetW = minW; targetH = targetW / A; }
    const cx = bb.x + bb.width/2; const cy = bb.y + bb.height/2;
    return { x: cx - targetW/2, y: cy - targetH/2, width: targetW, height: targetH };
  }catch{ return null; }
}

export async function animateZoomToNode(svg, g, {durationMs=100, fill=0.90}={}){
  try{
    const vb = svg.viewBox && svg.viewBox.baseVal; if (!vb) return;
    const from = { x: vb.x, y: vb.y, width: vb.width, height: vb.height };
    const to = _nodeTargetViewBoxFill(svg, g, fill) || from;
    await _tweenViewBox(svg, from, to, durationMs);
  }catch{}
}

export async function animateZoomFromNodeToFit(svg, g, {durationMs=180, fill=0.90}={}){
  try{
    const vb = svg.viewBox && svg.viewBox.baseVal; if (!vb) return;
    const ivb = svg.__initialViewBox || { x: vb.x, y: vb.y, width: vb.width, height: vb.height };
    const from = _nodeTargetViewBoxFill(svg, g, fill) || { x: vb.x, y: vb.y, width: vb.width, height: vb.height };
    svg.setAttribute('viewBox', `${from.x} ${from.y} ${from.width} ${from.height}`);
    await _tweenViewBox(svg, from, ivb, durationMs);
  }catch{}
}
