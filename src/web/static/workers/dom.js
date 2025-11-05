







// DOM and view helpers
export function h(tag, attrs = {}, children = []){
  const n = document.createElement(tag);
  for (const [k,v] of Object.entries(attrs||{})){
    if (k === 'class') n.className = v; else if (v!=null) n.setAttribute(k, String(v));
  }
  (Array.isArray(children)?children:[children]).forEach(c=>{ if(c==null) return; n.appendChild(typeof c==='string'?document.createTextNode(c):c); });
  return n;
}
export function phaseDot(phase){ const p=(phase||'').toLowerCase(); if (p==='failed') return 'dot-error'; if (p==='running'||p==='starting') return 'dot-running'; return 'dot-idle'; }
export function frPhase(phase){
  // delegate translation to i18n if available
  try{
    const mod = window.__i18n__ || null;
    // fallback mapping if i18n not initialized yet
    const map = { failed: 'En échec', running: 'Actif', starting: 'Actif', completed: 'Terminé', canceled: 'Annulé', idle: 'En veille', unknown: 'En veille' };
    const p=(phase||'').toLowerCase();
    if (!mod || !mod.t) return map[p] || map.unknown;
    const dict = { failed: 'status.failed', running: 'status.running', starting: 'status.starting', completed: 'status.completed', canceled: 'status.canceled', idle: 'status.idle', unknown: 'status.unknown' };
    return mod.t(dict[p]||'status.unknown');
  }catch{ const map = { failed: 'En échec', running: 'Actif', starting: 'Actif', completed: 'Terminé', canceled: 'Annulé', idle: 'En veille', unknown: 'En veille' }; const p=(phase||'').toLowerCase(); return map[p] || map.unknown; }
}
export function toolClass(name){ const n=String(name||'').toLowerCase(); if(n.includes('call_llm')||n.includes('llm')) return 't-llm'; if(n.includes('web')) return 't-web'; if(n.includes('scrape')) return 't-scrape'; if(n.includes('arxiv')) return 't-arxiv'; if(n.includes('gmail')) return 't-gmail'; if(n.includes('meteo')||n.includes('météo')) return 't-meteo'; return ''; }
export function gaugeRatio(spm, max=1500){ const v=Number(spm)||0; const m=Number(max)||1500; return Math.max(0, Math.min(1, v/m)); }
export function timeAgo(iso){ try{ if(!iso) return '—'; const t=new Date(iso).getTime(); if(!t) return '—'; const s=Math.max(0,(Date.now()-t)/1000); if(s<60) return `${Math.floor(s)}s`; const m=s/60; if(m<60) return `${Math.floor(m)}m`; const h=m/60; if(h<24) return `${Math.floor(h)}h`; const d=h/24; return `${Math.floor(d)}j`; }catch{ return '—'; } }
export function formatNum(n){ const num=Number(n); if(!isFinite(num)) return String(n||'—'); if(num>=1e6) return (Math.round(num/1e5)/10)+'M'; if(num>=1e3) return (Math.round(num/100)/10)+'k'; return String(num); }

