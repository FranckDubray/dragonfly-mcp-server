












import { api } from './api.js';
import { createModal } from './modal.js';
import { t } from './i18n.js';
import { resolveAsset, pickInitialKind, formatLocalTs } from './process_utils.js';
import { initHeader, buildStage } from './process_modal_dom.js';
import { createGraphLogic } from './process_modal_graph.js';
import { buildReplayControls } from './process_modal_replay.js';

export async function openProcessModal(worker){
  let display = worker; let avatarUrl = '';
  try{ const iw = await api.identityWorker(worker); const id = iw.identity||{}; const dn = id.display_name||''; if (dn) display = dn; avatarUrl = resolveAsset(id.avatar_url||''); }catch{}

  const modal = createModal({ title: `${t('modal.process_title','Processus —')} ${display}` , width: 'min(1200px, 96vw)' });

  // Header (avatar, badge, freeze)
  const header = initHeader(modal, { avatarUrl, display });

  // DOM stage + side IO
  const st = buildStage(modal);

  // Graph + observe logic
  const logic = createGraphLogic(worker, st.dom, (kind)=> header.upd(kind));

  // Replay controls (toolbar-in-modal) — build FIRST
  const replay = buildReplayControls(
    modal,
    worker,
    st.dom,
    async (ev)=>{
      const node = ev && ev.node_executed || '';
      const call = ev?.io?.in || {};
      const isTool = !!(call.tool || call.tool_name || call.operation);
      header.upd(isTool ? 'tool' : 'running');
      try{
        st.setCurrent(node);
        st.setStepTs(ev.finished_at || ev.started_at || '');
        const m = await import('./json_viewer.js');
        await m.ensureJsonFormatter();
        m.renderJson(st.dom.inBox, call, '');
        m.renderJson(st.dom.outBox, ev?.io?.out_preview||'', String(ev?.io?.out_preview||''));
        if (node){ await logic.ensureAndHighlight(node); }
      }catch{}
    },
    // onResetGraph: reset overview when user selects a new run
    async ()=>{ try{ await logic.loadGraph('overview'); }catch{} },
    header
  );

  // Start/Debug controls (insert AFTER replay controls so they stay on the same line)
  const ctrl = await import('./process_modal_controls.js');
  ctrl.buildProcessControls(modal, worker, logic, header);

  // Open and init
  modal.open();
  const initial = await pickInitialKind(worker, api);
  await logic.loadGraph(initial);
  await (async()=>{ try{ /* prewarm JSON viewer */ const m = await import('./json_viewer.js'); await m.ensureJsonFormatter(); }catch{} })();
  // Prime IO from status if running
  try{
    const stj = await api.status(worker);
    const ph = String(stj.phase || stj.status || '').toLowerCase();
    if (['completed','canceled','failed'].includes(ph)) header.upd('idle');
    if (ph==='running' || ph==='starting'){
      header.upd('running');
      const last = (Array.isArray(stj.recent_steps) ? stj.recent_steps : []).slice(-1)[0];
      const node = last && last.node || '';
      if (node){
        st.setCurrent(node); st.setStepTs(last.finished_at || last.started_at || '');
        const m = await import('./json_viewer.js');
        await m.ensureJsonFormatter();
        m.renderJson(st.dom.inBox, last.io?.in||{}, '');
        m.renderJson(st.dom.outBox, last.io?.out_preview||'', String(last.io?.out_preview||''));
        await logic.ensureAndHighlight(node);
      }
    }
  }catch{}
  // Start observe live by default and set mode badge
  try{ header.setMode && header.setMode('observe'); }catch{}
  logic.startObserve();

  // Auto-refresh runs list when a run completes/failed/canceled in observe/debug
  const onRunsRefresh = async (e)=>{
    try{ if (e && e.detail && e.detail.worker === worker){ /* Could refresh runs list here if controls exposed */ } }catch{}
  };
  window.addEventListener('workers:runsRefresh', onRunsRefresh);
  // Remove listener when modal closes (best-effort)
  modal.overlay.addEventListener('DOMNodeRemoved', ()=>{ try{ window.removeEventListener('workers:runsRefresh', onRunsRefresh); }catch{} }, {once:true});
}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
