












import { api } from './api.js';
import { fmtRunWindow, replayIntervalMs, setReplaySpeed, getReplaySpeed } from './process_utils.js';
import { ReplayController } from './replay_driver.js';
import { modalZoom, modalResetZoom } from './pmg_render.js';

export function buildReplayControls(modal, worker, dom, onReplayEvent, onResetGraph){
  // Ensure a single controls row (avoid duplicates)
  let holder = modal.body.querySelector('[data-role="replay-controls"]');
  if (!holder){
    holder = document.createElement('div');
    holder.setAttribute('data-role','replay-controls');
    holder.classList.add('pm-toolbar');
    // CSS fallback if class not present for any reason
    holder.style.cssText='position:sticky; top:0; left:0; right:0; z-index:20; background:#fff; display:flex; gap:8px; align-items:center; white-space:nowrap; overflow-x:auto; overflow-y:hidden; padding:6px 8px; margin:0 0 8px 0; border-bottom:1px solid var(--border)';
    modal.body.insertBefore(holder, dom.panel);
  } else {
    holder.classList.add('pm-toolbar');
    holder.style.position = 'sticky';
    holder.style.top = '0';
    holder.style.left = '0';
    holder.style.right = '0';
    holder.style.zIndex = '20';
    holder.style.background = '#fff';
    holder.style.display = 'flex';
    holder.style.alignItems = 'center';
    holder.style.gap = '8px';
    holder.style.whiteSpace = 'nowrap';
    holder.style.overflowX = 'auto';
    holder.style.overflowY = 'hidden';
    holder.style.padding = '6px 8px';
    holder.style.margin = '0 0 8px 0';
    holder.style.borderBottom = '1px solid var(--border)';
  }
  holder.innerHTML = '';

  // Smaller select with compact labels (even smaller font)
  const sel = document.createElement('select');
  sel.setAttribute('aria-label','Run');
  sel.style.minWidth='220px';
  sel.style.height='28px';
  sel.style.padding='2px 8px';
  sel.style.fontSize='11.5px';
  sel.title='Sélectionner un run';

  // Icons distincts avec title concis
  const bPrev = mkBtn('\u23ee','Précédent (\u2190)','prev');
  const bPlay = mkBtn('\u25b6','Lire / Pause (Espace)','play');
  const bNext = mkBtn('\u23ed','Suivant (\u2192)','next');
  const bStop = mkBtn('\u23f9','Arrêter la lecture','stop');
  const bRef  = mkBtn('\u27f3','Rafraîchir la liste des runs','refresh');

  const speedWrap = document.createElement('div'); speedWrap.className='btn-group'; speedWrap.setAttribute('data-role','speed');
  const bSMax = mkBtn('Max','Vitesse maximale (0 ms)'); bSMax.dataset.speed='max';
  const bS05 = mkBtn('0.5\u00d7','Vitesse ×0.5'); bS05.dataset.speed='0.5';
  const bS10 = mkBtn('1\u00d7',  'Vitesse ×1');     bS10.dataset.speed='1';
  const bS20 = mkBtn('2\u00d7',  'Vitesse ×2');     bS20.dataset.speed='2';
  speedWrap.append(bSMax,bS05,bS10,bS20);

  // Zoom group
  const zoomWrap = document.createElement('div'); zoomWrap.className='btn-group'; zoomWrap.setAttribute('aria-label','Zoom');
  const zOut   = mkBtn('\u2212','Zoom out','zoom-out');
  const zIn    = mkBtn('+','Zoom in','zoom-in');
  const zReset = mkBtn('\u27F2','Réinitialiser le zoom','zoom-reset');
  zoomWrap.append(zOut, zIn, zReset);

  // Init speed highlight
  const cur = getReplaySpeed();
  [bSMax,bS05,bS10,bS20].forEach(x=> x.style.fontWeight='');
  const curBtn = ({'max':bSMax,'0.5':bS05,'1':bS10,'2':bS20})[String(cur)] || null;
  if (curBtn) curBtn.style.fontWeight='700';

  holder.append(sel, bPrev, bPlay, bNext, bStop, bRef, speedWrap, zoomWrap);

  let replay = null;
  async function ensureReplay(){ if (!replay) replay = new ReplayController(worker, ev=>onReplayEvent(ev), api); }

  async function refreshRuns(keepSelection=true){
    const current = sel.value || '';
    try{
      const runs = await api.replayRuns(worker);
      sel.innerHTML='';
      (runs||[]).forEach(rm=>{ const o=document.createElement('option'); o.value=rm.id; o.textContent=fmtRunWindow(rm.started_at, rm.finished_at, rm.steps, rm.final_status); sel.appendChild(o); });
      if (keepSelection && current){
        const opt = Array.from(sel.options).find(o=>o.value===current);
        if (opt) sel.value = current;
      }
    }catch{ sel.innerHTML=''; const o=document.createElement('option'); o.textContent='(—)'; sel.appendChild(o); }
  }

  sel.onchange = async ()=>{
    await ensureReplay();
    await replay.setRun(sel.value);
    // Reset the graph to global overview on run change (via callback from process modal)
    try{ if (typeof onResetGraph === 'function') await onResetGraph(); }catch{}
    bPlay.textContent='\u25b6';
  };
  bPrev.onclick = async ()=>{ await ensureReplay(); replay.prev(); };
  bNext.onclick = async ()=>{ await ensureReplay(); replay.next(); };
  bPlay.onclick = async ()=>{
    await ensureReplay();
    const st=replay.getState();
    if (st.playing){ replay.pause(); bPlay.textContent='\u25b6'; }
    else { replay.play(replayIntervalMs()); bPlay.textContent='\u23f8'; }
  };
  bStop.onclick = async ()=>{ await ensureReplay(); replay.stop(); bPlay.textContent='\u25b6'; };
  bRef.onclick = async ()=>{ await refreshRuns(); };

  // Speed handlers
  function applySpeedChoice(btn){
    const sp = btn.getAttribute('data-speed');
    setReplaySpeed(sp);
    [bSMax,bS05,bS10,bS20].forEach(x=> x.style.fontWeight='');
    btn.style.fontWeight='700';
  }
  bSMax.onclick = ()=> applySpeedChoice(bSMax);
  bS05.onclick  = ()=> applySpeedChoice(bS05);
  bS10.onclick  = ()=> applySpeedChoice(bS10);
  bS20.onclick  = ()=> applySpeedChoice(bS20);

  // Zoom handlers
  zOut.onclick   = ()=>{ try{ modalZoom(dom.stage, -0.12); }catch{} };
  zIn.onclick    = ()=>{ try{ modalZoom(dom.stage, +0.12); }catch{} };
  zReset.onclick = ()=>{ try{ modalResetZoom(dom.stage); }catch{} };

  (async()=>{ await refreshRuns(); try{ const first = sel.options && sel.options[0] && sel.options[0].value; if (first){ await ensureReplay(); await replay.setRun(first); } }catch{} })();

  return { getController: ()=> replay, refreshRuns };
}

function mkBtn(label, title, data){ const b=document.createElement('button'); b.className='btn tooltip'; b.textContent=label; if (data) b.dataset.replay=data; if(title) b.setAttribute('data-tip', title); return b; }


 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
