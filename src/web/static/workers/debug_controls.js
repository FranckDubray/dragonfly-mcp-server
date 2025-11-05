

















// Contrôles debug via MCP /execute (actions HTTP)
export const DebugControls = {
  async action(worker, action, params={}){
    const payload = { tool:'py_orchestrator', params: { operation:'debug', worker_name: worker, debug: { action } } };
    if (params && params.timeout_sec != null){ payload.params.debug.timeout_sec = Number(params.timeout_sec); }
    if (params && (params.target_node || params.target_when)){
      payload.params.debug.target = { node: params.target_node || undefined, when: params.target_when || undefined };
    }
    if (params && (params.break_node || params.break_when)){
      payload.params.debug.breakpoint = { node: params.break_node || undefined, when: params.break_when || undefined };
    }
    const r = await fetch('/execute', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    if (!r.ok) throw new Error('debug action failed');
    const js = await r.json();
    return (js && js.result) ? js.result : js;
  },
  // Augmente les timeouts à 90s (au lieu de 10/15)
  step(worker){ return DebugControls.action(worker,'step',{timeout_sec:90}); },
  cont(worker){ return DebugControls.action(worker,'continue',{timeout_sec:90}); },
  runUntil(worker, node, when='always'){ return DebugControls.action(worker,'run_until',{timeout_sec:90, target_node:node, target_when:when}); },
  inspect(worker){ return DebugControls.action(worker,'inspect'); },
  breakAdd(worker, node, when='always'){ return DebugControls.action(worker,'break_add',{break_node:node, break_when:when}); },
  breakRemove(worker, node, when='always'){ return DebugControls.action(worker,'break_remove',{break_node:node, break_when:when}); },
  breakClear(worker){ return DebugControls.action(worker,'break_clear'); },
  breakList(worker){ return DebugControls.action(worker,'break_list'); },
};

 
 
 
 
 
 
 
 
