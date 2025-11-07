
(function(global){
  const Core = global.WorkersGridCore || {};
  function dbg(){ try{ if (global.__WG_DEBUG) console.log('[WG][tools]', ...arguments); }catch{} }

  let __toolsIdx = null, __toolsTs = 0;
  let __toolsIdxNorm = null; // normalized key -> rec
  const TOOLS_TTL = 15*60*1000;

  function _normKey(s){
    try{
      return String(s||'').toLowerCase()
        .replace(/[^a-z0-9]+/g, '_')
        .replace(/_+/g, '_')
        .replace(/^_+|_+$/g, '');
    }catch{ return String(s||''); }
  }

  async function ensureToolsIndex(){
    const now = Date.now();
    if (__toolsIdx && (now - __toolsTs) < TOOLS_TTL){ dbg('cache hit', __toolsIdx.size); return __toolsIdx; }
    try{
      let r = await fetch('/tools');
      let js = await r.json().catch(()=>null);
      if (!r.ok || !js || !Array.isArray(js.tools) || js.tools.length===0){
        const rr = await fetch('/tools?reload=1&list=1');
        js = await rr.json().catch(()=>null);
      }
      const arr = Array.isArray(js?.tools) ? js.tools : [];
      const idx = new Map();
      const nidx = new Map();
      let cntTool=0, cntOther=0;
      for (const t of arr){
        const keyRaw = String(t.name||'').trim(); if (!keyRaw) continue;
        const key = keyRaw.toLowerCase();
        const label = String(t.display_name || t.displayName || t.title || t.name || keyRaw).trim();
        const desc  = String(t.description || '').trim();
        const kind  = String(t.kind || '').trim().toLowerCase();
        if (kind==='tool') cntTool++; else cntOther++;
        const rec = { label, desc, kind, key: keyRaw };
        idx.set(key, rec);
        // normalized variants for robust lookup
        const variants = new Set([
          _normKey(keyRaw),
          _normKey(keyRaw.replace(/_/g,'-')),
          _normKey(keyRaw.replace(/-/g,'_')),
        ]);
        variants.forEach(v => { if (v) nidx.set(v, rec); });
      }
      __toolsIdx = idx; __toolsIdxNorm = nidx; __toolsTs = now;
      dbg('loaded', idx.size, 'kinds:', {tool:cntTool, other:cntOther}, 'norm:', nidx.size);
      if (idx.size === 0) __toolsTs = 0;
    }catch(e){ dbg('error', e); __toolsIdx = new Map(); __toolsIdxNorm = new Map(); __toolsTs = 0; }
    return __toolsIdx;
  }

  function resolveToolLabelSync(raw, idx){
    try{
      const s = String(raw||'').trim(); if (!s) return { text:'', tip:'', kind:'' };
      const parts = s.split(':', 2); // base[:op]
      const base = parts[0];
      const op = (parts.length>1)? parts[1] : '';
      const k = String(base||'').toLowerCase();
      let rec = idx && idx.get(k);
      if (!rec && __toolsIdxNorm){
        const nk = _normKey(base);
        rec = __toolsIdxNorm.get(nk);
      }
      if (!rec){
        return { text: s, tip: '', kind: '' };
      }
      const text = rec.label;
      const tip  = op ? `${rec.desc?rec.desc+'\n':''}operation: ${op}` : (rec.desc||'');
      return { text, tip, kind: rec.kind || '' };
    }catch{ return { text:String(raw||''), tip:'', kind:'' }; }
  }

  async function resolveToolLabel(raw){
    const idx = await ensureToolsIndex();
    const res = resolveToolLabelSync(raw, idx);
    dbg('resolveToolLabel', raw, '=>', res);
    return res;
  }

  function isToolName(name){
    try{
      const base = String((name||'').split(':',2)[0]).trim();
      const idx = __toolsIdx; if (!idx) return false;
      const rec = idx.get(base.toLowerCase()) || (__toolsIdxNorm && __toolsIdxNorm.get(_normKey(base)));
      const ok = !!(rec && rec.kind === 'tool');
      dbg('isToolName', name, '=>', ok, rec);
      return ok;
    }catch{ return false; }
  }

  async function refineChipsAfterRegistry(){
    try{
      const idx = await ensureToolsIndex();
      if (!idx || idx.size===0){ dbg('refine: idx empty'); return; }
      document.querySelectorAll('.card .tools .tool').forEach(async el=>{
        const name = el.getAttribute('data-tool')||'';
        const res = resolveToolLabelSync(name, idx);
        if (res.kind && res.kind !== 'tool'){ dbg('refine: remove non-tool', name, res); el.remove(); return; }
        el.textContent = res.text || name;
        if (res.tip) el.setAttribute('data-tip', res.tip); else el.removeAttribute('data-tip');
        dbg('refine: set', name, 'label:', res.text);
      });
    }catch(e){ dbg('refine error', e); }
  }

  global.WGLiveTools = { ensureToolsIndex, resolveToolLabelSync, resolveToolLabel, isToolName, refineChipsAfterRegistry };
})(window);
