



















import { loadOpts } from './prefs.js';
import { animateFuse, animatePulse } from './edge_fx.js';
import { setIdleMotion, animateZoomToNode, animateZoomFromNodeToFit } from './animations.js';
import { findNodeG } from './pmg_find.js';

function splitNode(node){
  const s = String(node||'');
  const parts = s.split('::');
  return { sg: parts[0] || '', step: parts[1] || '' };
}

export class GraphViewEvents{
  constructor(core, io){
    this.core = core; this.io = io;
    this._raf=0; this._pending=null; this._lastId=''; this._fx=null; this._idleTimer=0;
    this._lastSg=''; this._lastErrSig='';
    this._notFoundWarned = new Set();
    this._bind();
    try{
      if (this._idleTimer){ clearTimeout(this._idleTimer); this._idleTimer = 0; }
      this._idleTimer = setTimeout(()=>{
        try{
          const stage = document.querySelector('.graph-stage') || document.querySelector('.graph-stage--modal');
          if (stage) setIdleMotion(stage, true);
        }catch{}
      }, 2000);
    }catch{}
  }
  _bind(){
    window.addEventListener('workers:highlightNode', (e)=>{ const id=(e.detail||{}).nodeId||''; if(id){ this._handle({node_executed:id, io:{in:{}, out_preview:''}}); } });
  }
  _schedule(){ if (this._raf) return; this._raf = requestAnimationFrame(()=>{ this._raf=0; if (this._pending){ this._handle(this._pending); this._pending=null; } }); }
  handleEvent(evt){ this._pending = evt; this._schedule(); }
  _isSymbolic(node){
    if (!node) return true;
    if (node === 'START' || node === 'END') return true;
    const { step } = splitNode(node);
    if (['success','fail','retry','retry_exhausted'].includes(step)) return true;
    return false;
  }

  async _ensureNodeOnGraph(node){
    try{
      const stage = document.querySelector('.graph-stage') || document.querySelector('.graph-stage--modal');
      const getSvg = ()=> document.querySelector('.graph-stage svg') || document.querySelector('.graph-stage--modal svg');
      const tryFind = ()=>{ const svg = getSvg(); return findNodeG(svg, node); };

      const { sg } = splitNode(node);
      const curKind = this.core.currentKind;
      const curSg = (stage?.dataset?.subgraph||'');
      if (window.__GV_DEBUG){ try{ const svg=getSvg(); console.debug('[GV] ensure start', { node, curKind, curSg, diag: svg && svg.getAttribute && svg.getAttribute('data-mermaid-id') }); }catch{} }

      // If we are in overview and node has a subgraph, always switch (overview n'affiche pas les steps)
      if (curKind === 'overview' && sg){
        if (window.__GV_DEBUG){ try{ console.debug('[GV] force switch from overview to subgraph', sg); }catch{} }
        try{ this.core.gc && this.core.gc.clear && this.core.gc.clear(); }catch{}
        await this.core.render('subgraph', sg);
        const svgNew = getSvg();
        const gNew = svgNew && findNodeG(svgNew, node);
        if (svgNew && gNew){ try{ await animateZoomFromNodeToFit(svgNew, gNew, {durationMs:180, fill:0.90}); }catch{} }
        const gAfter = tryFind(); if (gAfter){ if (window.__GV_DEBUG) console.debug('[GV] found after overview->subgraph render'); return gAfter; }
      }

      // 1) Try current SVG
      let g = tryFind(); if (g){ if (window.__GV_DEBUG) console.debug('[GV] found on current svg'); return g; }

      // 2) If node has a subgraph, force switch to that subgraph (even if lastSg matches)
      if (sg){
        try{
          const svgCur = getSvg();
          const gCur = svgCur && findNodeG(svgCur, node);
          if (svgCur && gCur){ await animateZoomToNode(svgCur, gCur, {durationMs:100, fill:0.90}); }
        }catch{}
        try{ this.core.gc && this.core.gc.clear && this.core.gc.clear(); }catch{}
        if (window.__GV_DEBUG){ try{ console.debug('[GV] switch to subgraph', sg); }catch{} }
        await this.core.render('subgraph', sg);
        const svgNew = getSvg();
        const gNew = svgNew && findNodeG(svgNew, node);
        if (svgNew && gNew){ try{ await animateZoomFromNodeToFit(svgNew, gNew, {durationMs:180, fill:0.90}); }catch{} }
        g = tryFind(); if (g){ if (window.__GV_DEBUG) console.debug('[GV] found after subgraph render'); return g; }
      }

      // 3) Fallback try full process
      if (this.core.currentKind !== 'process'){
        try{ this.core.gc && this.core.gc.clear && this.core.gc.clear(); }catch{}
        if (window.__GV_DEBUG){ try{ console.debug('[GV] fallback process'); }catch{} }
        await this.core.render('process');
        g = tryFind(); if (g){ if (window.__GV_DEBUG) console.debug('[GV] found after process'); return g; }
      }
      // 4) Final fallback overview
      if (this.core.currentKind !== 'overview'){
        try{ this.core.gc && this.core.gc.clear && this.core.gc.clear(); }catch{}
        if (window.__GV_DEBUG){ try{ console.debug('[GV] fallback overview'); }catch{} }
        await this.core.render('overview');
        g = tryFind(); if (g){ if (window.__GV_DEBUG) console.debug('[GV] found after overview'); return g; }
      }
      if (window.__GV_DEBUG){ try{ console.debug('[GV] ensure end: not found', {node}); }catch{} }
      return null;
    }catch(e){ if (window.__GV_DEBUG){ try{ console.warn('[GV] ensure error', e); }catch{} } return null; }
  }

