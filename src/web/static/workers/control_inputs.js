


// Petit module d'inputs pour run_until et breakpoints
import { t } from './i18n.js';

export class ControlInputs{
  constructor(toolbarEl, worker, hooks){
    this.el = document.createElement('div');
    this.el.style.display='flex'; this.el.style.gap='6px'; this.el.style.alignItems='center';
    this.el.innerHTML = `
      <span style="margin-left:8px;color:#6b7280;font-size:12px">${t('control_inputs.debug_label','Debug:')}</span>
      <input aria-label="${t('control_inputs.node_id','Node ID')}" title="${t('control_inputs.node_id','Node ID (SG::STEP)')}" type="text" placeholder="SG::STEP" size="18" data-ci="node">
      <select aria-label="${t('control_inputs.when','When')}" title="${t('control_inputs.when','When condition')}" data-ci="when">
        <option value="always" selected>${t('control_inputs.when_always','always')}</option>
        <option value="success">${t('control_inputs.when_success','success')}</option>
        <option value="fail">${t('control_inputs.when_fail','fail')}</option>
        <option value="retry">${t('control_inputs.when_retry','retry')}</option>
      </select>
      <button class="btn" data-ci-act="run-until">${t('control_inputs.run_until','Run until')}</button>
      <button class="btn" data-ci-act="break-add">${t('control_inputs.break_add','Add break')}</button>
      <button class="btn" data-ci-act="break-remove">${t('control_inputs.break_remove','Remove break')}</button>
    `;
    toolbarEl.appendChild(this.el);
    this.worker = worker; this.hooks = hooks||{};
    this.el.addEventListener('click', async (e)=>{
      const b = e.target.closest('button[data-ci-act]'); if (!b) return;
      const act = b.getAttribute('data-ci-act');
      const node = this.el.querySelector('[data-ci="node"]').value.trim(); if (!node) return;
      const when = (this.el.querySelector('[data-ci="when"]').value||'always');
      try{
        if (act==='run-until' && this.hooks.onRunUntil) await this.hooks.onRunUntil(node, when);
        if (act==='break-add' && this.hooks.onBreakAdd) await this.hooks.onBreakAdd(node, when);
        if (act==='break-remove' && this.hooks.onBreakRemove) await this.hooks.onBreakRemove(node, when);
      }catch(err){ console.warn('control_inputs action error', err); }
    });
  }
}
