
// Workers Process - Consistency checks (logs <-> Mermaid graph)
(function(){
  function extractNodeIds(mermaidSrc){
    var set = new Set();
    try{
      var lines = String(mermaidSrc||'').split(/\n/);
      // Match ANY node id occurring anywhere in the line, not only at start
      // Supports Mermaid node syntaxes: id(text), id[text], id{decision}
      // Regex groups: 1 = boundary, 2 = node id, 3 = opening bracket/brace/paren
      var re = /(^|[^A-Za-z0-9_])([A-Za-z0-9_]+)\s*(\(|\[|\{)/g;
      for (var i=0;i<lines.length;i++){
        var line = lines[i];
        var m;
        while ((m = re.exec(line)) !== null){
          // Avoid empty/invalid ids just in case
          var id = (m[2]||'').trim();
          if (id) set.add(id);
        }
      }
    }catch(_){ }
    return set;
  }

  async function checkConsistency(mermaidSrc, currentNode){
    try{
      var nodeSet = extractNodeIds(mermaidSrc);
      var missingDetails = [];

      // Check current node first
      if (currentNode){
        var cur = String(currentNode).trim();
        if (cur && !nodeSet.has(cur)) missingDetails.push({ id: '-', name: cur, ts: '' });
      }

      // Fetch recent steps with id + when
      var r = await WPData.postQuery(WP.processWorkerId, "SELECT id, name, COALESCE(finished_at, started_at) AS ts FROM job_steps ORDER BY id DESC LIMIT 50");
      if (r?.rows?.length){
        for (var i=0;i<r.rows.length;i++){
          var name = String(r.rows[i].name||'').trim();
          if (!name) continue;
          if (!nodeSet.has(name)){
            missingDetails.push({ id: r.rows[i].id, name: name, ts: String(r.rows[i].ts||'') });
          }
        }
      }

      if (missingDetails.length){
        // Deduplicate by name+id
        var seen = new Set();
        var unique = [];
        for (var j=0;j<missingDetails.length;j++){
          var key = missingDetails[j].name+"#"+missingDetails[j].id;
          if (seen.has(key)) continue;
          seen.add(key); unique.push(missingDetails[j]);
        }
        // Build human message: cap to 5 samples
        var samples = unique.slice(0,5).map(function(x){
          var when = x.ts ? (new Date(x.ts).toLocaleString('fr-FR') || x.ts) : '';
          return (x.id!="-"? ("id="+x.id+" ") : "") + x.name + (when? (" ("+when+")") : "");
        });
        var more = unique.length>5 ? (" … +"+(unique.length-5)+" autres") : '';
        showProcessAlert('Incohérence logs ↔ schéma: '+unique.length+' nœud(s) inconnu(s). Exemples: '+samples.join(', ')+more);
      } else {
        hideProcessAlert();
      }
    }catch(e){ /* noop */ }
  }

  window.WPConsistency = { extractNodeIds, checkConsistency };
})();
