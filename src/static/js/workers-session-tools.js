/**
 * Workers Session - Tools bridge
 */

function handleFunctionCall(data){
  const callId = data.call_id; const name = data.name; let args = {};
  try{ args = data.arguments? JSON.parse(data.arguments):{} }catch(_){ args = {}; }
  const preview = `${name} ${safeArgsPreview(args)}`; miniAppend('tool', preview); inlineAppend('tool', preview);
  executeTool(name, args, callId);
}

async function executeTool(name, args, callId){
  try{
    const workerId = currentWorkerConfig?.worker_id; if (!workerId) throw new Error('Worker config missing');
    const res = await fetch(`/workers/${workerId}/tool/query`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(args) });
    if (!res.ok){ const txt = await res.text(); throw new Error(`HTTP ${res.status}: ${txt}`); }
    const data = await res.json();
    const output = data.summary || (Array.isArray(data.rows)? formatSQLResultForTTS(data): JSON.stringify(data));
    ws.send(JSON.stringify({ type:'conversation.item.create', item:{ type:'function_call_output', call_id: callId, output: String(output||'') } }));
    sendResponseCreateSafe('tool-output');
  }catch(e){
    ws?.send(JSON.stringify({ type:'conversation.item.create', item:{ type:'function_call_output', call_id: callId, output: `Erreur: ${e.message}` } }));
    sendResponseCreateSafe('tool-error');
  }
}

function formatSQLResultForTTS(result){
  const rows = result.rows||[]; const count = rows.length;
  if (count===0) return 'Aucun résultat.';
  if (count===1){ const cols = Object.keys(rows[0]); if (cols.length===1) return `Résultat : ${rows[0][cols[0]]}`; return 'Résultat : ' + Object.entries(rows[0]).map(([k,v])=>`${k} ${v}`).join(', '); }
  if (count<=3) return `${count} résultats. ` + rows.map((row,i)=> `Ligne ${i+1} : ` + Object.entries(row).map(([k,v])=>`${k} ${v}`).join(', ')).join('. ');
  return `${count} résultats trouvés. Premiers : ` + rows.slice(0,2).map(row=>Object.values(row).join(', ')).join(' | ');
}

// Expose
window.handleFunctionCall = handleFunctionCall;
window.executeTool = executeTool;
