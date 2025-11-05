








import { t } from './i18n.js';
import { formatLocalTs, fmtRunWindow } from './process_utils.js';
import { ReplayController } from './replay_driver.js';
import { api } from './api.js';

// Replay Panel (time machine): list runs and steps, playback highlighting nodes
export class ReplayPanel{
  constructor(root, worker){ this.root=root; this.worker=worker; this.box=document.createElement('div'); this.box.className='panel'; this.title=document.createElement('h3'); this.title.textContent=t('replay.title','Replay (time machine)'); this.body=document.createElement('div'); this.box.append(this.title, this.body); root.appendChild(this.box); this.steps=[]; this._live=null; this._replay=null; this.init(); }
  async init(){ this.renderShell(); await this.loadRuns(); }
  renderShell(){
    this.body.innerHTML='';
    const controls = document.createElement('div'); controls.style.display='flex'; controls.style.gap='8px'; controls.style.alignItems='center';
    const sel = document.createElement('select'); sel.setAttribute('aria-label',t('replay.load_run','Load run')); this.sel=sel; sel.style.minWidth='260px'; sel.style.height='34px'; sel.style.padding='6px 10px';
    const btnLoad = document.createElement('button'); btnLoad.className='btn'; btnLoad.textContent=t('replay.load_run','Load run'); btnLoad.onclick=()=>this.loadSteps();
    const btnPrev = document.createElement('button'); btnPrev.className='btn'; btnPrev.textContent='◀︎'; btnPrev.onclick=()=>this.prev();
    const btnPlay = document.createElement('button'); btnPlay.className='btn'; btnPlay.textContent='⏵'; btnPlay.onclick=()=>this.playOrPause();
    const btnNext = document.createElement('button'); btnNext.className='btn'; btnNext.textContent='▶︎'; btnNext.onclick=()=>this.next();
    const btnStop = document.createElement('button'); btnStop.className='btn danger'; btnStop.textContent='⏹'; btnStop.onclick=()=>this.stop();
    const btnRef = document.createElement('button'); btnRef.className='btn'; btnRef.textContent='⟳'; btnRef.onclick=()=>this.loadRuns();
    controls.append(sel, btnLoad, btnPrev, btnPlay, btnNext, btnStop, btnRef);
    const live = document.createElement('div'); live.setAttribute('aria-live','polite'); live.style.position='absolute'; live.style.left='-10000px'; live.style.top='auto'; live.style.width='1px'; live.style.height='1px'; live.style.overflow='hidden'; this._live = live;
    const list = document.createElement('div'); list.style.marginTop='8px'; list.style.display='grid'; list.style.gap='6px'; list.setAttribute('role','list'); this.list=list;
    this.body.append(controls, live, list);
  }
  async loadRuns(){
    try{
      const runs = await api.replayRuns(this.worker);
      this.sel.innerHTML='';
      (runs||[]).forEach(rm=>{ const o=document.createElement('option'); o.value=rm.id; o.textContent=fmtRunWindow(rm.started_at, rm.finished_at, rm.steps) || rm.id; this.sel.appendChild(o); });
      if (!runs || !runs.length){ const o=document.createElement('option'); o.textContent='(—)'; this.sel.appendChild(o); }
    }catch(e){ this.list.textContent = t('replay.error_runs','Error loading runs'); }
  }
  async ensureDriver(){ if (!this._replay) this._replay = new ReplayController(this.worker, (ev)=>this._handleEvent(ev), api); }
  async loadSteps(){ await this.ensureDriver(); await this._replay.setRun(this.sel.value||''); await this.renderSteps(); }
  async renderSteps(){
    try{
      const steps = await api.replaySteps(this.worker, this.sel.value||'', 500);
      this.steps = steps||[];
      this.list.innerHTML='';
      this.steps.forEach((st, i)=>{
        const row = document.createElement('div'); row.setAttribute('role','listitem'); row.style.border='1px solid #e5e7eb'; row.style.borderRadius='8px'; row.style.padding='8px';
        const when = formatLocalTs(st.finished_at || '');
        const meta = document.createElement('div'); meta.style.fontSize='12px'; meta.style.color='#6b7280'; meta.textContent = `#${i+1} • ${st.status||''} • ${st.duration_ms||0}ms • ${when}`;
        const node = document.createElement('div'); node.style.fontWeight='600'; node.textContent = st.node||'';
        const btn = document.createElement('button'); btn.className='btn'; btn.textContent=t('replay.view_node','View this node'); btn.onclick=()=>this.jumpTo(i);
        const io = document.createElement('pre'); io.className='io-pre'; io.textContent = `${t('io.in','IN')}:\n${safe(st.io?.in)}\n\n${t('io.out','OUT')}:\n${String(st.io?.out_preview??'')}`;
        row.append(meta, node, btn, io); this.list.appendChild(row);
      });
    }catch(e){ this.list.textContent = t('replay.error_steps','Error loading steps'); }
  }
  _handleEvent(ev){
    // Annonce ARIA
    if (this._live){
      const st = this._replay ? this._replay.getState() : {idx:-1,total:0};
      const idx = st.idx>=0? st.idx+1 : 0;
      this._live.textContent = String(t('replay.live_announce_step','Playing step {idx}/{total}: {nodeId}'))
        .replace('{idx}', String(idx)).replace('{total}', String(st.total||0)).replace('{nodeId}', String(ev?.node_executed||''));
    }
    // Déjà remis dans la tuyauterie via GraphViewEvents côté appelant (quand utilisé dans GraphView).
  }
  prev(){ this._replay && this._replay.prev(); }
  next(){ this._replay && this._replay.next(); }
  playOrPause(){ if (!this._replay) return; const st=this._replay.getState(); if (st.playing) this._replay.pause(); else this._replay.play(600); }
  stop(){ this._replay && this._replay.stop(); }
  jumpTo(i){ this._replay && this._replay.jumpTo(i); }
}
function safe(o){ try{ return JSON.stringify(o||{}, null, 2); }catch{ return String(o); } }

 
 
 
 
 
 
 
