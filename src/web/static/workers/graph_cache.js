



















import { buildSvgIndex, renderMermaid } from './svg_map.js';

export class GraphCache {
  constructor(worker, maxEntries=40){ this.worker = worker; this.cache = new Map(); this.order=[]; this.max=maxEntries; }
  key(kind, opts){
    const sg = opts?.subgraph || '';
    const hs = opts?.hide_start ? '1':'0';
    const he = opts?.hide_end ? '1':'0';
    const lb = (opts?.labels===false)?'0':'1';
    return `${kind}:${sg}:${hs}${he}${lb}`;
  }
  _touch(k){ if (!this.cache.has(k)) return; const i=this.order.indexOf(k); if(i>=0){ this.order.splice(i,1); this.order.push(k);} }
  _set(k, val){ this.cache.set(k,val); const i=this.order.indexOf(k); if(i>=0) this.order.splice(i,1); this.order.push(k); while(this.order.length>this.max){ const old=this.order.shift(); if(old) this.cache.delete(old); } }
  clear(){ this.cache.clear(); this.order.length=0; }
  async ensureRender(kind, opts){
    const k = this.key(kind, opts);
    if (this.cache.has(k)){ this._touch(k); if (window.__GV_DEBUG){ try{ console.debug('[GC] hit', {key:k}); }catch{} } return this.cache.get(k); }
    // Fetch mermaid via MCP /execute tool py_orchestrator (operation=graph)
    const include = { shapes: true, emojis: true, labels: (opts && 'labels' in opts) ? !!opts.labels : true };
    const render = { mermaid: true, hide_start: !!opts?.hide_start, hide_end: !!opts?.hide_end };
    if (kind === 'overview'){
      // overview is a render mode over the whole process
      render.overview_subgraphs = true;
    }
    const graphReq = { kind: (kind==='overview'?'process':kind), include, render };
    if ((kind==='subgraph' || opts?.subgraph) && opts?.subgraph){ graphReq.subgraphs = [opts.subgraph]; }
    const payload = {
      tool: 'py_orchestrator',
      params: { operation: 'graph', worker_name: this.worker, graph: graphReq }
    };
    if (window.__GV_DEBUG){ try{ console.debug('[GC] fetch', {kind, subgraph: opts?.subgraph||'', payload}); }catch{} }
    const r = await fetch('/execute', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    const js = await r.json();
    const mm = (js && (js.mermaid || (js.result && js.result.mermaid))) || '';
    if (window.__GV_DEBUG){ try{ console.debug('[GC] response', { ok:r.ok, mermaidChars: (mm? mm.length : 0), status: js?.status, message: js?.message || js?.result?.message }); }catch{} }
    if (!mm){
      const msg = String((js && (js.message || (js.result && js.result.message))) || js.status || 'Graph indisponible');
      throw new Error(msg);
    }
    const svg = await renderMermaid(mm);
    const index = buildSvgIndex(svg);
    const out = {svg, index};
    this._set(k, out);
    return out;
  }
}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 

