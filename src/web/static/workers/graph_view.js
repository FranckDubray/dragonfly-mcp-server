
import { GraphViewCore } from './graph_view_core.js';
import { GraphViewEvents } from './graph_view_events.js';
import { GraphViewStreams } from './graph_view_streams.js';
import { t } from './i18n.js';
import { api } from './api.js';
import { wireToolbarAndShortcuts } from './graph_view_toolbar_wiring.js';

export class GraphView{
  constructor(worker, root, ioPanel){
    this.core = new GraphViewCore(worker, root, ioPanel);
    this.events = new GraphViewEvents(this.core, ioPanel);
    this.streams = new GraphViewStreams(this.core, this.events);
  }
  async _pickInitialKind(){
    try{
      const js = await api.status(this.core.worker);
      const ph = String(js.phase || js.status || '').toLowerCase();
      if (ph === 'running' || ph === 'starting') return 'current_subgraph';
      return 'overview';
    }catch{ return 'overview'; }
  }
  _applyZoom(delta){
    try{
      const svg = document.querySelector('.graph-stage svg') || document.querySelector('.graph-stage--modal svg');
      if (!svg) return;
      const vb = svg.viewBox.baseVal; if (!vb || vb.width<=0 || vb.height<=0) return;
      const factor = (1 + delta);
      const newW = vb.width / factor;
      const newH = vb.height / factor;
      const cx = vb.x + vb.width/2; const cy = vb.y + vb.height/2;
      const nx = cx - newW/2; const ny = cy - newH/2;
      svg.setAttribute('viewBox', `${nx} ${ny} ${newW} ${newH}`);
    }catch{}
  }
  _resetZoom(){
    try{
      const svg = document.querySelector('.graph-stage svg') || document.querySelector('.graph-stage--modal svg');
      if (!svg) return;
      const vb = svg.viewBox && svg.viewBox.baseVal;
      if (vb && svg.__initialViewBox){
        const ivb = svg.__initialViewBox;
        svg.setAttribute('viewBox', `${ivb.x} ${ivb.y} ${ivb.width} ${ivb.height}`);
      }
    }catch{}
  }
  _fitHeight(){
    try{
      const stage = document.querySelector('.graph-stage') || document.querySelector('.graph-stage--modal');
      const svg = stage && (stage.querySelector('svg'));
      if (!svg) return;
      svg.style.width='auto';
      svg.style.height='100%';
      svg.style.display='block';
      svg.style.maxWidth='unset';
      const ivb = svg.__initialViewBox;
      if (ivb){ svg.setAttribute('viewBox', `${ivb.x} ${ivb.y} ${ivb.width} ${ivb.height}`); }
      requestAnimationFrame(()=>{
        try{
          const bb = svg.getBoundingClientRect();
          const st = stage.getBoundingClientRect();
          if (bb.width > st.width){
            const targetLeft = (svg.scrollWidth || stage.scrollWidth)/2 - (stage.clientWidth/2);
            stage.scrollLeft = targetLeft;
          }
        }catch{}
      });
    }catch{}
  }
  async attach(){
    const wrap = this.core.graphWrap(
      (node, when)=> import('./debug_controls.js').then(m=>m.DebugControls.runUntil(this.core.worker, node, when)),
      (node, when)=> import('./debug_controls.js').then(m=>m.DebugControls.breakAdd(this.core.worker, node, when)),
      (node, when)=> import('./debug_controls.js').then(m=>m.DebugControls.breakRemove(this.core.worker, node, when)),
    );
    this.core.attach(wrap.wrap);

    const initial = await this._pickInitialKind();
    await this.core.render(initial);

    this.streams.startObserve();

    // Minor i18n label tweaks + ensure Start (observe/debug) buttons exist
    try{
      const bar2 = document.querySelector('.graph-toolbar');
      const btnProcess = bar2.querySelector('button[data-act="process"]'); if (btnProcess) btnProcess.textContent = t('toolbar.process');
      const btnCurrent = bar2.querySelector('button[data-act="current"]'); if (btnCurrent) btnCurrent.textContent = t('toolbar.current');
      const btnOverview = bar2.querySelector('button[data-act="overview"]'); if (btnOverview) btnOverview.textContent = t('toolbar.overview');

      const ctrlGroup = bar2.querySelectorAll('.group')[1] || bar2;
      if (!bar2.querySelector('button[data-act="start-observe"]')){
        const b = document.createElement('button'); b.className='btn tooltip'; b.dataset.act='start-observe'; b.setAttribute('data-tip', t('common.start_observe','Start (observe)')); b.textContent = t('common.start_observe','Start (observe)');
        ctrlGroup.insertBefore(b, ctrlGroup.firstChild);
      }
      if (!bar2.querySelector('button[data-act="start-debug"]')){
        const b = document.createElement('button'); b.className='btn'; b.dataset.act='start-debug'; b.textContent = t('common.start_debug');
        ctrlGroup.insertBefore(b, ctrlGroup.firstChild.nextSibling);
      }
    }catch{}

    // Delegate toolbar wiring and keyboard shortcuts
    wireToolbarAndShortcuts(this);
  }
}
