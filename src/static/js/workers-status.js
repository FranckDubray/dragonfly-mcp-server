










/**
 * Workers Status - stats & derniers événements (5s) + runtime status (running/idle)
 */

function robustParseLocal(ts){
  try{
    if (!ts) return null;
    const raw = String(ts).trim();
    // If raw already ISO with timezone (Z or ±HH:MM)
    if (/Z|[+\-]\d{2}:?\d{2}$/.test(raw)){
      const dIso = new Date(raw);
      if (!isNaN(dIso)) return dIso;
    }
    // Try native parse (kept as very last resort below)
    // Parse common SQLite naive formats as UTC (then display local)
    const m = raw.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?$/);
    if (m){
      const y  = parseInt(m[1],10), mo = parseInt(m[2],10)-1, da = parseInt(m[3],10);
      const hh = parseInt(m[4],10), mi = parseInt(m[5],10), ss = parseInt(m[6],10);
      let ms = 0; if (m[7]){ const frac = (m[7]+'000').slice(0,3); ms = parseInt(frac,10)||0; }
      // IMPORTANT: treat naive as UTC
      const dUtc = new Date(Date.UTC(y, mo, da, hh, mi, ss, ms));
      if (!isNaN(dUtc)) return dUtc;
    }
    // Fallback: try native parse
    let d = new Date(raw);
    if (!isNaN(d)) return d;
  }catch(_){ }
  return null;
}

async function refreshWorkerStats(workerId){
  try {
    // Tâches totales (succeeded + failed)
    const tasksRes = await fetch(`/workers/${workerId}/query`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ query: "SELECT COUNT(*) as count FROM job_steps WHERE status IN ('succeeded', 'failed')", limit: 1 }) });
    if (tasksRes.ok){ const data = await tasksRes.json(); const count = data.rows[0]?.count || 0; const el = document.getElementById(`stat-${workerId}-tasks`); if (el) el.textContent = count; }

    // Erreurs (failed)
    const errorsRes = await fetch(`/workers/${workerId}/query`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ query: "SELECT COUNT(*) as count FROM job_steps WHERE status='failed'", limit: 1 }) });
    if (errorsRes.ok){ const data = await errorsRes.json(); const count = data.rows[0]?.count || 0; const el = document.getElementById(`stat-${workerId}-errors`); if (el) el.textContent = count; }

    // Activité (nb de lignes job_steps dernière heure)
    const actRes = await fetch(`/workers/${workerId}/query`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ query: "SELECT COUNT(*) AS c FROM job_steps WHERE (strftime('%s','now') - strftime('%s', COALESCE(finished_at, started_at))) <= 3600", limit: 1 }) });
    if (actRes.ok){
      const data = await actRes.json();
      const c = data.rows[0]?.c || 0;
      const card = document.getElementById(`card-${workerId}`);
      if (card){
        card.classList.remove('activity-green','activity-orange','activity-red');
        if (c <= 20) card.classList.add('activity-green');
        else if (c <= 50) card.classList.add('activity-orange');
        else card.classList.add('activity-red');
      }
    }
  } catch (_) {
    const elTasks = document.getElementById(`stat-${workerId}-tasks`);
    const elErrors = document.getElementById(`stat-${workerId}-errors`);
    if (elTasks) elTasks.textContent = '—';
    if (elErrors) elErrors.textContent = '—';
  }
}

