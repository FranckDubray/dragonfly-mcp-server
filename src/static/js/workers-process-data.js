



// Workers Process - Data access helpers
(function(){
  async function postQuery(workerId, query, limit){
    try{
      var body = { query: query };
      if (typeof limit === 'number') body.limit = Math.max(1, Math.min(limit, 200));
      var res = await fetch('/workers/'+workerId+'/query', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
      if (!res.ok){ return {}; }
      return await res.json();
    }catch(_){ return {}; }
  }

  async function fetchMermaid(){
    var q1 = "SELECT svalue AS mermaid FROM job_state_kv WHERE skey='graph_mermaid' ORDER BY rowid DESC LIMIT 1";
    var g1 = await postQuery(WP.processWorkerId, q1, 1);
    if (g1?.rows?.length && g1.rows[0].mermaid) return g1.rows[0].mermaid;
    var q2 = "SELECT svalue AS mermaid FROM job_meta WHERE skey='graph_mermaid' LIMIT 1";
    var g2 = await postQuery(WP.processWorkerId, q2, 1);
    if (g2?.rows?.length && g2.rows[0].mermaid) return g2.rows[0].mermaid;
    return '';
  }

  async function fetchCurrentState(){
    var node = '';
    var args = '';
    try {
      var n = await postQuery(WP.processWorkerId, "SELECT svalue AS cur FROM job_state_kv WHERE skey IN ('current_node','current_step','current_stage') ORDER BY rowid DESC LIMIT 1", 1);
      if (n?.rows?.length) node = String(n.rows[0].cur||'').trim();
    } catch(_){ }
    try {
      var a = await postQuery(WP.processWorkerId, "SELECT svalue AS a FROM job_state_kv WHERE skey IN ('current_args','current_params','current_payload') ORDER BY rowid DESC LIMIT 1", 1);
      if (a?.rows?.length) args = String(a.rows[0].a||'');
    } catch(_){ }
    return { node: node, args: args };
  }

  async function fetchHistory(rangeKey){
    // Load as much as permitted by backend cap (200 rows)
    var cap = 200;
    var q = "SELECT id, name AS node, status, COALESCE(finished_at, started_at) AS ts FROM job_steps ORDER BY id DESC LIMIT "+cap;
    var r = await postQuery(WP.processWorkerId, q, cap);
    if (r?.rows?.length) return r.rows.map(function(x){ return { id: x.id, node: x.node||'', status: x.status||'', ts: x.ts||'' }; });
    var f = await postQuery(WP.processWorkerId, "SELECT rowid AS id, skey AS node FROM job_state_kv WHERE skey LIKE 'event_%' ORDER BY rowid DESC LIMIT "+cap, cap);
    if (f?.rows?.length) return f.rows.map(function(x){ return { id: x.id, node: x.node||'', status: '', ts: '' }; });
    return [];
  }

  async function fetchStatsLastHour(){
    // Tasks performed (succeeded/failed) in 1h
    var qTasks = "SELECT COUNT(*) AS c FROM job_steps WHERE status IN ('succeeded','failed') AND (strftime('%s','now') - strftime('%s', COALESCE(finished_at, started_at))) <= 3600";
    var rTasks = await postQuery(WP.processWorkerId, qTasks, 1);
    var tasks = (rTasks?.rows?.[0]?.c) || 0;

    // call_llm calls in 1h (match both 'call_llm%' and 'call llm%')
    var qLLM = "SELECT COUNT(*) AS c FROM job_steps WHERE ((name LIKE 'call_llm%' ESCAPE '\\') OR (name LIKE 'call llm%')) AND (strftime('%s','now') - strftime('%s', COALESCE(finished_at, started_at))) <= 3600";
    var rLLM = await postQuery(WP.processWorkerId, qLLM, 1);
    var llm = (rLLM?.rows?.[0]?.c) || 0;

    // cycles in 1h - heuristic: count sleep_interval occurrences
    var qCycles = "SELECT COUNT(*) AS c FROM job_steps WHERE name='sleep_interval' AND (strftime('%s','now') - strftime('%s', COALESCE(finished_at, started_at))) <= 3600";
    var rCycles = await postQuery(WP.processWorkerId, qCycles, 1);
    var cycles = (rCycles?.rows?.[0]?.c) || 0;

    // fallback: if no sleep_interval, try finish_mailbox_db
    if (!cycles){
      var qAlt = "SELECT COUNT(*) AS c FROM job_steps WHERE name='finish_mailbox_db' AND (strftime('%s','now') - strftime('%s', COALESCE(finished_at, started_at))) <= 3600";
      var rAlt = await postQuery(WP.processWorkerId, qAlt, 1);
      cycles = (rAlt?.rows?.[0]?.c) || 0;
    }

    return { tasks: Number(tasks)||0, llm_calls: Number(llm)||0, cycles: Number(cycles)||0 };
  }

  // UI helper: load details for one step and render inside #stepDetails
  async function loadAndShowStepDetails(workerId, stepId){
    try{
      var idNum = parseInt(stepId, 10);
      if (!isFinite(idNum) || idNum <= 0) idNum = 0;
      var q = "SELECT * FROM job_steps WHERE id="+idNum+" LIMIT 1";
      var r = await postQuery(workerId, q, 1);
      var panel = document.getElementById('stepDetails');
      if (!panel) return;
      var box = panel.querySelector('.code');
      if (!box){ panel.innerHTML = '<div class="panel-title">Détails</div><div class="code"></div>'; box = panel.querySelector('.code'); }
      if (r?.rows?.length){
        var obj = r.rows[0];
        var pretty = JSON.stringify(obj, null, 2);
        box.textContent = pretty;
      } else {
        box.textContent = 'Aucun détail disponible pour l\'identifiant '+ idNum;
      }
    }catch(e){
      try{
        var panel = document.getElementById('stepDetails');
        if (panel){ var box = panel.querySelector('.code'); if (box) box.textContent = 'Erreur chargement détails: '+ (e.message||e); }
      }catch(_){ }
    }
  }

  window.WPData = { postQuery, fetchMermaid, fetchCurrentState, fetchHistory, fetchStatsLastHour };
  // Expose global for overlay click handler
  window.loadAndShowStepDetails = loadAndShowStepDetails;
})();

 
 
 
 
 