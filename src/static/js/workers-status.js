/**
 * Workers Status - stats & derniers événements (5s)
 */

async function refreshWorkerStats(workerId){
  try {
    const tasksRes = await fetch(`/workers/${workerId}/query`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ query: "SELECT COUNT(*) as count FROM job_steps WHERE status IN ('succeeded', 'failed')", limit: 1 }) });
    if (tasksRes.ok){ const data = await tasksRes.json(); const count = data.rows[0]?.count || 0; const el = document.getElementById(`stat-${workerId}-tasks`); if (el) el.textContent = count; }
    const errorsRes = await fetch(`/workers/${workerId}/query`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ query: "SELECT COUNT(*) as count FROM job_steps WHERE status='failed'", limit: 1 }) });
    if (errorsRes.ok){ const data = await errorsRes.json(); const count = data.rows[0]?.count || 0; const el = document.getElementById(`stat-${workerId}-errors`); if (el) el.textContent = count; }
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
      lines = r.rows.map(x=>({ when: formatWhen(x.ts||''), node: String(x.node||''), sev: computeSeverity(String(x.status||''), String(x.node||'')) }));
    } else {
      const f = await postQuery(workerId, `SELECT skey FROM job_state_kv WHERE skey LIKE 'event_%' ORDER BY rowid DESC LIMIT ${Math.max(1, Math.min(limit, 5))}`);
      if (f?.rows?.length){ lines = f.rows.map(x=>({ when: '', node: String(x.skey||''), sev: 'normal' })); }
    }
    if (!lines.length){ el.innerHTML = '—'; return; }
    el.innerHTML = lines.map(item=> `<div class=\"ev-line\"><div class=\"ev-when\">${escapeHtml(item.when)}</div><div class=\"ev-node ${escapeHtml(item.sev)}\">${escapeHtml(item.node)}</div><div class=\"ev-status\"></div></div>`).join('');
  }catch(e){ el.innerHTML = '—'; }
}

function computeSeverity(status, node){
  const s = status.toLowerCase();
  if (s === 'failed') return 'crit';
  if (s === 'running') return 'warn';
  return 'normal';
}

function formatWhen(s){
  if (!s) return '';
  try {
    const d = new Date(s);
    if (isNaN(d.getTime())) return String(s).slice(11,16) || String(s);
    const now = new Date();
    const sameDay = d.getFullYear()===now.getFullYear() && d.getMonth()===now.getMonth() && d.getDate()===now.getDate();
    if (sameDay){
      return d.toLocaleTimeString('fr-FR', {hour:'2-digit', minute:'2-digit'});
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

// polling 5s
setInterval(async () => {
  for (const w of (window.workersData||[])){
    await refreshWorkerStats(w.id);
    await refreshWorkerEvents(w.id, 3);
  }
}, 5000);

// Expose
window.refreshWorkerStats = refreshWorkerStats;
window.refreshWorkerEvents = refreshWorkerEvents;
