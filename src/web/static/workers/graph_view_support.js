
// Helpers specific to GraphView: resolve worker file and wait for phase
import { api } from './api.js';

// Resolve workers/<template>/process.py from identity response
export async function resolveWorkerFile(worker){
  try{
    const r = await fetch(`/workers/api/identity?worker=${encodeURIComponent(worker)}`);
    const js = await r.json();
    // Prefer top-level template (API provides it), fallback to identity.template if present
    const tpl = (js && (js.template || (js.identity && js.identity.template))) ? String(js.template || js.identity.template).trim() : '';
    if (!tpl) return '';
    return `workers/${tpl}/process.py`;
  }catch{ return ''; }
}

export async function waitForPhase(worker, phases = ['starting','running'], timeoutMs = 5000, tickMs = 200){
  const deadline = Date.now() + Math.max(0, timeoutMs||0);
  while(Date.now() < deadline){
    try{
      const js = await api.status(worker);
      const ph = String(js.phase || js.status || '').toLowerCase();
      if (phases.includes(ph)) return ph;
    }catch{}
    await new Promise(r=>setTimeout(r, tickMs));
  }
  return '';
}
