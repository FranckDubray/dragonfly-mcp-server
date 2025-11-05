
// Wiring for toolbar actions and keyboard shortcuts for GraphView
import { DebugControls } from './debug_controls.js';
import { api } from './api.js';
import { setReplaySpeed, getReplaySpeed, replayIntervalMs } from './process_utils.js';
import { t } from './i18n.js';
import { resolveWorkerFile, waitForPhase } from './graph_view_support.js';

export function wireToolbarAndShortcuts(view){
  const bar = document.querySelector('.graph-toolbar');
  if (!bar) return;

  // Click handlers
  bar.addEventListener('click', async (e)=>{
    const b = e.target.closest('button[data-act]');
    if(b){
      const act = b.dataset.act;
      if (act==='process') return view.core.render('process');
      if (act==='current') return view.core.render('current_subgraph');
      if (act==='overview') return view.core.render('overview');
      if (act==='mode-observe'){ view.streams.stopDebugStream(); view.streams.startObserve(); removeReplayBadge(bar); return; }
      if (act==='mode-debug-stream'){ view.streams.stopObserve(); view.streams.startDebugStream(); removeReplayBadge(bar); return; }
      if (act==='mode-replay'){
        try{
          const list = await api.replayRuns(view.core.worker);
          injectReplayControls(bar, list, view.streams, view.core.worker);
          addReplayBadge(bar);
          const firstId = list && list[0] && list[0].id;
          if (firstId){ await view.streams.startReplay(firstId); }
          else { await view.streams.startReplay(''); }
        }catch{}
        return;
      }
      if (act==='start-debug'){
        view.core.gc.clear();
        const wf = await resolveWorkerFile(view.core.worker);
        try{ await api.startDebug(view.core.worker, wf); }catch(err){ console.warn('[start-debug] error', err); }
        await waitForPhase(view.core.worker, ['starting','running'], 5000, 220);
        await view.core.render('current_subgraph');
        return;
      }
      if (act==='start-observe'){
        view.core.gc.clear();
        const wf = await resolveWorkerFile(view.core.worker);
        try{ await api.startObserve(view.core.worker, wf); }catch(err){ console.error('[START-OBSERVE] network error', err); }
        const ph = await waitForPhase(view.core.worker, ['starting','running'], 5000, 220);
        await view.core.render('current_subgraph');
        view.streams.stopDebugStream();
        view.streams.startObserve();
        removeReplayBadge(bar);
        return;
      }
    }

    const cb = e.target.closest('input[type="checkbox"][data-opt]');
    if (cb){
      view.core.readOpts();
      const kind = view.core.currentKind || 'process';
      await view.core.render(kind);
      return;
    }
  });

  // Initialize speed visual
  try{
    const cur = getReplaySpeed();
    const btn = bar.querySelector(`.btn[data-speed="${cur}"]`);
    if (btn) btn.style.fontWeight = '700';
  }catch{}

  // Zoom buttons
  wireZoomButtons(view);
  // Ctrl/Cmd + wheel
  wireCtrlWheelZoom(view);

  // Keyboard shortcuts (with replay overrides)
  window.addEventListener('keydown', (e)=>{
    if (e.target && /input|textarea|select/.test((e.target.nodeName||'').toLowerCase())) return;
    const k = e.key;
    if (view.streams && view.streams.mode === 'replay'){
      if (k === ' '){ e.preventDefault(); const st=view.streams.replayState(); if (st.playing) view.streams.replayPause(); else view.streams.replayPlay(replayIntervalMs()); return; }
      if (k === 'ArrowLeft'){ e.preventDefault(); view.streams.replayPrev(); return; }
      if (k === 'ArrowRight'){ e.preventDefault(); view.streams.replayNext(); return; }
      if (k.toLowerCase() === 's'){ e.preventDefault(); view.streams.stopReplay(); return; }
    }
    const kl = k.toLowerCase();
    if (kl==='g'){ view.core.render('process'); }
    if (kl==='h'){ view.core.render('current_subgraph'); }
    if (kl==='o'){ view.core.render('overview'); }
    if (kl==='+' || kl==='='){ view._applyZoom(+0.12); }
    if (kl==='-'){ view._applyZoom(-0.12); }
    if (kl==='0'){ view._resetZoom(); }
    if (kl==='\u21f5' || kl==='f'){ view._fitHeight(); }
    if (view.streams.mode !== 'replay'){
      if (kl==='s'){ DebugControls.step(view.core.worker); }
      if (kl==='c'){ DebugControls.cont(view.core.worker); }
    }
    if (kl==='x'){ api.stop(view.core.worker); }
  });
}

