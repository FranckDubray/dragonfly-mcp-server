


import { h } from './dom.js';
import { toast } from './toast.js';
import { createModal } from './modal.js';
import { buildAddWorkerModalUI, updateSummary } from './add_worker_form.js';
import { renderConfigHuman, redactPromptsDeep } from './add_worker_helpers.js';
import { wireStartNewWorker } from './add_worker_submit.js';
import { t } from './i18n.js';

// Public API: openAddWorkerModal
export async function openAddWorkerModal(){
  const modal = createModal({ title: t('add_worker.modal_title','Add worker'), width: '840px' });
  const status = h('div',{class:'help-text','aria-live':'polite'});

  // Construit le squelette UI
  const {form, bCreate, bClose, fieldTpl, fieldFirst, fieldLeader, tplDesc, cfgHost, summary} = buildAddWorkerModalUI(modal, status);

  // Chargement templates & leaders
  async function loadData(){
    try{
      const [tplResp, leadResp] = await Promise.all([
        fetch('/workers/api/templates').then(r=>r.json()).catch(()=>({templates:[]})),
        fetch('/workers/api/leaders').then(r=>r.json()).catch(()=>({leaders:[]})),
      ]);
      const templates = Array.isArray(tplResp.templates)? tplResp.templates : [];
      const leaders = Array.isArray(leadResp.leaders)? leadResp.leaders : [];

      fieldTpl.innerHTML = '';
      templates.forEach(tpl => {
        const o = document.createElement('option');
        o.value = tpl.name; o.textContent = tpl.title || tpl.name; o.title = tpl.description || '';
        fieldTpl.appendChild(o);
      });
      await onTplChange();

      fieldLeader.innerHTML = '';
      if (!leaders.length){
        const o = document.createElement('option'); o.value=''; o.textContent=t('add_worker.none_leader','(no leader)'); fieldLeader.appendChild(o);
        status.className='error-text'; status.textContent=t('add_worker.none_leader_hint','No leader found — create a leader before adding a worker.');
      } else {
        leaders.forEach(l => {
          const o = document.createElement('option');
          const dn = (l.identity||{}).display_name || l.name;
          o.value = l.name; o.textContent = dn;
          fieldLeader.appendChild(o);
        });
      }
      updateSummary(summary, fieldTpl.value||'', fieldFirst.value||'');
    } finally {
      // rien
    }
  }
  async function onTplChange(){
    const tpl=(fieldTpl.value||'').trim();
    cfgHost.innerHTML = '';
    if (!tpl) return; 
    try{
      const r = await fetch(`/workers/api/templates?name=${encodeURIComponent(tpl)}`);
      const js = await r.json();
      tplDesc.textContent = (js.docs?.description || '').trim();
      const cleaned = redactPromptsDeep(js.config || {});
      renderConfigHuman(cfgHost, cleaned);
    }catch{
      const pre = document.createElement('pre'); pre.className='io-pre'; pre.textContent = t('add_worker.template_config_error','Unable to load template config');
      cfgHost.appendChild(pre);
    }
  }

  fieldTpl.addEventListener('change', async ()=>{ await onTplChange(); updateSummary(summary, fieldTpl.value||'', fieldFirst.value||''); });
  fieldFirst.addEventListener('input', ()=> updateSummary(summary, fieldTpl.value||'', fieldFirst.value||''));
  bClose.addEventListener('click', () => modal.close());

  // Soumission officielle new_worker
  wireStartNewWorker(form, modal, status);

  modal.open();
  await loadData();
}
