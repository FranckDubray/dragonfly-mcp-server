




(function(global){
  function dbg(){ try{ if (global.__WG_DEBUG) console.log('[WG][helpers]', ...arguments); }catch{} }

  function deriveToolName(call){
    try{
      if (!call || typeof call !== 'object') return '';
      const t  = String(call.tool || call.tool_name || call.name || '').trim();
      const op = String(call.operation || '').trim();
      if (t && op) return `${t}:${op}`;
      if (t) return t;
      if (op) return `py_orchestrator:${op}`;
      return '';
    }catch{ return ''; }
  }

  function collectNamesFromAny(obj, out){
    try{
      if (!obj || typeof obj !== 'object') return;
      const add = (name)=>{ if (name) out.add(String(name)); };
      const t  = String(obj.tool || obj.tool_name || obj.name || '').trim();
      const op = String(obj.operation || '').trim();
      if (t || op){ add((t && op) ? `${t}:${op}` : (t || (op ? `py_orchestrator:${op}` : ''))); }
      const call = (obj.call && typeof obj.call==='object') ? obj.call : null;
      if (call){ add(deriveToolName(call)); }
      const tcall = (obj.tool_call && typeof obj.tool_call==='object') ? obj.tool_call : null;
      if (tcall){
        const tn = String(tcall.tool || tcall.tool_name || tcall.name || '').trim();
        const op2= String(tcall.operation || '').trim();
        if (tn || op2) add((tn && op2)? `${tn}:${op2}` : (tn || (op2? `py_orchestrator:${op2}`: '')));
      }
      const nameKey = String(obj.toolName || obj.toolname || '').trim();
      if (nameKey){ add(nameKey); }
    }catch{}
  }

  function escapeRegExp(s){ return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  function containsWordish(hay, needle){
    try{
      if (!hay || !needle) return false;
      const re = new RegExp(`(^|[^A-Za-z0-9_])${escapeRegExp(needle)}([^A-Za-z0-9_]|$)`, 'i');
      return re.test(hay);
    }catch{ return false; }
  }

  global.WGLiveHelpers = { dbg, deriveToolName, collectNamesFromAny, containsWordish };
})(window);

