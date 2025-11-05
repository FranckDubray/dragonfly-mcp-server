


















export class Highlighter{
  attach(svg, index){ this.svg=svg; this.index=index; this.current=null; this._prevShapes=[]; }

  _clearInline(){
    try{
      if (this._prevShapes && this._prevShapes.length){
        for (const it of this._prevShapes){
          const el = it.el;
          if (!el) continue;
          if (it.strokeSet){ el.style.stroke = it.prevStroke; }
          if (it.wSet){ el.style.strokeWidth = it.prevW; }
          if (it.fSet){ el.style.filter = it.prevF; }
          if (it.foSet){ el.style.fillOpacity = it.prevFO; }
        }
      }
    }catch{}
    this._prevShapes=[];
  }

  highlight(nodeId){
    if (!this.svg || !this.index) return false;
    const g = this.index.get(nodeId);
    try{ console.debug('[HIGHLIGHT] node =', nodeId, 'svgGroupId =', g && g.id ? g.id : '(not-found)'); }catch{}
    if (!g) return false;

    // remove previous highlight
    try{ if (this.current && this.current!==g) this.current.classList.remove('m-node-active'); }catch{}
    this._clearInline();

    // bring the node group to front (z-order)
    try{ if (g.parentNode && g.parentNode.appendChild) g.parentNode.appendChild(g); }catch{}

    // apply highlight class
    this.current = g;
    try{ g.classList.add('m-node-active'); }catch{}

    // Quick pulse animation (non-blocking, very light)
    try{
      // CSS pulse on shapes
      g.classList.add('m-pulse');
      setTimeout(()=>{ try{ g.classList.remove('m-pulse'); }catch{} }, 220);
      // Tiny circle pulse overlay (SVG), non-blocking import
      Promise.resolve()
        .then(()=> import('./edge_fx.js'))
        .then(m => { try{ m.animatePulse(this.svg, g, {times:1}); }catch{} })
        .catch(()=>{});
    }catch{}

    // Inline style as a safety net (in case CSS specificity loses against Mermaid inline styles)
    try{
      const shapes = g.querySelectorAll('rect, polygon, path');
      shapes.forEach(el=>{
        const prevStroke = el.style.stroke || '';
        const prevW = el.style.strokeWidth || '';
        const prevF = el.style.filter || '';
        const prevFO = el.style.fillOpacity || '';
        this._prevShapes.push({ el, prevStroke, prevW, prevF, prevFO, strokeSet:true, wSet:true, fSet:true, foSet:true });
        el.style.stroke = '#f97316';
        el.style.strokeWidth = '3px';
        // keep filter animated by CSS pulse; fallback inline ensures visibility
        if (!el.style.fillOpacity) el.style.fillOpacity = '.96';
      });
    }catch{}

    // Horizontal smooth scroll to center the node if a scroll container exists and auto-center is enabled
    try{
      const stage = this.svg.closest('.graph-stage, .graph-stage--modal');
      const auto = String(stage?.dataset?.autoCenter || 'true') !== 'false';
      if (stage && auto){
        const gbb = g.getBoundingClientRect();
        const sbb = stage.getBoundingClientRect();
        const centerOffset = (gbb.left + gbb.width/2) - (sbb.left + sbb.width/2);
        const targetLeft = stage.scrollLeft + centerOffset;
        stage.scrollTo({ left: targetLeft, behavior: 'smooth' });
        return true;
      }
    }catch(e){ /* noop */ }

    // Pan/zoom fallback via viewBox (no scroll container)
    try{
      const stage = this.svg.closest('.graph-stage, .graph-stage--modal');
      const auto = String(stage?.dataset?.autoCenter || 'true') !== 'false';
      if (!auto) return true;
      const bb = g.getBBox();
      const vb = this.svg.viewBox.baseVal;
      const cx = bb.x + bb.width/2; const cy = bb.y + bb.height/2;
      const scale = Math.max(1, Math.min(2.2, Math.min(vb.width/bb.width, vb.height/bb.height)*0.6));
      const w = vb.width/scale; const h = vb.height/scale;
      this.svg.setAttribute('viewBox', `${cx - w/2} ${cy - h/2} ${w} ${h}`);
    }catch(e){ /* noop */ }
    return true;
  }
}
