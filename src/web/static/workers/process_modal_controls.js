












// Process modal: add Start (observe) and Start debug buttons, minimal wiring
import { api } from './api.js';
import { resolveWorkerFile, waitForPhase } from './graph_view_support.js';
import { pickInitialKind } from './process_utils.js';
import { t } from './i18n.js';

export function buildProcessControls(modal, worker, logic, header){
  // Reuse replay controls holder if present to keep everything on one line
  let holder = modal.body.querySelector('[data-role="replay-controls"]');
  let created = false;
  if (!holder){
    holder = document.createElement('div');
    holder.style.cssText = 'display:flex; gap:8px; align-items:center; margin:8px 0; flex-wrap:nowrap; overflow-x:auto;';
    created = true;
  } else {
    // ensure single-row behavior
    holder.style.flexWrap = 'nowrap';
    holder.style.overflowX = 'auto';
  }

  const bStartObs = document.createElement('button');
  bStartObs.className = 'btn';
  bStartObs.textContent = t('common.start_observe','Start (observe)');

  const bStartDbg = document.createElement('button');
  bStartDbg.className = 'btn';
  bStartDbg.textContent = t('common.start_debug','Start debug');

  // insert buttons at the beginning of the row
  try{
    const firstChild = holder.firstChild;
    if (firstChild) holder.insertBefore(bStartDbg, firstChild); else holder.appendChild(bStartDbg);
    if (firstChild) holder.insertBefore(bStartObs, holder.firstChild); else holder.appendChild(bStartObs);
  }catch{
    holder.append(bStartDbg, bStartObs);
  }

  if (created){
    // If no replay controls row, insert near top as a single row
    try{ modal.body.insertBefore(holder, modal.body.firstChild.nextSibling); }catch{}
  }

  async function startAndAttach(startFn){
    try{
      const wf = await resolveWorkerFile(worker);
      await startFn(worker, wf);
      header?.setLiveAvailable?.(true);
    }catch(e){ console.warn('[process-modal] start error', e); }
    // Choose same initial view across modes: current_subgraph if running, else overview
    try{ await waitForPhase(worker, ['starting','running'], 7000, 250); }catch{}
    try{
      const initial = await pickInitialKind(worker, api);
      await logic.loadGraph(initial);
    }catch{}
    try{ await logic.startObserve(); }catch{}
  }

  bStartObs.onclick = async () => {
    try{ header?.setMode?.('observe'); }catch{}
    await startAndAttach(api.startObserve);
  };

  bStartDbg.onclick = async () => {
    try{ header?.setMode?.('debug'); }catch{}
    await startAndAttach(api.startDebug);
  };

  return holder;
}

 
 
 
 
 
 
 
