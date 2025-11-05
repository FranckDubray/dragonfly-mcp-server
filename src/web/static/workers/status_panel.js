
import { api } from './api.js';
import { formatLocalTs } from './process_utils.js';

export class StatusPanel{
  constructor(root, worker){
    this.worker = worker;
    this.box = document.createElement('div');
    this.box.className = 'panel';
    this.title = document.createElement('h3');
    // i18n title via t if available
    let titleTxt = 'Statut & métriques';
    try{ const mod = window.__i18n__ || null; if (mod && typeof mod.t==='function') titleTxt = mod.t('status.panel_title','Status & metrics'); }catch{}
    this.title.textContent = titleTxt;
    this.pre = document.createElement('pre'); this.pre.className = 'io-pre';
    this.box.append(this.title, this.pre);
    root.prepend(this.box);
    this.loop();
  }
  async loop(){
    try{
      const js = await api.status(this.worker);
      const view = {
        phase: js.phase || js.status,
        pid: js.pid,
        db_path: js.db_path,
        heartbeat: js.heartbeat,
        heartbeat_local: formatLocalTs(js.heartbeat||''),
        recent_steps: [],
        metrics: js.metrics || {},
        preflight_warnings: js.preflight_warnings || [],
        preflight_errors: js.preflight_errors || [],
      };
      const steps = (js.recent_steps||[]).slice(-5);
      view.recent_steps = steps.map(s=>({
        ...s,
        started_at_local: formatLocalTs(s.started_at||''),
        finished_at_local: formatLocalTs(s.finished_at||''),
      }));
      this.pre.textContent = JSON.stringify(view, null, 2);
    }catch(e){ /* noop */ }
    setTimeout(()=>this.loop(), 4000);
  }
}
