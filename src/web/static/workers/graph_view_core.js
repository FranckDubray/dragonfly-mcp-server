



























import { GraphCache } from './graph_cache.js';
import { Highlighter } from './highlight.js';
import { swapGraph, setIdleMotion } from './animations.js';
import { loadOpts, saveOpts, loadKind, saveKind } from './prefs.js';
import { createToolbar } from './toolbar.js';
import { ControlInputs } from './control_inputs.js';
import { DebugControls } from './debug_controls.js';
import { NodeMenu } from './node_menu.js';
import { t } from './i18n.js';
import { findNodeG } from './pmg_find.js'; // NEW: tolerant finder like process modal

// DEBUG bootstrap (persist across reloads via localStorage or ?gvdebug=1)
try{
  const qs = new URLSearchParams(location.search);
  const qdbg = qs.get('gvdebug');
  const ldbg = localStorage.getItem('GV_DEBUG')||sessionStorage.getItem('GV_DEBUG');
  const on = (qdbg==='1') || (ldbg==='1');
  if (on) window.__GV_DEBUG = true;
  window.__GV_SET_DEBUG = (b)=>{ try{ window.__GV_DEBUG=!!b; localStorage.setItem('GV_DEBUG', b?'1':''); }catch{} };
}catch{}

export class GraphViewCore{
  constructor(worker, root, ioPanel){
    this.worker = worker; this.root = root; this.io = ioPanel;
    this.gc = new GraphCache(worker);
    this.hl = new Highlighter();
    this.currentKind = loadKind(worker) || 'process';
    this.renderChain = Promise.resolve();
    this.menu = new NodeMenu(worker);
    window.addEventListener('workers:openSubgraph', (e)=>{
      const sg = (e.detail||{}).subgraph||''; if (!sg) return; this.render('subgraph', sg);
    });
  }
  setActive(kind, mode){
    document.querySelectorAll('.graph-toolbar .btn[data-act]').forEach(b=> b.classList.remove('active'));
    const btn = document.querySelector(`.graph-toolbar .btn[data-act="${kind}"]`);
    if (btn) btn.classList.add('active');
    const mo = document.querySelector(`.graph-toolbar .btn[data-act="mode-${mode}"]`);
    if (mo) mo.classList.add('active');
  }
  toolbar(onRunUntil, onBreakAdd, onBreakRemove){
    const opts = loadOpts();
    const div = createToolbar(opts);
    new ControlInputs(div.querySelector('div:first-child'), this.worker, { onRunUntil, onBreakAdd, onBreakRemove });
    return div;
  }
  graphWrap(onRunUntil, onBreakAdd, onBreakRemove){
    const wrap = document.createElement('div');
    wrap.className = 'graph-wrap';
    const tb = this.toolbar(onRunUntil, onBreakAdd, onBreakRemove);
    const stage = document.createElement('div');
    stage.className = 'graph-stage';
    try{
      const opts = loadOpts();
      stage.dataset.autoCenter = String(!!opts.auto_center);
    }catch{}
    wrap.appendChild(tb); wrap.appendChild(stage);
    const setH = ()=>{
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
      wrap.style.height = `calc(var(--vh, 1vh) * 100)`;
      const th = tb.getBoundingClientRect().height;
      stage.style.height = `calc(100% - ${th}px)`;
      stage.style.overflowX = 'auto';
      stage.style.overflowY = 'hidden';
      stage.style.position = 'relative';
      const svg = stage.querySelector('svg');
      if (svg){
        svg.style.position=''; svg.style.top=''; svg.style.left='';
        svg.style.width='auto'; svg.style.height='100%'; svg.style.maxWidth='unset';
      }
      setIdleMotion(stage, false);
    };
    const deb = ()=>{ clearTimeout(window.__gv_resize_to); window.__gv_resize_to=setTimeout(setH,100); };
    setH(); window.addEventListener('resize', deb);
    return {wrap, stage};
  }
  readOpts(){
    const bar = document.querySelector('.graph-toolbar');
    const opts = {
      hide_start: bar.querySelector('input[data-opt="hide_start"]').checked,
      hide_end: bar.querySelector('input[data-opt="hide_end"]').checked,
      labels: bar.querySelector('input[data-opt="labels"]').checked,
      follow_sg: (bar.querySelector('input[data-opt="follow_sg"]')?.checked) || false,
      auto_center: (bar.querySelector('input[data-opt="auto_center"]')?.checked) !== false,
    };
    const out = saveOpts(opts);
    try{ const stage = document.querySelector('.graph-stage'); if (stage) stage.dataset.autoCenter = String(!!out.auto_center); }catch{}
    return out;
  }
  async render(kind, subgraph){
    if (window.__GV_DEBUG){ try{ console.debug('[GV:render] request', {kind, subgraph}); }catch{} }
    this.renderChain = this.renderChain.then(async ()=>{
      this.currentKind = kind; saveKind(this.worker, kind);
      const opts = loadOpts();
      try{
        const {svg} = await this.gc.ensureRender(kind, {...opts, subgraph});
        try{
          svg.removeAttribute('width'); svg.removeAttribute('height');
          svg.setAttribute('preserveAspectRatio','xMidYMid meet');
          svg.style.width='auto'; svg.style.height='100%'; svg.style.display='block'; svg.style.maxWidth='unset';
        }catch{}
        const stage = document.querySelector('.graph-stage');
        if (!stage){ if (window.__GV_DEBUG) console.warn('[GV:render] stage not found'); return; }
        await swapGraph(stage, svg.cloneNode(true));
        const liveSvg = stage.querySelector('svg');
        try{
          const vb = liveSvg.viewBox && liveSvg.viewBox.baseVal;
          if (vb && !liveSvg.__initialViewBox){ liveSvg.__initialViewBox = { x: vb.x, y: vb.y, width: vb.width, height: vb.height }; }
        }catch{}
        try{
          requestAnimationFrame(()=>{
            const bb = liveSvg.getBoundingClientRect();
            const st = stage.getBoundingClientRect();
            if (bb.width > st.width){
              const targetLeft = (liveSvg.scrollWidth || stage.scrollWidth)/2 - (stage.clientWidth/2);
              stage.scrollLeft = targetLeft;
            }
          });
        }catch{}
        liveSvg.addEventListener('click', (e)=>{
          const g = e.target.closest('g[id]'); if(!g) return;
          const isNode = g.querySelector('rect, path'); if (!isNode) return;
          this.menu.showAt(stage, liveSvg, g);
        });
        this.hl.attach(liveSvg, {
          get: (id)=> findNodeG(liveSvg, id),
          has: (id)=> !!findNodeG(liveSvg, id)
        });
        setIdleMotion(stage, false);
        try{ stage.dataset.kind = kind; stage.dataset.subgraph = subgraph || ''; }catch{}
        if (window.__GV_DEBUG){ try{ console.debug('[GV:render] swapped', {kind, subgraph, svg: !!liveSvg}); }catch{} }
      }catch(err){
        const stage = document.querySelector('.graph-stage');
        if (stage){
          stage.innerHTML = '';
          const panel = document.createElement('div'); panel.className = 'panel';
          const h3 = document.createElement('h3'); h3.textContent = t('graph.error_title','Graph');
          const pre = document.createElement('pre'); pre.className='io-pre'; pre.textContent = String((err && err.message) ? err.message : t('graph.unavailable','Graph unavailable'));
          panel.append(h3, pre); stage.appendChild(panel);
        }
        if (window.__GV_DEBUG){ try{ console.warn('[GV:render] error', err); }catch{} }
      }
    }).catch(()=>{});
    return this.renderChain;
  }
  attach(root){ this.root.appendChild(root); }
}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
