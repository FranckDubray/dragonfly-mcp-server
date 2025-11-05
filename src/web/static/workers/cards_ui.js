















import { h, phaseDot, frPhase, toolClass, gaugeRatio } from './dom.js';
import { openProcessModal } from './process_modal.js';
import { openLeaderIdentityModal } from './leader_identity_modal.js';
import { t } from './i18n.js';

// --- Smoothing / state memories ---
const EMA = new Map();      // worker -> ema rate (t/s normalized)
const ANG = new Map();      // worker -> last angle (deg)
const HYST = new Map();     // worker -> {active:boolean, lastStepTs:number}
const STEPISO = new Map();  // worker -> last last_step_at iso (for spark)
let CHRONO_TICK = null;     // interval id for continuous chrono update

function normalizeRatePerSec(ar){
  try{
    const v = Number(ar?.value||0);
    const u = String(ar?.unit||'t/s');
    if (u === 't/s') return v;
    if (u === 't/10s') return v/10;
    if (u === 't/min') return v/60;
    return 0;
  }catch{ return 0; }
}

function resolveAsset(url){
  const u = String(url||'').trim();
  if (!u) return '';
  if (/^https?:\/\//i.test(u)) return u;
  if (u.startsWith('/')) return u; // already absolute
  return `/docs/images/${u}`;
}

function toTitle(s){ try{ s=String(s||'').trim(); if(!s) return ''; return s.charAt(0).toUpperCase()+s.slice(1); }catch{ return String(s||''); } }
function firstFromSlug(wn){ try{ const last=(String(wn||'').split('_').filter(Boolean).pop()||String(wn||'')); return toTitle(last.replace(/[-]+/g,' ')); }catch{ return String(wn||''); } }

function pickDisplayName(rec){
  const dn = (rec.display_name && String(rec.display_name).trim()) || '';
  const looksSlug = (!!dn && (/_/.test(dn) || /^[a-z0-9_]+$/.test(dn) || dn.length > 24));
  if (!dn || looksSlug) return firstFromSlug(rec.worker_name);
  return dn;
}

function humanizeAgo(iso){
  try{ if(!iso) return '—'; const t=new Date(iso).getTime(); if(!t) return '—'; const s=Math.max(0,(Date.now()-t)/1000); if(s<60) return `${Math.floor(s)}s`; const m=s/60; if(m<60) return `${Math.floor(m)}m`; const h=m/60; if(h<24) return `${Math.floor(h)}h`; const d=h/24; return `${Math.floor(d)}j`; }catch{ return '—'; }
}
function fmtMMSS(elapsedSec){ try{ const s=Math.max(0, Math.floor(elapsedSec)); const m=Math.floor(s/60), ss=String(s%60).padStart(2,'0'); return `${m}:${ss}`; }catch{ return '0:00'; }

function ensureChronoTick(){
  if (CHRONO_TICK) return;
  CHRONO_TICK = setInterval(()=>{
    // Update all running tool chronos continuously (every ~500ms)
    document.querySelectorAll('.card').forEach(card=>{
      const startedIso = card.dataset.toolStarted || '';
      if (!startedIso) return;
      const started = Date.parse(startedIso);
      if (!Number.isFinite(started)) return;
      const elapsed = Math.max(0, Math.floor((Date.now()-started)/1000));
      const mm = Math.floor(elapsed/60), ss = String(elapsed%60).padStart(2,'0');
      const chrono = card.querySelector('.tools .tool.running .chrono');
      if (chrono) chrono.textContent = `${mm}:${ss}`;
    });
  }, 500);
}

// ===== Avatar aura helper =====
function setAvatarAura(card, {phase, running_kind, sleeping}){
  try{
    const av = card.querySelector('.avatar'); if (!av) return;
    av.classList.add('aura');
    av.classList.remove('a--running','a--tool','a--sleep','a--stop-ok','a--stop-err');
    const p = String(phase||'').toLowerCase();
    const rk = String(running_kind||'');
    if (p === 'failed'){ av.classList.add('a--stop-err'); return; }
    if (rk === 'tool'){ av.classList.add('a--tool'); return; }
    if (p === 'running' || p === 'starting'){
      if (sleeping) av.classList.add('a--sleep'); else av.classList.add('a--running');
      return;
    }
    av.classList.add('a--stop-ok');
  }catch{}
}

export function buildCard(rec){
  const avatarUrl = resolveAsset(rec.avatar_url);
  const avatar = h('div',{class:'avatar', title:t('common.edit_identity')},[
    h('div',{class:'img',style: avatarUrl ? `background-image:url('${avatarUrl.replace(/'/g,"%27")}')` : ''}),
    h('span',{class:'state-dot '+phaseDot(rec.phase)})
  ]);

  const disp = pickDisplayName(rec);

  // Name line
  const leaderName = (rec.leader || '').trim();
  const nameLineChildren = [];
  nameLineChildren.push(h('div',{class:'name'}, disp));
  const statusChip = h('div',{class:'status-chip', title:t('common.worker_status')}, frPhase(rec.phase) || '—');
  nameLineChildren.push(statusChip);
  const toolBadge = h('span',{class:'tool-badge', 'data-role':'tool-badge', style:'display:none'}, 'TOOL');
  nameLineChildren.push(toolBadge);
  if (leaderName){ nameLineChildren.push(h('span',{class:'leader-badge', title:`Leader: @${leaderName}`},[ h('span',{class:'at'}, `@${leaderName}`) ])); }

  const who = h('div',{class:'who'},[
    h('div',{class:'name-line'}, nameLineChildren),
    rec.last_step_at ? h('div',{class:'meta-sm'}, `${t('common.last_step')||'Last step'}: ${humanizeAgo(rec.last_step_at)}`) : null,
  ].filter(Boolean));

  // Gauge with needle + hub + legend (mini)
  const gauge = h('div',{class:'gauge'}, [
    h('div',{class:'gval'}, [ h('div',{class:'gnum'}, '0.0'), h('div',{class:'glab'}, 'steps/mn') ]),
    h('div',{class:'needle'}),
    h('div',{class:'hub'})
  ]);
  const gleg = h('div',{class:'gleg','data-role':'gleg'}, '');
  const gwrap = h('div',{class:'gwrap'}, [gauge, gleg]);

  const head = h('div',{class:'card-head'},[ avatar, who, gwrap ]);

  // Tools row (chips)
  const toolsRow = h('div',{class:'tools'},[ h('span',{class:'label'},'Tools') ]);
  (rec.tools_used||[]).forEach(name=>{
    const chip = h('div',{class:`tool ${toolClass(name)}`,'data-tool':name},[ name ]);
    toolsRow.appendChild(chip);
  });

  const actions = h('div',{class:'card-actions'},[
    h('button',{class:'btn primary small','data-act':'process'}, `🧭 Processus`),
  ]);

  const card = h('article',{class:'card modern','data-worker':rec.worker_name, role:'article', 'aria-label':`Worker ${disp} — ${frPhase(rec.phase)}`}, [ head, toolsRow, actions ]);

  // Navigation
  card.addEventListener('click', (e)=>{ if (e.target.closest('.card-actions')) return; location.href = `/workers/${encodeURIComponent(rec.worker_name)}`; });
  actions.addEventListener('click', async (e)=>{
    const b = e.target.closest('button[data-act]'); if (!b) return;
    e.stopPropagation();
    const act = b.getAttribute('data-act')||''; const wn = rec.worker_name;
    if (act==='process'){
      await openProcessModal(wn); return;
    }
  });

  // Identity edit on avatar
  avatar.addEventListener('click', async (e)=>{
    e.stopPropagation();
    try{
      const r = await fetch(`/workers/api/identity?worker=${encodeURIComponent(rec.worker_name)}`);
      const js = await r.json();
      const ident = js.identity || {};
      openLeaderIdentityModal(rec.worker_name, ident, (nameSlug, identity)=>{
        try{
          const newDisp = (identity.display_name||disp);
          who.querySelector('.name').textContent = newDisp;
          if (identity.avatar_url){
            const av = avatar.querySelector('.img');
            const url = resolveAsset(identity.avatar_url);
            av && (av.style.backgroundImage = `url('${url.replace(/'/g,"%27")}')`);
          }
        }catch{}
      });
    }catch{}
  });
  avatar.tabIndex = 0;
  avatar.addEventListener('keydown', (e)=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); avatar.click(); }});

  return card;
}

