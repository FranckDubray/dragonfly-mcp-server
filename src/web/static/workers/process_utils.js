



















// Utilities for process modal (mini helpers)
export function resolveAsset(url){
  const u = String(url||'').trim();
  if (!u) return '';
  if (/^https?:\/\//i.test(u)) return u;
  if (u.startsWith('/')) return u;
  return `/docs/images/${u}`;
}

export function setAura(el, {phase}){
  try{
    const p = String(phase||'').toLowerCase();
    el.classList.add('aura');
    el.classList.remove('a--running','a--tool','a--sleep','a--stop-ok','a--stop-err');
    if (p === 'failed') el.classList.add('a--stop-err');
    else if (p === 'running' || p === 'starting') el.classList.add('a--running');
    else el.classList.add('a--stop-ok');
  }catch{}
}

export function skeleton(){
  const wrap = document.createElement('div');
  wrap.style.cssText = 'min-height:300px; display:grid; place-items:center;';
  const bar = document.createElement('div');
  bar.style.cssText = 'width:72%; height:12px; background:#eee; border-radius:999px; position:relative; overflow:hidden;';
  const sh = document.createElement('div');
  sh.style.cssText = 'position:absolute; inset:0; transform:translateX(-100%); background:linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,.7) 50%, rgba(255,255,255,0) 100%); animation: shimmer 1.4s infinite;';
  bar.appendChild(sh); wrap.appendChild(bar);
  return wrap;
}

export async function pickInitialKind(worker, api){
  try{
    const st = await api.status(worker);
    const ph = String(st.phase || st.status || '').toLowerCase();
    if (ph === 'running' || ph === 'starting') return 'current_subgraph';
    return 'overview';
  }catch{ return 'overview'; }
}

// Simplified local date-times for humans (no year)
export function formatLocalTs(iso){
  try{
    if (!iso) return '';
    const d = new Date(iso);
    if (!isFinite(d.getTime())) return String(iso);
    const date = d.toLocaleDateString(undefined, { month:'2-digit', day:'2-digit' });
    const time = d.toLocaleTimeString(undefined, { hour:'2-digit', minute:'2-digit', second:'2-digit' });
    return `${date} ${time}`;
  }catch{ return String(iso||''); }
}

// Very short local time only (no year/date)
export function formatLocalTimeShort(iso){
  try{
    if (!iso) return '';
    const d = new Date(iso);
    if (!isFinite(d.getTime())) return String(iso);
    return d.toLocaleTimeString(undefined, { hour:'2-digit', minute:'2-digit', second:'2-digit' });
  }catch{ return String(iso||''); }
}

function isSameDay(a, b){ try{ return a && b && a.getFullYear()===b.getFullYear() && a.getMonth()===b.getMonth() && a.getDate()===b.getDate(); }catch{ return false; } }

// Shared label for run window (now simplified): prefer times; add date only if not same-day as today
export function fmtRunWindow(startIso, endIso, steps, finalStatus){
  try{
    const s = startIso ? new Date(startIso) : null;
    const e = endIso ? new Date(endIso) : null;
    const now = new Date();
    const tOpts = { hour:'2-digit', minute:'2-digit' };
    const dOpts = { month:'2-digit', day:'2-digit' };

    const sameDayAsToday = s && isSameDay(s, now) && e && isSameDay(e, now);
    const dS = s ? s.toLocaleDateString(undefined, dOpts) : '…';
    const tS = s ? s.toLocaleTimeString(undefined, tOpts) : '…';
    const tE = e ? e.toLocaleTimeString(undefined, tOpts) : '…';

    const when = sameDayAsToday ? `${tS}–${tE}` : `${dS} ${tS}–${tE}`;
    const stepsStr = (typeof steps==='number' && steps>=0) ? ` • ${steps}` : '';
    const emoji = statusEmoji(finalStatus);
    return `${emoji} ${when} ${stepsStr}`.trim();
  }catch{ return '• run'; }
}

// New: compact local label with emoji status (no year) — for run selector (no steps)
export function fmtRunShort(startIso, endIso, steps, finalStatus){
  try{
    const s = startIso ? new Date(startIso) : null;
    const e = endIso ? new Date(endIso) : null;
    const now = new Date();
    const tOpts = { hour:'2-digit', minute:'2-digit' };
    const dOpts = { month:'2-digit', day:'2-digit' };

    const sameDayAsToday = s && isSameDay(s, now) && e && isSameDay(e, now);
    const dS = s ? s.toLocaleDateString(undefined, dOpts) : '…';
    const tS = s ? s.toLocaleTimeString(undefined, tOpts) : '…';
    const tE = e ? e.toLocaleTimeString(undefined, tOpts) : '…';

    const when = sameDayAsToday ? `${tS}–${tE}` : `${dS} ${tS}–${tE}`;
    const emoji = statusEmoji(finalStatus);
    return `${emoji} ${when}`.trim();
  }catch{ return '• run'; }
}

export function statusEmoji(st){
  const s = String(st||'').toLowerCase();
  if (s === 'completed' || s === 'success' || s === 'succeeded' || s === 'ok') return '✅';
  if (s === 'failed' || s === 'error') return '❌';
  if (s === 'canceled' || s === 'cancelled') return '🛑';
  if (s === 'running' || s === 'in_progress' || s === 'starting') return '⏳';
  return '•';
}

// ===== Replay speed helpers =====
const K_SPEED = 'workers_ui_replay_speed'; // stores a factor number or 'max'
export function getReplaySpeed(){
  try{
    const raw = sessionStorage.getItem(K_SPEED)||'1';
    if (raw === 'max') return 'max';
    const v = parseFloat(raw);
    return (isFinite(v) && v>0) ? v : 1;
  }catch{ return 1; }
}
export function setReplaySpeed(f){
  try{
    if (String(f) === 'max'){
      sessionStorage.setItem(K_SPEED, 'max');
      return;
    }
    const v = parseFloat(f);
    if (isFinite(v) && v>0) sessionStorage.setItem(K_SPEED, String(v));
  }catch{}
}
export function replayIntervalMs(){
  const f = getReplaySpeed();
  if (f === 'max') return 0; // no sleep: fastest possible
  const factor = Number(f)||1;
  return Math.max(0, Math.round(600 / factor)); // allow 0 for very high speeds
}

 
 
 
 
