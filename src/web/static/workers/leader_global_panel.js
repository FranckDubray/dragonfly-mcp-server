


import { LeaderChatPanel } from './leader_chat_panel.js';
import { t } from './i18n.js';

export class LeaderGlobalPanel{
  constructor(root){ this.root=root; this.box=document.createElement('div'); this.box.className='panel'; this.title=document.createElement('h3'); this.title.textContent=t('leader_global.title','Leader — Global chat'); this.body=document.createElement('div'); this.box.append(this.title, this.body); root.appendChild(this.box); this._chat=null; this._leader=''; this._form=null; this.init(); }
  async init(){ await this.renderShell(); const leaders = await this.detectLeaders(); this.populateLeaders(leaders); if (leaders.length===1){ this.select.value = leaders[0]; this.onLeaderChange(); } }
  async detectLeaders(){
    // Source of truth: dedicated API that scans leader_*.db only
    try{
      const r = await fetch('/workers/api/leaders');
      const js = await r.json();
      const items = Array.isArray(js.leaders)? js.leaders : [];
      return items.map(it=> String(it?.name||'').trim()).filter(Boolean);
    }catch{ return []; }
  }
  async renderShell(){
    this.body.innerHTML='';
    const line = document.createElement('div'); line.style.display='flex'; line.style.gap='8px'; line.style.alignItems='center';
    const lab = document.createElement('span'); lab.style.fontSize='12px'; lab.style.color='#6b7280'; lab.textContent=t('leader_global.select_label','Leader:');
    const sel = document.createElement('select'); sel.setAttribute('aria-label',t('leader_global.select_aria','Select leader')); this.select=sel; sel.onchange=()=>this.onLeaderChange();
    line.append(lab, sel); this.body.appendChild(line);
    // Identity form
    const form = document.createElement('form'); form.style.marginTop='8px'; this._form=form;
    form.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
        <label>${t('leader_global.display','Display name')}<br><input name="display_name" placeholder="Rolland"/></label>
        <label>${t('leader_global.role','Role')}<br><input name="role" placeholder="Leader"/></label>
        <label>${t('leader_global.persona','Persona')}<br><input name="persona" placeholder="${t('leader_global.persona_ph','Orchestrator of workers')}"/></label>
      </div>
      <div style="margin-top:8px;display:flex;gap:8px"><button class="btn primary" type="submit">${t('common.save','Save')}</button></div>
    `;
    form.addEventListener('submit',(e)=>{ e.preventDefault(); this.saveIdentity(); });
    this.body.appendChild(form);
    // Chat holder
    const chatHolder = document.createElement('div'); chatHolder.style.marginTop='8px'; this.body.appendChild(chatHolder);
    // Create chat panel placeholder
    this._chat = new LeaderChatPanel(chatHolder, '');
  }
  populateLeaders(list){ this.select.innerHTML=''; if (!list.length){ const o=document.createElement('option'); o.textContent=t('leader_global.none_detected','(no leader detected)'); this.select.appendChild(o); } else { list.forEach(n=>{ const o=document.createElement('option'); o.value=n; o.textContent='@'+n; this.select.appendChild(o); }); } }
  async onLeaderChange(){ const leader = this.select.value||''; if (!leader) return; this._leader=leader; await this.loadIdentity(); try{ await this._chat.openGlobal(leader); }catch{} }
  async loadIdentity(){ try{ const r=await fetch(`/workers/api/leader_identity?name=${encodeURIComponent(this._leader)}`); const js = await r.json(); const id = js.identity||{}; const set=(n,v)=>{ const el=this._form.querySelector(`[name="${n}"]`); if(el) el.value = (v||''); }; set('display_name', id.display_name); set('role', id.role); set('persona', id.persona);}catch{} }
  async saveIdentity(){ if (!this._leader) return; const data={ display_name:this._form.display_name.value.trim(), role:this._form.role.value.trim(), persona:this._form.persona.value.trim() }; try{ await fetch(`/workers/api/leader_identity?name=${encodeURIComponent(this._leader)}`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data)}); }catch{} }
}
