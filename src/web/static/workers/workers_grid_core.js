
(function(global){
  const Core = {};

  Core.h = function h(tag, attrs = {}, children = []){
    const n = document.createElement(tag);
    for (const [k,v] of Object.entries(attrs||{})){
      if (k === 'class') n.className = v; else if (v!=null) n.setAttribute(k, String(v));
    }
    (Array.isArray(children)?children:[children]).forEach(c=>{ if(c==null) return; n.appendChild(typeof c==='string'?document.createTextNode(c):c); });
    return n;
  };

  Core.formatLocalTs = function formatLocalTs(iso){
    try{ if(!iso) return ''; const d=new Date(iso); if(!isFinite(d.getTime())) return String(iso); return d.toLocaleString(undefined,{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'}); }catch{ return String(iso||''); }
  };

  Core.apiList = async function(){ const r=await fetch('/workers/api/list'); if(!r.ok) throw 0; return r.json(); };
  Core.apiStatusMCP = async function(w){ const payload={ tool:'py_orchestrator', params:{ operation:'status', worker_name:w, include_metrics:true } }; const r=await fetch('/execute',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) }); if(!r.ok) throw 0; return r.json(); };
  Core.apiIdentity = async function(w){ const r=await fetch(`/workers/api/identity?worker=${encodeURIComponent(w)}`); if(!r.ok) throw 0; return r.json(); };

  Core.phaseDot = function(phase){ const p=(phase||'').toLowerCase(); if (p==='failed') return 'dot-error'; if (p==='running'||p==='starting') return 'dot-running'; return 'dot-idle'; };
  Core.frPhase = function(phase){ try{ const mod = window.__i18n__ || null; const map = { failed: 'En échec', running: 'Actif', starting: 'Actif', completed: 'Terminé', canceled: 'Annulé', idle: 'En veille', unknown: 'En veille' }; const p=(phase||'').toLowerCase(); if (!mod || !mod.t) return map[p] || map.unknown; const dict = { failed: 'status.failed', running: 'status.running', starting: 'status.starting', completed: 'status.completed', canceled: 'status.canceled', idle: 'status.idle', unknown: 'status.unknown' }; return mod.t(dict[p]||'status.unknown'); }catch{ const map = { failed: 'En échec', running: 'Actif', starting: 'Actif', completed: 'Terminé', canceled: 'Annulé', idle: 'En veille', unknown: 'En veille' }; const p=(phase||'').toLowerCase(); return map[p] || map.unknown; } };
  Core.toTitle = function(s){ try{ s=String(s||'').trim(); if(!s) return ''; return s.split(/\s+/).map(w=> w.charAt(0).toUpperCase()+w.slice(1)).join(' '); }catch{return String(s||''); } };
  Core.firstFromSlug = function(slug){ try{ const last=(String(slug||'').split('_').filter(Boolean).pop()||String(slug||'')); return Core.toTitle(last.replace(/[-]+/g,' ')); }catch{ return String(slug||''); } };
  Core.resolveAsset = function(url){ const u = String(url||'').trim(); if (!u) return ''; if (/^https?:\/\//i.test(u)) return u; if (u.startsWith('/')) return u; return `/docs/images/${u}`; };
  Core.setAvatarAura = function(card, {phase, running_kind, sleeping}){ try{ const av = card.querySelector('.avatar'); if (!av) return; av.classList.add('aura'); av.classList.remove('a--running','a--tool','a--sleep','a--stop-ok','a--stop-err'); const p = String(phase||'').toLowerCase(); const rk = String(running_kind||''); if (p === 'failed'){ av.classList.add('a--stop-err'); return; } if (rk === 'tool'){ av.classList.add('a--tool'); return; } if (p === 'running' || p === 'starting'){ if (sleeping) av.classList.add('a--sleep'); else av.classList.add('a--running'); return; } av.classList.add('a--stop-ok'); }catch{} };

  Core.sanitizeWorkers = function(list){ const items = (list?.workers || []).filter(Boolean); const map = new Map(); for (const w of items){ const wn = String(w?.worker_name||'').trim(); if (!wn || wn.startsWith('leader_')) continue; if (!map.has(wn)) map.set(wn, w); } return Array.from(map.values()); };

  global.WorkersGridCore = Core;
})(window);
