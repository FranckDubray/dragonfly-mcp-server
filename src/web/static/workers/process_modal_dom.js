

















import { t } from './i18n.js';
import { setAura, formatLocalTimeShort } from './process_utils.js';

export function initHeader(modal, { avatarUrl, display, initialMode='live' }){
  let headerAvatar = null, headerBadge = null, modeBadge = null;
  let headerFreeze = (String(initialMode||'live').toLowerCase()==='freeze');
  let liveAvailable = false; // devient true une fois observe/debug démarré
  let headerMode = '';

  function setHeaderVisual(kind){
    try{
      const p = String(kind||'').toLowerCase();
      let labelKey = 'status.idle'; let fallback = 'Idle';
      if (p==='failed'){ labelKey='status.failed'; fallback='Failed'; }
      else if (p==='running'){ labelKey='status.running'; fallback='Running'; }
      else if (p==='starting'){ labelKey='status.starting'; fallback='Starting'; }
      else if (p==='completed'){ labelKey='status.completed'; fallback='Completed'; }
      else if (p==='canceled'){ labelKey='status.canceled'; fallback='Canceled'; }
      else if (p==='tool'){ labelKey='status.tool'; fallback='Tool'; }
      else if (p==='sleep'){ labelKey='status.sleep'; fallback='Sleeping'; }
      if (headerBadge){ headerBadge.textContent = t(labelKey, fallback); }
      if (headerAvatar){ setAura(headerAvatar, {phase: (p==='tool'||p==='sleep') ? 'running' : p}); }
    }catch{}
  }

  function setFreezeUi(){
    try{
      freezeBtn.textContent = headerFreeze ? 'Freeze' : 'Live';
      freezeBtn.classList.toggle('primary', headerFreeze);
      freezeBtn.setAttribute('aria-pressed', headerFreeze? 'true':'false');
    }catch{}
  }

  function setMode(mode){
    headerMode = String(mode||'').toLowerCase();
    try{
      let txt = '';
      if (headerMode==='observe') txt = 'Observe';
      else if (headerMode==='debug') txt = 'Debug';
      else if (headerMode==='replay') txt = 'Replay';
      else txt = '';
      modeBadge.style.display = txt ? '' : 'none';
      modeBadge.textContent = txt;
    }catch{}
  }

  // Build header avatar + status + freeze button + mode badge
  headerAvatar = document.createElement('div');
  headerAvatar.className = 'avatar aura a--stop-ok';
  headerAvatar.style.width = '28px'; headerAvatar.style.height = '28px'; headerAvatar.style.borderWidth = '2px'; headerAvatar.style.flexShrink = '0';
  const pic = document.createElement('div'); pic.className = 'img'; if (avatarUrl) pic.style.backgroundImage = `url('${avatarUrl.replace(/'/g,"%27")}')`;
  headerAvatar.appendChild(pic);

  headerBadge = document.createElement('span'); headerBadge.className = 'badge'; headerBadge.style.marginLeft='6px'; headerBadge.textContent = t('status.idle','Idle');

  modeBadge = document.createElement('span'); modeBadge.className = 'badge'; modeBadge.style.marginLeft='6px'; modeBadge.style.display='none';

  const freezeBtn = document.createElement('button'); freezeBtn.className = 'btn small'; freezeBtn.type='button';
  freezeBtn.addEventListener('click', () =>{
    if (!liveAvailable && !headerFreeze){
      // Live indisponible: rester en Freeze
      freezeBtn.blur();
      return;
    }
    headerFreeze = !headerFreeze; setFreezeUi();
  });

  const holder = document.createElement('div'); holder.style.display='flex'; holder.style.alignItems='center'; holder.style.gap='6px';
  holder.append(headerAvatar, headerBadge, modeBadge, freezeBtn);
  modal.header.insertBefore(holder, modal.titleEl);
  setHeaderVisual('idle');
  setFreezeUi();

  function setLiveAvailable(avail){
    liveAvailable = !!avail;
    try{
      if (!liveAvailable){ headerFreeze = true; setFreezeUi(); }
      freezeBtn.disabled = !liveAvailable && !headerFreeze; // Live non dispo => on autorise seulement Freeze
    }catch{}
  }

  return {
    setHeaderVisual,
    setMode,
    upd: (kind)=>{ if (!headerFreeze) setHeaderVisual(kind); },
    setFreeze: (b)=>{ headerFreeze = !!b; setFreezeUi(); },
    setLiveAvailable,
    isFreeze: () => headerFreeze,
  };
}