async function refreshWorkerEvents(workerId, limit=3){
  const el = document.getElementById(`eventsList-${workerId}`); if (!el) return;
  try{
    const q = `SELECT name AS node, status, COALESCE(finished_at, started_at) AS ts FROM job_steps ORDER BY id DESC LIMIT ${Math.max(1, Math.min(limit, 5))}`;
    const r = await postQuery(workerId, q);
    let lines = [];
    if (r?.rows?.length){
      lines = r.rows.map(x=>{
        const d = robustParseLocal(x.ts||'');
        const lang = (typeof navigator !== 'undefined' && navigator.language) ? navigator.language : 'fr-FR';
        const localStr = d? d.toLocaleTimeString(lang,{hour:'2-digit',minute:'2-digit'}) : (String(x.ts||'').slice(11,16)||String(x.ts||''));
        return { when: localStr, node: String(x.node||''), sev: computeSeverity(String(x.status||''), String(x.node||'')) };
      });
    } else {
      const f = await postQuery(workerId, `SELECT skey FROM job_state_kv WHERE skey LIKE 'event_%' ORDER BY rowid DESC LIMIT ${Math.max(1, Math.min(limit, 5))}`);
      if (f?.rows?.length){ lines = f.rows.map(x=>({ when: '', node: String(x.skey||''), sev: 'normal' })); }
    }
    if (!lines.length){ el.innerHTML = '—'; return; }
    el.innerHTML = lines.map(item=> `<div class="ev-line"><div class="ev-when">${escapeHtml(item.when)}</div><div class="ev-node ${escapeHtml(item.sev)}">${escapeHtml(item.node)}</div><div class="ev-status"></div></div>`).join('');
  }catch(e){ el.innerHTML = '—'; }
}

function computeSeverity(status, node){
  const s = status.toLowerCase();
  if (s === 'failed') return 'crit';
  if (s === 'running') return 'warn';
  return 'normal';
}

function formatWhen(s){
  // Deprecated by robustParseLocal in refreshWorkerEvents, keep for fallback
  if (!s) return '';
  try {
    const d = robustParseLocal(s);
    if (!d) return String(s).slice(11,16) || String(s);
    const now = new Date();
    const sameDay = d.getFullYear()===now.getFullYear() && d.getMonth()===now.getMonth() && d.getDate()===now.getDate();
    const lang = (typeof navigator !== 'undefined' && navigator.language) ? navigator.language : 'fr-FR';
    if (sameDay){
      return d.toLocaleTimeString(lang, {hour:'2-digit', minute:'2-digit'});
    } else {
      const dd = String(d.getDate()).padStart(2,'0');
      const mm = String(d.getMonth()+1).padStart(2,'0');
      return `${dd}/${mm}`;
    }
  } catch(_){ }
  return String(s).slice(11,16) || String(s);
}

async function postQuery(workerId, query){
  try{
    const res = await fetch(`/workers/${workerId}/query`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ query, limit: 3 }) });
    if (!res.ok){ return {}; }
    return await res.json();
  }catch(_){ return {}; }
}

// ===== Runtime Status (running/idle + échecs récents) =====
async function refreshWorkerRuntimeStatus(workerId){
  try{
    const q = "SELECT strftime('%s','now') AS now, MAX(strftime('%s', COALESCE(finished_at, started_at))) AS tmax FROM job_steps";
    const r = await postQuery(workerId, q);
    if (!r?.rows?.length) return;
    const now = Number(r.rows[0]?.now||0);
    const tmax = Number(r.rows[0]?.tmax||0);
    const age = (now && tmax) ? (now - tmax) : 0;
    const status = (tmax && age <= 300) ? 'running' : 'idle';

    const errRes = await postQuery(workerId, "SELECT COUNT(*) AS c FROM job_steps WHERE status='failed' AND strftime('%s', COALESCE(finished_at, started_at)) >= strftime('%s','now') - 900");
    const recentFailed = Number(errRes?.rows?.[0]?.c||0);

    const badge = document.getElementById(`runtime-${workerId}`);
    if (badge){
      badge.textContent = status === 'running' ? `En cours · échecs(15min): ${recentFailed}` : `Au repos · échecs(15min): ${recentFailed}`;
      badge.classList.toggle('chip', true);
    }
  }catch(_){ }
}

// polling 5s
setInterval(async () => {
  for (const w of (window.workersData||[])){
    await refreshWorkerStats(w.id);
    await refreshWorkerEvents(w.id, 3);
    await refreshWorkerRuntimeStatus(w.id);
  }
}, 5000);

// Expose
window.refreshWorkerStats = refreshWorkerStats;
window.refreshWorkerEvents = refreshWorkerEvents;
window.refreshWorkerRuntimeStatus = refreshWorkerRuntimeStatus;

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
