

// Workers Process UI Core - buildReplaySequence shim (with ts_ms/ts_precise)
(function(){
  function buildAllowedNodeIdSet(){
    try{
      var src = window.MERMAID_CACHE || window.__MERMAID_CACHE__ || '';
      if (!src || !window.WPConsistency || typeof WPConsistency.extractNodeIds !== 'function') return null;
      var ids = WPConsistency.extractNodeIds(src);
      if (!ids || !ids.size) return null;
      // Build a sanitized lookup too (to match history labels)
      var san = new Set();
      ids.forEach(function(id){ try{ san.add((window.RenderUtils?.sanitizeId(id) || String(id)).toLowerCase()); }catch(_){ } });
      return { raw: ids, san: san };
    }catch(_){ return null; }
  }

  window.buildReplaySequence = (async function(rangeKey){
    var hist = await WPData.fetchHistory(rangeKey); // DESC (newest first)
    var allow = buildAllowedNodeIdSet();
    var nodes = [];
    var meta = [];
    for (var i=hist.length-1; i>=0; i--){
      var nRaw = String(hist[i].node||'').trim();
      if (!nRaw) continue;
      // Filter out anything that is not a real node in the diagram
      if (allow){
        var ok = allow.raw.has(nRaw) || allow.san.has((window.RenderUtils?.sanitizeId(nRaw)||nRaw).toLowerCase());
        if (!ok) continue; // skip pseudo-steps (e.g. arrows/transitions)
      }
      if (nodes.length===0 || nodes[nodes.length-1] !== nRaw){
        nodes.push(nRaw);
        meta.push({ id: hist[i].id, node: nRaw, ts: hist[i].ts || '', ts_precise: hist[i].ts_precise || '', ts_ms: Number(hist[i].ts_ms)||0 });
      }
    }
    WP.replayMeta = meta; // aligned with nodes
    return { nodes: nodes, meta: meta };
  });
})();
