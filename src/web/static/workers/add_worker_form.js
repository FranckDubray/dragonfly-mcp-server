
import { h } from './dom.js';
import { toast } from './toast.js';
import { slugify, redactPromptsDeep, renderConfigHuman } from './add_worker_helpers.js';

export function buildAddWorkerModalUI(modal, status){
  const wrap = h('div',{class:'form-two'});
  const form = h('form',{class:'form-grid'});
  const aside = h('div',{class:'panel'});

  const fieldTpl = h('select',{ 'aria-label':'Template', class:'input' });
  const tplDesc = h('div',{class:'field-desc'});
  const fieldFirst = h('input',{ type:'text', placeholder:'Prénom', 'aria-label':'Prénom', class:'input' });
  const fieldLeader = h('select',{ 'aria-label':'Leader', class:'input' });

  const actions = h('div',{class:'form-actions'});
  const bCreate = h('button',{class:'btn primary', type:'submit'},'Créer le worker');
  const bClose = h('button',{class:'btn ghost', type:'button'},'Fermer');
  actions.append(bClose, bCreate);

  form.append(
    labelWrap('Template', fieldTpl, tplDesc),
    labelWrap('Prénom', fieldFirst),
    labelWrap('Leader', fieldLeader),
    actions
  );

  const cfgTitle = h('h3',{},'Paramètres de config (template) – lecture seule');
  const cfgHint = h('div',{class:'hint'},"Aperçu lisible de la configuration du template. Aucun champ n'est éditable ici.");
  const cfgHost = h('div');
  const summary = h('div',{class:'summary panel'});
  summary.innerHTML = `
    <h3>Résumé</h3>
    <div class="kv">
      <div class="k">Worker name</div><div class="v" data-f="wn">—</div>
      <div class="k">Process</div><div class="v" data-f="wf">—</div>
    </div>`;

  aside.append(summary, cfgTitle, cfgHint, cfgHost);
  wrap.append(form, aside);
  modal.body.append(status, wrap);

  return {form, bCreate, bClose, fieldTpl, fieldFirst, fieldLeader, tplDesc, cfgHost, summary};
}

export function updateSummary(summary, tpl, first){
  const wn = `${slugify(tpl)}_${slugify(first)}`.replace(/^_+|_+$/g,'');
  const wf = tpl ? `workers/${tpl}/process.py` : '';
  summary.querySelector('[data-f="wn"]').textContent = wn || '—';
  summary.querySelector('[data-f="wf"]').textContent = wf || '—';
}

export function labelWrap(label, input, under=null){
  const box = h('label',{class:'field'},[ h('div',{},label), input ]);
  if (under) box.appendChild(under);
  return box;
}

export async function loadTemplatePreview(fieldTpl, tplDesc, cfgHost){
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
    const pre = document.createElement('pre'); pre.className='io-pre'; pre.textContent = 'Impossible de charger la config du template';
    cfgHost.appendChild(pre);
  }
}
