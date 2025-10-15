/**
 * Workers Process (Mermaid overlay) + Replay 1x + Auto-refresh 10s + Step details
 * Version sans template literals complexes pour éviter erreurs de parse
 */

var _mermaidReady = false;
var _replayTimer = null;
var _replayActive = false;
var _replayIx = 0;
var _replaySeq = [];
var _processWorkerId = '';
var _processRefreshTimer = null;

function ensureMermaid(){
  return new Promise(function(resolve){
    if (_mermaidReady && window.mermaid) return resolve();
    var existing = document.querySelector('script[data-mermaid]');
    if (existing && window.mermaid){ _mermaidReady = true; return resolve(); }
    var s = document.createElement('script');
    s.src = 'https://unpkg.com/mermaid@10/dist/mermaid.min.js';
    s.async = true; s.defer = true; s.setAttribute('data-mermaid','1');
    s.onload = function(){ try{ window.mermaid.initialize({ startOnLoad:false, theme:'neutral', securityLevel:'loose' }); _mermaidReady = true; }catch(_){} resolve(); };
    document.head.appendChild(s);
  });
}

function ensureProcessOverlay(){
  var el = document.getElementById('processOverlay');
  if (el) return el;
  el = document.createElement('div');
  el.id = 'processOverlay'; el.className = 'process-overlay';
  el.innerHTML = ''+
    '<div class="process-content" role="dialog" aria-modal="true" aria-label="Processus">'+
    '  <div class="process-header">'+
    '    <div class="title">Processus</div>'+
    '    <div class="tools">'+
    '      <select id="replayRange" aria-label="Période">'+
    '        <option value="15min">15 min</option>'+
    '        <option value="1h">1 h</option>'+
    '        <option value="4h">4 h</option>'+
    '      </select>'+
    '      <button class="btn btn-ghost" id="btnReplay" aria-label="Replay">▶︎</button>'+
    '      <button class="btn btn-ghost" id="btnCloseProcess" aria-label="Fermer">×</button>'+
    '    </div>'+
    '  </div>'+
    '  <div class="process-body">'+
    '    <div class="process-graph" id="processGraph"></div>'+
    '    <div class="process-side" id="processSide"></div>'+
    '  </div>'+
    '</div>';
  document.body.appendChild(el);
  el.addEventListener('click', function(e){ if (e.target === el) closeProcess(); });
  document.addEventListener('keydown', function(e){ if (e.key==='Escape') closeProcess(); });
  el.querySelector('#btnCloseProcess').addEventListener('click', closeProcess);
  el.querySelector('#btnReplay').addEventListener('click', toggleReplay);
  el.addEventListener('click', async function(e){
    var it = e.target.closest('.tl-item');
    if (!it) return;
    var stepId = it.getAttribute('data-id');
    if (stepId) await loadAndShowStepDetails(_processWorkerId, stepId);
  });
  return el;
}

async function openProcess(workerId){
  _processWorkerId = String(workerId||'');
  var overlay = ensureProcessOverlay(); overlay.classList.add('open');
  await ensureMermaid();
  await refreshProcessView();
  clearInterval(_processRefreshTimer);
  _processRefreshTimer = setInterval(async function(){ var open = document.getElementById('processOverlay')?.classList.contains('open'); if (!open){ clearInterval(_processRefreshTimer); return; } await refreshProcessView(); }, 10000);
}

async function refreshProcessView(){
  var graphEl = document.getElementById('processGraph');
  var sideEl = document.getElementById('processSide');
  var rangeSelect = document.getElementById('replayRange');
  if (!graphEl || !sideEl || !rangeSelect) return;
  try {
    var mermaid = await fetchMermaid();
    var current = await fetchCurrentState();
    if (mermaid){
      await renderMermaid(mermaid, graphEl, current.node);
    } else { graphEl.innerHTML = '<p style="padding:10px;">Graph non disponible</p>'; }
    await updateProcessSide(rangeSelect.value, current.args);
    _replaySeq = await buildReplaySequence(rangeSelect.value);
    _replayIx = 0;
  } catch (e) {
    console.error('[Mermaid] render error:', e);
    graphEl.innerHTML = '<p style="padding:10px;color:var(--danger);">Erreur Mermaid: '+escapeHtml(e.message||e)+'</p>';
  }
}