export function buildStage(modal){
  const status = document.createElement('div'); status.className = 'help-text';
  const panel = document.createElement('div'); panel.className = 'panel';

  // Title row with back button
  const titleRow = document.createElement('div');
  titleRow.style.cssText = 'display:flex; align-items:center; justify-content:space-between; gap:8px;';

  const title = document.createElement('h3'); title.textContent = t('toolbar.process','Processus');

  const backBtn = document.createElement('button');
  backBtn.className = 'btn small';
  backBtn.type = 'button';
  backBtn.textContent = '← ' + t('common.back','Back');
  backBtn.title = t('common.back','Back');
  backBtn.style.display = 'none'; // hidden until subgraph
  backBtn.setAttribute('data-role','graph-back');

  titleRow.append(title, backBtn);

  const row = document.createElement('div'); row.style.cssText = 'display:flex; gap:12px; min-height:0; align-items:stretch;';
  const leftCol = document.createElement('div'); leftCol.style.cssText = 'flex:1 1 auto; min-width:0; display:flex; flex-direction:column; min-height:0;';
  const stage = document.createElement('div'); stage.className = 'graph-stage--modal'; stage.setAttribute('role','region'); stage.setAttribute('aria-label', t('graph.aria_label','Graph Mermaid')); stage.style.flex = '1 1 auto';
  // Désactiver tout auto-center de Highlighter pour éviter le fallback de zoom
  stage.dataset.autoCenter = 'false';
  leftCol.appendChild(stage);
  const side = document.createElement('div'); side.style.cssText = 'flex:0 0 360px; max-width:38vw; min-width:280px; border-left:1px solid var(--border); padding-left:12px; display:flex; flex-direction:column; gap:8px; overflow:auto;';
  const sideTitle = document.createElement('h3'); sideTitle.textContent = t('io.title','Entrées/Sorties du nœud');
  const curLine = document.createElement('div'); curLine.style.cssText = 'font-size:12px; color:#6b7280; display:flex; align-items:center; gap:8px; flex-wrap:wrap;';
  const curLabelKey = document.createElement('span'); curLabelKey.textContent = `${t('common.current_step','Step courant')}:`;
  const curLabelVal = document.createElement('strong'); curLabelVal.style.cssText='font-size:12px; overflow:hidden; text-overflow:ellipsis;';
  const curTs = document.createElement('span'); curTs.className='hint'; curTs.textContent = '';
  const pendingBadge = document.createElement('span'); pendingBadge.className='badge'; pendingBadge.textContent = `${t('common.pending','En attente')} SSE: 0`;
  curLine.append(curLabelKey, curLabelVal, curTs, pendingBadge);
  const inTitle = document.createElement('div'); inTitle.className='hint'; inTitle.textContent = t('io.in','IN'); const inBox = document.createElement('div'); inBox.className='panel'; inBox.style.cssText='max-height:22vh; overflow:auto;';
  const outTitle = document.createElement('div'); outTitle.className='hint'; outTitle.textContent = t('io.out','OUT'); const outBox = document.createElement('div'); outBox.className='panel'; outBox.style.cssText='max-height:22vh; overflow:auto;';
  const errTitle = document.createElement('div'); errTitle.className='hint'; errTitle.textContent = t('io.error','ERREUR'); errTitle.style.display='none'; const errBox = document.createElement('pre'); errBox.className='io-pre'; errBox.style.cssText='max-height:18vh; overflow:auto; display:none;';

  side.append(sideTitle, curLine, inTitle, inBox, outTitle, outBox, errTitle, errBox);
  row.append(leftCol, side); panel.append(titleRow, row); modal.body.append(status, panel);

  return {
    dom: { status, panel, stage, inBox, outBox, errTitle, errBox, curLabelVal, curTs, backBtn },
    setCurrent: (node)=>{ try{ curLabelVal.textContent = String(node||'').trim(); }catch{} },
    setStepTs: (iso)=>{ try{ curTs.textContent = iso ? `@ ${formatLocalTimeShort(iso)}` : ''; }catch{} },
  };
}

 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
