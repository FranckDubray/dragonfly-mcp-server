// Worker Error Modal — shows rich context when a worker errors (observe/debug/status)
import { createModal } from './modal.js';

function safeJSON(x){ try{ return JSON.stringify(x||{}, null, 2); }catch{ return String(x||''); } }

export async function openWorkerErrorModal(worker, evtOrStatus = {}) {
  const modal = createModal({ title: `Erreur worker — ${worker}`, width: '820px' });

  const info = document.createElement('div');
  info.className='panel';

  const node = String(evtOrStatus.node_executed||'').trim();
  const cycle = String(evtOrStatus.cycle_id||'').trim();
  const phase = String(evtOrStatus.phase||evtOrStatus.status||'').trim();
  const heartbeat = String(evtOrStatus.heartbeat||'').trim();
  const dur = (evtOrStatus.duration_ms!=null)? String(evtOrStatus.duration_ms) : '';
  const errMsg = (evtOrStatus.error && evtOrStatus.error.message) ? String(evtOrStatus.error.message) : String(evtOrStatus.last_error||'');

  const head = document.createElement('div');
  head.innerHTML = `
    <div style="display:grid;grid-template-columns:160px 1fr;gap:8px">
      <div class="k">Phase</div><div class="v">${phase||'—'}</div>
      <div class="k">Node</div><div class="v">${node||'—'}</div>
      <div class="k">Cycle</div><div class="v">${cycle||'—'}</div>
      <div class="k">Durée</div><div class="v">${dur? (dur+' ms'):'—'}</div>
      <div class="k">Heartbeat</div><div class="v">${heartbeat||'—'}</div>
    </div>
  `;
  info.appendChild(head);

  const errTitle = document.createElement('h3'); errTitle.textContent = 'Erreur';
  const err = document.createElement('pre'); err.className='io-pre'; err.textContent = (errMsg||'').trim() || '(pas de message d’erreur)';

  const inTitle = document.createElement('h3'); inTitle.textContent = 'IN (call)';
  const inPre = document.createElement('pre'); inPre.className='io-pre'; inPre.textContent = safeJSON((evtOrStatus.io && evtOrStatus.io.in) || evtOrStatus.call || {});

  const outTitle = document.createElement('h3'); outTitle.textContent = 'OUT (preview)';
  const outPre = document.createElement('pre'); outPre.className='io-pre'; outPre.textContent = String((evtOrStatus.io && evtOrStatus.io.out_preview) ?? evtOrStatus.last_result_preview ?? '');

  const bar = document.createElement('div'); bar.style.cssText='display:flex;gap:8px;margin:6px 0;flex-wrap:wrap;';
  const bCopyIn = document.createElement('button'); bCopyIn.className='btn small'; bCopyIn.textContent='Copier IN';
  const bCopyOut = document.createElement('button'); bCopyOut.className='btn small'; bCopyOut.textContent='Copier OUT';
  const bCopyErr = document.createElement('button'); bCopyErr.className='btn small'; bCopyErr.textContent='Copier erreur';
  const bOpenGraph = document.createElement('button'); bOpenGraph.className='btn small'; bOpenGraph.textContent='Ouvrir le graphe';
  bar.append(bCopyIn, bCopyOut, bCopyErr, bOpenGraph);

  bCopyIn.onclick  = async ()=>{ try{ await navigator.clipboard.writeText(inPre.textContent||''); }catch{} };
  bCopyOut.onclick = async ()=>{ try{ await navigator.clipboard.writeText(outPre.textContent||''); }catch{} };
  bCopyErr.onclick = async ()=>{ try{ await navigator.clipboard.writeText(err.textContent||''); }catch{} };
  bOpenGraph.onclick = async ()=>{
    try{ const mod = await import('./process_modal.js'); await mod.openProcessModal(worker); }catch{}
  };

  modal.body.append(info, errTitle, err, bar, inTitle, inPre, outTitle, outPre);
  modal.open();
}
