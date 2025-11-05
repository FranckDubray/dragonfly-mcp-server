

















import { toast } from './toast.js';

export function wireStartNewWorker(form, modal, status){
  const submit = async (e)=>{
    e.preventDefault();
    status.textContent=''; status.className='help-text';
    const tplEl = form.querySelector('select[aria-label="Template"]');
    const firstEl = form.querySelector('input[aria-label="Prénom"]');
    const leaderEl = form.querySelector('select[aria-label="Leader"]');
    const tpl = String(tplEl && tplEl.value || '').trim();
    const first = String(firstEl && firstEl.value || '').trim();
    const leader = String(leaderEl && leaderEl.value || '').trim();
    // NOW REQUIRED: leader must be selected at creation
    if (!tpl || !first || !leader){
      status.className='error-text';
      status.textContent='Template, prénom et leader requis.';
      return;
    }
    try{
      // Use MCP /execute instead of /workers/api/start
      const payload = {
        tool: 'py_orchestrator',
        params: {
          operation: 'start',
          // new_worker flow: delegate derivation to orchestrator
          new_worker: { first_name: first, template: tpl },
          leader: { name: leader },
          hot_reload: true
        }
      };
      const resp = await fetch('/execute', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
      const js = await resp.json().catch(()=>({}));
      if (!resp.ok || (js && js.accepted===false)){
        status.className='error-text'; status.textContent = (js && (js.message||js.status)) || 'Création échouée';
        return;
      }
      try{ toast('Worker créé'); }catch{}
      modal.close(); location.reload();
    }catch(err){ status.className='error-text'; status.textContent='Création échouée'; }
  };
  form.addEventListener('submit', submit);
}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