  async _handle(evt){
    const node = evt?.node_executed || '';
    if (!node) return;

    try{ this.io.update(evt); }catch{}

    try{
      const stage = document.querySelector('.graph-stage') || document.querySelector('.graph-stage--modal');
      if (stage){
        setIdleMotion(stage, false);
        if (this._idleTimer){ clearTimeout(this._idleTimer); this._idleTimer = 0; }
        this._idleTimer = setTimeout(()=>{ try{ setIdleMotion(stage, true); }catch{} }, 2000);
      }
    }catch{}

    if (this._isSymbolic(node)){
      if (window.__GV_DEBUG){ try{ console.debug('[GV] symbolic node skip', node); }catch{} }
      return;
    }

    const last = this._lastId; this._lastId = node;
    const { sg } = splitNode(node);
    const { sg: sgLast } = splitNode(last);
    const err = (String(evt?.chunk_type||'')==='error' || String(evt?.status||'')==='failed');

    if (window.__GV_DEBUG){ try{ console.debug('[GV] step', {node, sg, last, curKind:this.core.currentKind}); }catch{} }
    const g = await this._ensureNodeOnGraph(node);
    const svg = document.querySelector('.graph-stage svg') || document.querySelector('.graph-stage--modal svg');

    if (!g){
      const key = `${this.core.currentKind}|${node}`;
      if (!this._notFoundWarned.has(key)){
        this._notFoundWarned.add(key);
        try{ console.warn('[GraphView] node not found on graph after fallbacks:', { node, kind:this.core.currentKind }); }catch{}
      }
      return;
    }

    const fromG = last ? findNodeG(svg, last) : null;
    if (err){ try{ g.classList.add('m-node-error'); }catch{} this.core.hl.highlight(node); }
    else if (fromG && sgLast===sg){ try{ this._fx && this._fx.cancel(); }catch{} this._fx = animateFuse(svg, fromG, g, {durationMs:500}); setTimeout(() => this.core.hl.highlight(node), 480); }
    else {
      try{ animatePulse(svg, g, {times:1}); }catch{}
      this.core.hl.highlight(node);
    }
  }
}

 
 
 
 
 
 
 
 
 
 
 
 
 