function closeProcess(){ clearInterval(_processRefreshTimer); _processRefreshTimer=null; clearReplayTimer(); var el = document.getElementById('processOverlay'); if (el) el.classList.remove('open'); }

async function fetchMermaid(){
  var q1 = "SELECT svalue AS mermaid FROM job_state_kv WHERE skey='graph_mermaid' ORDER BY rowid DESC LIMIT 1";
  var g1 = await postQuery(_processWorkerId, q1);
  if (g1?.rows?.length && g1.rows[0].mermaid) return g1.rows[0].mermaid;
  var q2 = "SELECT svalue AS mermaid FROM job_meta WHERE skey='graph_mermaid' LIMIT 1";
  var g2 = await postQuery(_processWorkerId, q2);
  if (g2?.rows?.length && g2.rows[0].mermaid) return g2.rows[0].mermaid;
  return '';
}

async function fetchCurrentState(){
  var node = '';
  var args = '';
  try {
    var n = await postQuery(_processWorkerId, "SELECT svalue AS cur FROM job_state_kv WHERE skey IN ('current_node','current_step','current_stage') ORDER BY rowid DESC LIMIT 1");
    if (n?.rows?.length) node = String(n.rows[0].cur||'').trim();
  } catch(_){ }
  try {
    var a = await postQuery(_processWorkerId, "SELECT svalue AS a FROM job_state_kv WHERE skey IN ('current_args','current_params','current_payload') ORDER BY rowid DESC LIMIT 1");
    if (a?.rows?.length) args = String(a.rows[0].a||'');
  } catch(_){ }
  return { node: node, args: args };
}

async function fetchHistory(rangeKey){
  var limit = 20; if (rangeKey==='1h') limit=60; if (rangeKey==='4h') limit=150;
  var q = "SELECT id, name AS node, status, COALESCE(finished_at, started_at) AS ts FROM job_steps ORDER BY id DESC LIMIT "+limit;
  var r = await postQuery(_processWorkerId, q);
  if (r?.rows?.length) return r.rows.map(function(x){ return { id: x.id, node: x.node||'', status: x.status||'', ts: x.ts||'' }; });
  var f = await postQuery(_processWorkerId, "SELECT rowid AS id, skey AS node FROM job_state_kv WHERE skey LIKE 'event_%' ORDER BY rowid DESC LIMIT "+limit);
  if (f?.rows?.length) return f.rows.map(function(x){ return { id: x.id, node: x.node||'', status: '', ts: '' }; });
  return [];
}

async function updateProcessSide(rangeKey, currentArgs){
  var sideEl = document.getElementById('processSide');
  var argsHtml = currentArgs ? '<div class="panel"><div class="panel-title">Arguments</div><pre class="code">'+escapeHtml(currentArgs||'')+'</pre></div>' : '';
  var history = await fetchHistory(rangeKey);
  var histItems = (history||[]).map(function(h){
    var ts = escapeHtml((h.ts||'').slice(11,16));
    var node = escapeHtml(h.node||'');
    var status = escapeHtml(h.status||'');
    return '<div class="tl-item" data-id="'+h.id+'"><div class="tl-when">'+ts+'</div><div class="tl-node">'+node+'</div><div class="tl-status '+status+'">'+status+'</div></div>';
  }).join('');
  var histHtml = '<div class="panel"><div class="panel-title">Historique ('+rangeKey+')</div><div class="timeline">'+(histItems||'<div class="empty">Aucun événement</div>')+'</div></div>';
  sideEl.innerHTML = argsHtml + histHtml + '<div class="panel" id="stepDetails"><div class="panel-title">Détails</div><div class="code">Cliquez un événement pour voir les détails</div></div>';
}