// --- EMA smoothing and angle helper ---
function updateEMA(worker, val, alpha){
  const prev = EMA.get(worker) || 0;
  const cur = alpha * val + (1 - alpha) * prev;
  EMA.set(worker, cur);
  return cur;
}
function smoothAngle(worker, target){
  const prev = (ANG.get(worker) ?? -90);
  const cur = prev + 0.2 * (target - prev);
  ANG.set(worker, cur);
  return cur;
}

// Live visual updater from observe_many_client → apply(ev, {getRate, getAdaptiveRate, getToolProgress})
export function applyObserveUpdate(ev, helpers){
  try{
    const wn = ev?.worker_name||''; if(!wn) return;
    const card = document.querySelector(`.card[data-worker="${CSS.escape(wn)}"]`); if(!card) return;

    const dot = card.querySelector('.state-dot');
    const chip = card.querySelector('.status-chip');
    const g = card.querySelector('.gauge');
    const gnum = card.querySelector('.gnum');
    const glab = card.querySelector('.glab');
    const gleg = card.querySelector('[data-role="gleg"]');
    const needle = card.querySelector('.needle');

    const p = String(ev.phase||'').toLowerCase();
    if (dot){ dot.classList.remove('dot-running','dot-idle','dot-error'); dot.classList.add(p==='failed'?'dot-error':(p.match(/running|starting/)?'dot-running':'dot-idle')); }
    if (chip){ chip.textContent = frPhase(p); }

    // remove gauge state classes
    try{ g && g.classList.remove('spin','pulse','doze'); }catch{}

    // Defaults gauge
    let ringColor = '#10b981'; // green
    let ringRatio = 0;         // 0..1
    let centerVal = '0.0';
    let centerUnit = 'steps/mn';
    let legend = '';

    const rk = String(ev.running_kind||'');
    const rstarted = ev.running_started_at || '';

    // Window label for tooltip from adaptive unit
    const ar = helpers?.getAdaptiveRate ? helpers.getAdaptiveRate(wn) : {value:0, unit:'t/s', ratio:0};
    const ratePerSec = normalizeRatePerSec(ar);
    const perMin = ratePerSec * 60;
    const winSec = (ar.unit==='t/s') ? 1 : (ar.unit==='t/10s' ? 10 : 60);

    // Running tool highlight + chrono
    try{
      const toolsRow = card.querySelector('.tools');
      toolsRow && toolsRow.querySelectorAll('.tool.running').forEach(el=>el.classList.remove('running'));
      if (rk === 'tool'){
        const toolName = String(ev?.last_io_call?.tool || ev?.last_io_call?.tool_name || '').trim();
        let chipEl = null;
        if (toolName){ chipEl = toolsRow && toolsRow.querySelector(`.tool[data-tool="${CSS.escape(toolName)}"]`); }
        if (!chipEl){ chipEl = toolsRow && toolsRow.querySelector('.tool'); }
        if (chipEl){
          chipEl.classList.add('running');
          let chrono = chipEl.querySelector('.chrono');
          if (!chrono){ chrono = document.createElement('span'); chrono.className='chrono'; chipEl.appendChild(chrono); }
          const started = Date.parse(rstarted||'');
          if (Number.isFinite(started)){
            const elapsed = Math.max(0, Math.floor((Date.now() - started)/1000));
            const mm = Math.floor(elapsed/60), ss = String(elapsed%60).padStart(2,'0');
            chrono.textContent = `${mm}:${ss}`;
            // persist started ISO on card for continuous chrono tick
            card.dataset.toolStarted = rstarted;
            ensureChronoTick();
          } else {
            chrono.textContent = '';
            delete card.dataset.toolStarted;
          }
        }
      } else {
        const toolsRow2 = card.querySelector('.tools');
        toolsRow2 && toolsRow2.querySelectorAll('.tool .chrono').forEach(el=> el.textContent='');
        delete card.dataset.toolStarted;
      }
    }catch{}

    // Hysteresis memory for transform activity & spark on new step
    const h = HYST.get(wn) || {active:false, lastStepTs:0};
    const nowMs = Date.now();
    const prevIso = STEPISO.get(wn) || '';
    const curIso = String(ev.last_step_at||'');
    if (curIso && curIso !== prevIso){
      STEPISO.set(wn, curIso);
      // spark flash on gauge
      try{
        const s = document.createElement('div'); s.className='spark'; g && g.appendChild(s);
        setTimeout(()=>{ try{ s.remove(); }catch{} }, 520);
        // combo +1 bubble
        const cb = document.createElement('div'); cb.className='combo'; cb.textContent = '+1'; g && g.appendChild(cb);
        setTimeout(()=>{ try{ cb.remove(); }catch{} }, 350);
      }catch{}
    }

    if (ev.last_step_at){ try{ h.lastStepTs = new Date(ev.last_step_at).getTime() || h.lastStepTs; }catch{} }
    const since = nowMs - (h.lastStepTs||0);
    const isBurstActive = (ratePerSec>0.2) || (since < 500);
    const shouldBeActive = (p==='running' && rk!=='tool' && isBurstActive);
    if (shouldBeActive) h.active = true; else if (since > 1500) h.active = false;
    HYST.set(wn, h);

    // Mode → mapping ratio and colors
    if (p==='failed'){
      ringColor = '#ef4444'; ringRatio=1; centerVal='ERR'; centerUnit=''; legend='';
    } else if (p==='completed' || p==='canceled'){
      ringColor = '#60a5fa'; ringRatio=0; centerVal='0.0'; centerUnit='steps/mn'; legend='stopped';
    } else if ((p==='' || p==='unknown') && !ev.last_step_at){
      ringColor = '#9ca3af'; ringRatio=0; centerVal='—'; centerUnit=''; legend='never started';
    } else if (rk === 'tool'){
      ringColor = '#8b5cf6'; if (g) g.classList.add('pulse');
      // tool: stable low regime ~0.28; center shows steps/mn for consistency
      updateEMA(wn, 0.0, 0.1);
      ringRatio = 0.28; centerVal = String((perMin||0).toFixed(1)); centerUnit='steps/mn';
      legend = (rstarted ? `tool ${humanizeAgo(rstarted)}` : 'tool');
    } else if (p==='running' || p==='starting'){
      // Transform active/idle with smoothing and anti-jitter
      const ema = updateEMA(wn, ratePerSec, 0.25);
      const k = 0.8; // compression
      const mapped = 1 - Math.exp(-k * Math.max(0, ema));
      ringRatio = Math.max(0, Math.min(1, mapped));
      ringColor = (ema>0 ? '#f59e0b' : '#10b981');
      centerVal = String((perMin||0).toFixed(1));
      centerUnit = 'steps/mn';
      if (h.active && g) g.classList.add('spin');
      // proportional spin speed
      try{
        const spinDur = Math.max(1.2, 2.8 - 1.6 * Math.min(perMin/120, 1));
        g && g.style.setProperty('--spinDur', `${spinDur}s`);
      }catch{}
      legend = '';
    } else {
      ringColor = '#10b981'; ringRatio = 0; centerVal='0.0'; centerUnit='steps/mn'; legend='';
    }

    if (g){ g.style.setProperty('--p', String(ringRatio)); g.style.setProperty('--g', ringColor); g.setAttribute('title', `${centerVal} steps/mn (fenêtre ${winSec}s)`); }
    if (gnum){ gnum.textContent = centerVal; }
    if (glab){ glab.textContent = centerUnit; }
    if (gleg){ gleg.textContent = legend; }
    if (needle){
      const angleTarget = -90 + (ringRatio * 180);
      const angle = smoothAngle(wn, angleTarget);
      needle.style.transform = `translate(-50%, -100%) rotate(${angle}deg)`;
      needle.style.backgroundColor = ringColor;
    }

    // Sleep Zzz (animated)
    try{
      const nameLine = card.querySelector('.name-line');
      const sleeping = (p==='running' && ratePerSec===0 && rk!=='tool');
      let z = card.querySelector('.sleep-zz');
      if (sleeping){ if (!z){ z = document.createElement('span'); z.className='sleep-zz'; z.textContent='Zzz'; z.title='Sleeping'; nameLine.appendChild(z); } }
      else { if (z) z.remove(); }
      // Aura
      setAvatarAura(card, { phase:p, running_kind:rk, sleeping });
    }catch{}

  }catch{}
}
