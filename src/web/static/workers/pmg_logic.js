





























































// Process Modal Graph — main logic (observe/replay glue)
import { Highlighter } from './highlight.js';
import { startSSE, startPoll } from './process_stream.js';
import { ensureJsonFormatter, renderJson } from './json_viewer.js';
import { findNodeG, splitNode, isSymbolic } from './pmg_find.js';
import { loadGraph as doLoadGraph, wireSvgClicks } from './pmg_render.js';

export function createGraphLogic(worker, dom, onStatusKind){
  const hl = new Highlighter();
  const _notFoundWarned = new Set();
  let lastEventAt = 0;
  let sleepTimer = 0;
  let stopObserveFn = null;

  const state = {
    currentKind: 'process',
    currentSubgraph: '',
    lastNonSubKind: 'process',
    followSubgraph: true, // ALWAYS follow (no toggle)
  };

  function armSleep(){
    try{ if (sleepTimer) clearTimeout(sleepTimer); sleepTimer = setTimeout(()=>{ if (Date.now()-lastEventAt>2200) onStatusKind('sleep'); }, 2200); }catch{}
  }

  // Safe DOM helpers fallback if caller passed only dom.stage etc.
  const _dom = {
    setCurrent: typeof dom.setCurrent === 'function' ? dom.setCurrent : (node)=>{},
    setStepTs: typeof dom.setStepTs === 'function' ? dom.setStepTs : (iso)=>{},
    inBox: dom.inBox || null,
    outBox: dom.outBox || null,
    errTitle: dom.errTitle || { style:{ display:'none' } },
    errBox: dom.errBox || { style:{ display:'none' }, textContent:'' },
    stage: dom.stage,
    status: dom.status || null,
  };

  async function ensureAndHighlight(node){
    const DBG = !!window.__GV_DEBUG;
    try{
      if (isSymbolic(node)) return true; // skip view changes

      const tryFind = () => {
        const svg = _dom.stage.querySelector('svg');
        return findNodeG(svg, node);
      };
      let g = tryFind(); if (DBG) console.info('[PM ensure] try current', !!g);
      if (g){ hl.highlight(node); return true; }

      const { sg } = splitNode(node);

      if (sg && (state.currentKind!=='subgraph' || state.currentSubgraph!==sg)){
        if (DBG) console.info('[PM ensure] follow: switch subgraph', sg);
        await loadGraph('subgraph', sg);
        g = tryFind(); if (DBG) console.info('[PM ensure] found after subgraph', !!g);
        if (g){ hl.highlight(node); return true; }
      }
      if (!sg && state.currentKind !== 'process'){
        if (DBG) console.info('[PM ensure] follow: fallback process');
        await loadGraph('process');
        g = tryFind(); if (DBG) console.info('[PM ensure] found after process', !!g);
        if (g){ hl.highlight(node); return true; }
      }

      const k = `${state.currentKind}|${node}`;
      if (!_notFoundWarned.has(k)){
        _notFoundWarned.add(k);
        console.warn('[PROCESS MODAL] node not found after fallbacks:', node);
      }
      return false;
    }catch(e){ console.warn('[PROCESS MODAL] ensureAndHighlight error', e); return false; }
  }

  async function loadGraph(kind='process', subgraph=''){
    if (kind !== 'subgraph') state.lastNonSubKind = kind;

    state.currentKind = kind;
    if (kind === 'subgraph') state.currentSubgraph = String(subgraph||state.currentSubgraph||'').trim();

    const svg = await doLoadGraph({ worker, dom: { ..._dom, stage: _dom.stage }, hl, state, onStatusKind: (k)=>{
      if (k === 'back'){
        loadGraph(state.lastNonSubKind);
      }
    }});

    if (svg){
      wireSvgClicks(svg, state, (sg)=>{ loadGraph('subgraph', sg); });
    }
  }

  async function startObserve(){
    try{
      await startSSE(worker, {
        onConnected: ()=>{},
        onEvent: async (ev)=>{
          lastEventAt = Date.now();
          const node = ev && ev.node_executed || '';
          const call = ev?.io?.in || {};
          const isTool = !!(call.tool || call.tool_name || call.operation);
          onStatusKind(isTool ? 'tool' : 'running');
          armSleep();
          if (!node || isSymbolic(node)) return;
          _dom.setCurrent(node); _dom.setStepTs(ev.finished_at || ev.started_at || '');
          await ensureJsonFormatter();
          renderJson(_dom.inBox, call, '');
          renderJson(_dom.outBox, ev?.io?.out_preview||'', String(ev?.io?.out_preview||''));
          await ensureAndHighlight(node);
          const errm = (ev?.error?.message||'').trim();
          if (errm){ onStatusKind('failed'); _dom.errTitle.style.display=''; _dom.errBox.style.display='block'; _dom.errBox.textContent = errm; }
          else { _dom.errTitle.style.display='none'; _dom.errBox.style.display='none'; _dom.errBox.textContent=''; }
        },
        onTerminal: async ()=>{ onStatusKind('idle'); }
      });
      return;
    }catch(e){ /* SSE failed → poll */ }

    try{ stopObserveFn && stopObserveFn(); }catch{}
    stopObserveFn = startPoll(worker, {
      onEvent: async (evt)=>{
        lastEventAt = Date.now();
        const node = evt && evt.node_executed || '';
        const call = evt?.io?.in || {};
        const isTool = !!(call.tool || call.tool_name || call.operation);
        onStatusKind(isTool ? 'tool' : 'running');
        armSleep();
        if (!node || isSymbolic(node)) return;
        _dom.setCurrent(node); _dom.setStepTs(evt.finished_at || evt.started_at || '');
        await ensureJsonFormatter();
        renderJson(_dom.inBox, call, '');
        renderJson(_dom.outBox, evt?.io?.out_preview||'', String(evt?.io?.out_preview||''));
        await ensureAndHighlight(node);
        const errm = (evt?.error?.message||'').trim();
        if (errm){ onStatusKind('failed'); _dom.errTitle.style.display=''; _dom.errBox.style.display='block'; _dom.errBox.textContent = errm; }
        else { _dom.errTitle.style.display='none'; _dom.errBox.style.display='none'; _dom.errBox.textContent=''; }
      },
      onTerminal: async ()=>{ onStatusKind('idle'); }
    });
  }

  return { loadGraph, startObserve, ensureAndHighlight };
}

 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
