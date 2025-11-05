




















import { h } from './dom.js';
import { openAddWorkerModal } from './add_worker_ui.js';
import { t, setLang, getLang, listAvailableLangsDetailed } from './i18n.js';

function toTitle(s){ try{ s=String(s||'').trim(); if(!s) return ''; return s.split(/\s+/).map(w=> w.charAt(0).toUpperCase()+w.slice(1)).join(' '); }catch{return String(s||'');} }
function firstFromSlug(slug){ try{ const last=(String(slug||'').split('_').filter(Boolean).pop()||String(slug||'')); return toTitle(last.replace(/[-]+/g,' ')); }catch{ return String(slug||''); } }

function langLabel(code, flag, native){
  let name = t(`lang.${code}`, code);
  if (name === code && native) name = native;
  return `${flag||''} ${name}`.trim();
}

function buildLangDropdown(avail){
  const host = document.createElement('div');
  host.style.cssText = 'position:relative;';
  const current = getLang();
  const cur = avail.find(x=>x.code===current) || avail[0] || {code: current, flag:'', native: current};
  const curLabel = langLabel(cur.code, cur.flag, cur.native);

  const btn = document.createElement('button');
  btn.className = 'btn';
  btn.type = 'button';
  btn.textContent = curLabel || '🌐 Lang';
  btn.setAttribute('aria-haspopup','true');
  btn.setAttribute('aria-expanded','false');

  const panel = document.createElement('div');
  panel.style.cssText = 'position:absolute; right:0; top:42px; background:#fff; color:var(--ink); border:1px solid var(--border); border-radius:12px; box-shadow:0 16px 48px rgba(0,0,0,.18); padding:10px; z-index:10000; width:min(560px, 86vw); max-height:60vh; overflow:auto; display:none;';
  panel.setAttribute('role','menu');

  // Grid two columns
  const grid = document.createElement('div');
  grid.style.cssText = 'display:grid; grid-template-columns:1fr 1fr; gap:6px;';

  // Alphabetical list already sorted upstream (label)
  avail.forEach(({code, flag, native, label})=>{
    const item = document.createElement('button');
    item.type = 'button';
    item.className = 'btn ghost';
    item.style.cssText = 'justify-content:flex-start; text-align:left;';
    item.textContent = label || langLabel(code, flag, native);
    item.setAttribute('role','menuitem');
    item.dataset.code = code;
    if (code===current){ item.style.fontWeight='700'; }
    item.addEventListener('click', ()=>{
      try{ setLang(code); }catch{}
      location.reload();
    });
    grid.appendChild(item);
  });

  panel.appendChild(grid);

  function open(){ panel.style.display='block'; btn.setAttribute('aria-expanded','true'); document.addEventListener('mousedown', onDoc, true); document.addEventListener('keydown', onKey, true); }
  function close(){ panel.style.display='none'; btn.setAttribute('aria-expanded','false'); document.removeEventListener('mousedown', onDoc, true); document.removeEventListener('keydown', onKey, true); }
  function onDoc(e){ if (!panel.contains(e.target) && e.target!==btn) close(); }
  function onKey(e){ if (e.key==='Escape'){ e.preventDefault(); close(); btn.focus(); } }
  btn.addEventListener('click', () =>{ const shown = panel.style.display!=='none'; if (shown) close(); else open(); });

  host.append(btn, panel);
  return host;
}

export async function renderHeader(kpis, leaders, selectedLeader, {onAddLeader}={}){
  let availDetailed = await listAvailableLangsDetailed();
  // Sort alphabetically by label in current language (fallback native)
  try{
    availDetailed = availDetailed
      .map(it => ({...it, label: langLabel(it.code, it.flag, it.native)}))
      .sort((a,b)=> a.label.localeCompare(b.label));
  }catch{}

  const langDropdown = buildLangDropdown(availDetailed);

  const actions = [
    h('button',{class:'btn tooltip',title:t('header.add_leader'), 'data-act':'add-leader','data-tip':t('header.add_leader')}, t('header.add_leader')),
    h('button',{class:'btn tooltip',title:t('header.add_worker'), 'data-act':'add-worker','data-tip':t('header.add_worker')}, t('header.add_worker')),
    langDropdown,
  ];

  const leaderSelWrap = h('div',{style:'display:flex;align-items:center;gap:8px'});
  if (Array.isArray(leaders) && leaders.length){
    const lab = h('span',{class:'lab',style:'font-size:12px;color:var(--muted)'}, t('header.leader'));
    const sel = h('select',{ 'aria-label':'Leader', class:'input', style:'min-width:200px;height:34px;padding:6px 10px' });
    leaders.forEach(l=>{
      const opt = document.createElement('option');
      opt.value = l.name; // slug
      const raw = (l.identity && l.identity.display_name) ? String(l.identity.display_name).trim() : '';
      const label = raw && !/_/.test(raw) ? raw : firstFromSlug(l.name);
      opt.textContent = label;
      if (l.name === selectedLeader) opt.selected = true;
      sel.appendChild(opt);
    });
    sel.addEventListener('change', () =>{
      const name = sel.value||'';
      try{ sessionStorage.setItem('workers_ui_leader', name); }catch{}
      location.reload();
    });
    leaderSelWrap.append(lab, sel);
  }

  const tiles = [
    [t('kpis.workers'), kpis.workers],
    [t('kpis.leaders','Leaders'), (typeof kpis.leaders==='number' ? kpis.leaders : (leaders||[]).length)],
    [t('kpis.actifs'), kpis.actifs],
    [t('kpis.steps24h'), kpis.steps24h ?? '—'],
    [t('kpis.tokens24h'), kpis.tokens24h ?? '—'],
    [t('kpis.qualite7j'), kpis.qualite7j ?? '—'],
  ];

  const headerRight = h('div', {class:'kpis'}, [
    ...tiles.map(([lab,val]) =>
      h('div',{class:'k'},[ h('span',{class:'lab'},lab), h('span',{class:'val'}, String(val??'—')) ])
    ),
    leaderSelWrap,
    ...actions,
  ]);

  const bar = h('header', {class:'top'}, [
    h('div', {class:'brand'}, [ h('h1',{}, t('header.title')) ]),
    headerRight
  ]);

  bar.addEventListener('click', async (e)=>{
    const el = e.target.closest('button[data-act]'); if(!el) return;
    const act = el.getAttribute('data-act');
    try{
      if (act==='add-worker'){
        await openAddWorkerModal(); return;
      }
      if (act==='add-leader' && typeof onAddLeader==='function'){
        await onAddLeader(); return;
      }
    }catch(err){ console.error('[header action error]', err); }
  });
  return bar;
}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 