async function buildReplaySequence(rangeKey){
  var hist = await fetchHistory(rangeKey);
  var nodes = [];
  for (var i=hist.length-1; i>=0; i--){ var n = String(hist[i].node||'').trim(); if (n && nodes[nodes.length-1]!==n) nodes.push(n); }
  return nodes;
}

async function loadAndShowStepDetails(workerId, stepId){
  var det = document.getElementById('stepDetails'); if (!det) return;
  try{
    var q = 'SELECT id, name, status, started_at, finished_at, duration_ms, details_json FROM job_steps WHERE id='+Number(stepId)+' LIMIT 1';
    var r = await postQuery(workerId, q);
    if (!r?.rows?.length){ det.innerHTML = '<div class="panel-title">Détails</div><div class="code">Introuvable</div>'; return; }
    var row = r.rows[0];
    var details = {};
    try{ details = row.details_json ? JSON.parse(row.details_json) : {}; }catch(_){ details = { raw: String(row.details_json||'') }; }
    var meta = [
      ['Étape', row.name||''],
      ['Statut', row.status||''],
      ['Début', row.started_at||''],
      ['Fin', row.finished_at||''],
      ['Durée (ms)', String(row.duration_ms||'')]
    ].map(function(kv){ return '<div><strong>'+escapeHtml(kv[0])+':</strong> '+escapeHtml(kv[1])+'</div>'; }).join('');

    var calls = Array.isArray(details.tool_calls)? details.tool_calls: [];
    var outs = Array.isArray(details.tool_outputs)? details.tool_outputs: [];
    var callsHtml = calls.length? '<div class="panel-title" style="margin-top:8px;">Tool calls</div>'+calls.map(function(c){ return '<div class="code">'+escapeHtml(JSON.stringify(c))+'</div>'; }).join(''): '';
    var outsHtml = outs.length? '<div class="panel-title" style="margin-top:8px;">Tool outputs</div>'+outs.map(function(o){ return '<div class="code">'+escapeHtml(JSON.stringify(o))+'</div>'; }).join(''): '';

    var other = Object.assign({}, details); delete other.tool_calls; delete other.tool_outputs;
    var otherHtml = Object.keys(other).length? '<div class="panel-title" style="margin-top:8px;">Payload</div><div class="code">'+escapeHtml(JSON.stringify(other, null, 2))+'</div>': '';

    det.innerHTML = '<div class="panel-title">Détails</div><div class="code">'+meta+'</div>'+callsHtml+outsHtml+otherHtml;
  }catch(e){ det.innerHTML = '<div class="panel-title">Détails</div><div class="code">Erreur: '+escapeHtml(e.message)+'</div>'; }
}

function clearReplayTimer(){ if (_replayTimer){ clearInterval(_replayTimer); _replayTimer = null; } }

async function toggleReplay(){
  var btn = document.getElementById('btnReplay');
  if (!_replaySeq || _replaySeq.length===0){ btn.textContent = '▶︎'; return; }
  _replayActive = !_replayActive;
  btn.textContent = _replayActive ? '⏸' : '▶︎';
  clearReplayTimer();
  if (_replayActive){ _replayIx = 0; _replayTimer = setInterval(stepReplay, 1200); }
}

async function stepReplay(){
  try{
    var graphEl = document.getElementById('processGraph'); if (!graphEl) return;
    var mermaid = await fetchMermaid(); if (!mermaid) return;
    var current = await fetchCurrentState();
    await renderMermaid(mermaid, graphEl, _replaySeq[_replayIx]||current.node||'');
    _replayIx++;
    if (_replayIx >= _replaySeq.length) { clearReplayTimer(); var btn = document.getElementById('btnReplay'); if (btn){ btn.textContent = '▶︎'; } _replayActive = false; }
  }catch(_){ clearReplayTimer(); }
}

async function postQuery(workerId, query){
  try{
    var res = await fetch('/workers/'+workerId+'/query', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ query: query, limit: 3 }) });
    if (!res.ok){ return {}; }
    return await res.json();
  }catch(_){ return {}; }
}

function escapeHtml(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

window.openProcess = openProcess;
window.closeProcess = closeProcess;
window.toggleReplay = toggleReplay;