function wireZoomButtons(view){
  const bar = document.querySelector('.graph-toolbar'); if (!bar) return;
  bar.addEventListener('click', async (e)=>{
    const b = e.target.closest('button[data-act]');
    if (b && b.dataset.act==null){
      const sp = b.getAttribute('data-speed');
      if (sp){
        setReplaySpeed(sp);
        bar.querySelectorAll('.btn[data-speed]').forEach(x=> x.style.fontWeight='');
        b.style.fontWeight='700';
        return;
      }
    }
    if (!b) return;
    const act = b.getAttribute('data-act');
    if (act === 'zoom-in'){ view._applyZoom(+0.12); }
    if (act === 'zoom-out'){ view._applyZoom(-0.12); }
    if (act === 'zoom-reset'){ view._resetZoom(); }
    if (act === 'zoom-fit-height'){ view._fitHeight(); }
  });
}

function wireCtrlWheelZoom(view){
  const stage = document.querySelector('.graph-stage');
  if (!stage) return;
  stage.addEventListener('wheel', (e)=>{
    try{
      if (e.ctrlKey || e.metaKey){
        e.preventDefault();
        const dir = e.deltaY < 0 ? +1 : -1;
        view._applyZoom(dir * 0.12);
      }
    }catch{}
  }, { passive: false });
}

// Inline helpers copied from original file (must be in the same module scope)
function injectReplayControls(bar, runsMeta, streams, worker){
  try{
    let host = bar.querySelector('[data-replay-host]');
    if (!host){
      host = document.createElement('div');
      host.className = 'group';
      host.setAttribute('data-replay-host','');
      bar.appendChild(host);
    }
    host.innerHTML = '';
    const badge = document.createElement('span'); badge.className='badge'; badge.textContent='Replay'; badge.style.marginRight='6px'; badge.setAttribute('title','Mode replay (lecture d\'un run précédent)');
    const sel = document.createElement('select'); sel.setAttribute('aria-label', 'Run'); sel.style.minWidth='260px'; sel.style.height='34px'; sel.style.padding='6px 10px'; sel.setAttribute('title','Sélectionner un run à rejouer');
    (runsMeta||[]).forEach(rm=>{ const o = document.createElement('option'); o.value = rm.id; o.textContent = rm.id; sel.appendChild(o); });
    const bPrev = mkBtn('\u25c0\ufe0e','prev','Étape précédente');
    const bPlay = mkBtn('\u23f5','play','Lire / Pause');
    const bNext = mkBtn('\u25b6\ufe0e','next','Étape suivante');
    const bStop = mkBtn('\u23f9','stop','Arrêter la lecture');
    const bRef  = mkBtn('\u27f3','refresh','Rafraîchir la liste des runs');
    const bS05 = mkBtn('0.5\u00d7',null,'Vitesse x0.5'); bS05.setAttribute('data-speed','0.5');
    const bS10 = mkBtn('1\u00d7',  null,'Vitesse x1 (par défaut)'); bS10.setAttribute('data-speed','1');
    const bS20 = mkBtn('2\u00d7',  null,'Vitesse x2'); bS20.setAttribute('data-speed','2');

    const cur = getReplaySpeed();
    [bS05,bS10,bS20].forEach(x=> x.style.fontWeight = '');
    const curBtn = ({'0.5':bS05,'1':bS10,'2':bS20})[String(cur)];
    if (curBtn) curBtn.style.fontWeight = '700';

    host.append(badge, sel, bPrev, bPlay, bNext, bStop, bRef, bS05, bS10, bS20);

    sel.onchange = async ()=>{ await streams.startReplay(sel.value); };
    bPrev.onclick = ()=> streams.replayPrev();
    bNext.onclick = ()=> streams.replayNext();
    bPlay.onclick = ()=>{ const st = streams.replayState(); if (st.playing) streams.replayPause(); else streams.replayPlay(replayIntervalMs()); };
    bStop.onclick = ()=> streams.stopReplay();
    bRef.onclick  = async ()=>{ try{ const list = await api.replayRuns(worker); injectReplayControls(bar, list, streams, worker); if (list && list[0]) sel.value = list[0].id; }catch{} };

    bS05.onclick = ()=>{ setReplaySpeed(0.5); [bS05,bS10,bS20].forEach(x=> x.style.fontWeight = ''); bS05.style.fontWeight='700'; };
    bS10.onclick = ()=>{ setReplaySpeed(1);   [bS05,bS10,bS20].forEach(x=> x.style.fontWeight = ''); bS10.style.fontWeight='700'; };
    bS20.onclick = ()=>{ setReplaySpeed(2);   [bS05,bS10,bS20].forEach(x=> x.style.fontWeight = ''); bS20.style.fontWeight='700'; };
  }catch{}
}
function mkBtn(label, data, tip){ const b=document.createElement('button'); b.className='btn'; b.textContent=label; if (data) b.dataset.replay=data; if(tip) b.setAttribute('title', tip); return b; }
function addReplayBadge(bar){ try{ const g=bar.querySelector('[data-replay-host]'); if (!g) return; if (!g.querySelector('.badge')){ const s=document.createElement('span'); s.className='badge'; s.textContent='Replay'; s.style.marginRight='6px'; g.prepend(s);} }catch{} }
function removeReplayBadge(bar){ try{ const g=bar.querySelector('[data-replay-host]'); if (!g) return; g.querySelectorAll('.badge').forEach(n=>n.remove()); }catch{} }
