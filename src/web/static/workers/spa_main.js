







































// SPA main bootstrap (UMD-friendly)
import { h, formatNum } from './dom.js';
import { api } from './api.js';
import { buildChatModal } from './leader_chat_modal.js';
import { buildLeaderSection } from './leader_section.js';
import { renderHeader } from './header_bar.js';
import { initI18n } from './i18n.js';
import { openProcessModal } from './process_modal.js';

// Expose modal openers to UMD scripts (classic <script>)
try{
  window.__MODALS__ = window.__MODALS__ || {};
  window.__MODALS__.openProcess = openProcessModal;
}catch{}

function loadScript(src){
  return new Promise((resolve, reject)=>{
    const s = document.createElement('script');
    s.src = src; s.async = true; s.onload = ()=>resolve(); s.onerror = (e)=>reject(e);
    document.head.appendChild(s);
  });
}

async function main(){
  try{ console.log('[SPA] /workers boot'); }catch{}
  // Initialize i18n before rendering UI
  try{ await initI18n(); }catch{}

  const root = document.getElementById('app-workers-list'); root.innerHTML = '';
  const wrap = h('div',{class:'wrap'}); root.appendChild(wrap);

  // Preload KPIs & leaders (for header only)
  const [kpis, leadersResp] = await Promise.all([
    api.kpis(),
    fetch('/workers/api/leaders').then(r=>r.json()).catch(()=>({leaders:[]}))
  ]);
  const leaders = (leadersResp && leadersResp.leaders) || [];
  const stored = sessionStorage.getItem('workers_ui_leader')||'';
  // Default: if none stored, select the first detected leader so the Leader section is visible
  const selected = (stored && leaders.find(l => (l.name||'') === stored)?.name)
    ? stored
    : (leaders[0]?.name || '');
  try{ console.log('[SPA] leaders:', leaders.length, 'selected:', selected||'(none)'); }catch{}

  const k = {
    workers: kpis.workers ?? '—',
    leaders: (leaders || []).length,          // <- ajout nombre de leaders
    actifs: kpis.actifs ?? '—',
    steps24h: kpis.steps24h ?? '—',
    tokens24h: kpis.tokens24h ?? '—',
    qualite7j: kpis.qualite7j ?? '—'
  };
  const headerEl = await renderHeader(k, leaders, selected, { onAddLeader: async () =>{
    const mod = await import('./leader_identity_modal.js');
    mod.openLeaderIdentityModal('', {}, (newSlug)=>{ try{ const t = import('./toast.js').then(m=>m.toast('Leader créé')); }catch{} }, {mode:'create'});
  }});
  wrap.appendChild(headerEl);

  // Leader section (card) with open global chat
  if (selected){
    try{
      const chosen = leaders.find(l => (l.name||'') === selected);
      if (chosen){
        const leaderData = { name: chosen.name, ...(chosen.identity||{}) };
        const sec = buildLeaderSection(leaderData, ()=>{
          const ev = new CustomEvent('leader:openGlobalChat', {detail:{leader:selected}});
          window.dispatchEvent(ev);
        });
        wrap.appendChild(sec);
      }
    }catch{}
  }

  // Optional debug: test /tools registry load when ?wgdebug=1
  try{
    const qs = new URLSearchParams(location.search);
    if (qs.get('wgdebug') === '1'){
      console.log('[SPA] /tools registry debug: start');
      try{
        const reg = await api.toolsRegistry();
        console.log('[SPA] /tools registry debug: ok', Array.isArray(reg?.tools)? reg.tools.length : (reg && Object.keys(reg||{}).length));
      }catch(e){ console.warn('[SPA] /tools registry debug: error', e); }
    }
  }catch{}

  // Global Leader Chat modal (listens to events from cards)
  const chat = buildChatModal({ title: 'Leader — Global chat' });
  chat.closeModal(); // keep hidden initially
  window.addEventListener('leader:openGlobalChat', (e)=>{
    const leader = (e.detail||{}).leader||'';
    if (!leader) return;
    chat.setLeader(leader);
    chat.setTitle(`Leader — Global chat (@${leader})`);
    chat.refresh();
    chat.attach(async (message)=>{
      const p = new URLSearchParams({name: leader, message, model: 'gpt-5-mini', history_limit: '20'});
      const r = await fetch(`/workers/api/leader_chat_global?${p.toString()}`, {method:'POST'});
      return r.json();
    });
    chat.open();
  });

  // Build grid (UMD): load workers_grid.js as classic script, then call window.WorkersGrid
  try{
    console.log('[SPA] loading workers_grid.js');
    await loadScript(`/static/workers/workers_grid.js?v=${Date.now()}`);
    if (window.WorkersGrid && typeof window.WorkersGrid.buildWorkersGrid === 'function'){
      console.log('[SPA] WorkersGrid found, building grid…');
      await window.WorkersGrid.buildWorkersGrid(wrap, selected);
    } else {
      throw new Error('WorkersGrid not found');
    }
  }catch(err){
    console.error('Failed to load workers_grid.js (UMD)', err);
    const panel = h('div',{class:'panel'}, [
      h('h3',{}, 'Chargement des workers'),
      h('div',{class:'hint'}, 'Impossible de charger la grille. Essayez de recharger la page (Ctrl+F5).')
    ]);
    wrap.appendChild(panel);
  }
}

main();

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
