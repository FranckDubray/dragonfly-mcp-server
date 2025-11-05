


// Leader Identity Panel: view/edit leader identity (from leader_<name>.db)
import { t } from './i18n.js';
export class LeaderIdentityPanel{
  constructor(root, worker){ this.root=root; this.worker=worker; this.leader=''; this.box=document.createElement('div'); this.box.className='panel'; this.title=document.createElement('h3'); this.title.textContent='Leader'; this.body=document.createElement('div'); this.box.append(this.title, this.body); root.appendChild(this.box); this.init(); }
  async init(){
    // Get worker identity to know leader name
    try{
      const r = await fetch(`/workers/api/identity?worker=${encodeURIComponent(this.worker)}`);
      const js = await r.json();
      const ident = (js.identity)||{}; this.leader = (ident.leader||'').trim();
      this.renderShell();
      if (this.leader){
        await this.loadLeader();
        await this.loadWorkersUnderLeader();
      } else {
        this.body.innerHTML = `<small style="color:#6b7280">${t('leader_identity_panel.no_leader','No leader assigned')}</small>`;
      }
    }catch(e){ this.body.textContent = t('leader_identity_panel.error_read','Error reading worker identity'); }
  }
  renderShell(){
    this.body.innerHTML = '';
    const top = document.createElement('div'); top.style.display='flex'; top.style.gap='8px'; top.style.alignItems='center';
    const name = document.createElement('strong'); name.textContent = this.leader?(`@${this.leader}`):'(leader?)';
    const btn = document.createElement('button'); btn.className='btn'; btn.textContent=t('leader_identity_panel.refresh','Refresh'); btn.onclick=()=>{ this.loadLeader(); this.loadWorkersUnderLeader(); };
    top.append(name, btn);
    this.form = document.createElement('form'); this.form.style.marginTop='8px';
    this.form.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
        <label>${t('leader_identity_panel.display','Display name')}<br><input name="display_name" placeholder="Rolland"/></label>
        <label>${t('leader_identity_panel.role','Role')}<br><input name="role" placeholder="Leader"/></label>
        <label>${t('leader_identity_panel.persona','Persona')}<br><input name="persona" placeholder="${t('leader_identity_panel.persona_ph','Orchestrator of workers')}"/></label>
      </div>
      <div style="margin-top:8px;display:flex;gap:8px"><button class="btn primary" type="submit">${t('common.save','Save')}</button><button class="btn" type="button" data-act="see-global">${t('leader_identity_panel.global_chat','Global chat')}</button></div>
    `;
    this.form.addEventListener('submit', (e)=>{ e.preventDefault(); this.save(); });
    this.form.querySelector('[data-act="see-global"]').addEventListener('click',()=>{
      const ev = new CustomEvent('leader:openGlobalChat', {detail:{leader:this.leader}});
      window.dispatchEvent(ev);
    });

    // Workers under this leader
    this.listBox = document.createElement('div'); this.listBox.className='panel';
    const h3 = document.createElement('h3'); h3.textContent = t('leader_identity_panel.leader_workers','Leader’s workers');
    this.listContent = document.createElement('div'); this.listContent.textContent = t('leader_identity_panel.loading','Loading…');
    this.listBox.append(h3, this.listContent);

    this.body.append(top, this.form, this.listBox);
  }
  async loadLeader(){
    if (!this.leader){ this.body.innerHTML=`<small style="color:#6b7280">${t('leader_identity_panel.no_leader','No leader assigned')}</small>`; return; }
    try{
      const r = await fetch(`/workers/api/leader_identity?name=${encodeURIComponent(this.leader)}`);
      const js = await r.json();
      const id = js.identity||{};
      const set=(n,v)=>{ const el=this.form.querySelector(`[name="${n}"]`); if(el) el.value = (v||''); };
      set('display_name', id.display_name); set('role', id.role); set('persona', id.persona);
    }catch(e){ /* noop */ }
  }
  async loadWorkersUnderLeader(){
    if (!this.leader){ this.listContent.textContent = '—'; return; }
    try{
      const r = await fetch('/workers/api/list');
      const js = await r.json();
      const items = Array.isArray(js.workers) ? js.workers : [];
      const matches = [];
      for (const w of items){
        const wn = (w && w.worker_name) ? String(w.worker_name).trim() : '';
        if (!wn) continue;
        try{
          const ir = await fetch(`/workers/api/identity?worker=${encodeURIComponent(wn)}`);
          const idj = await ir.json();
          const leader = ((idj.identity||{}).leader || '').trim();
          if (leader && leader === this.leader) matches.push(wn);
        }catch{}
      }
      if (!matches.length){ this.listContent.textContent = t('leader_identity_panel.none_attached','No attached workers'); return; }
      const ul = document.createElement('ul'); ul.style.margin='6px 0';
      matches.sort().forEach(wn=>{
        const li = document.createElement('li');
        const a = document.createElement('a'); a.href = `/workers/${encodeURIComponent(wn)}`; a.textContent = wn;
        li.appendChild(a); ul.appendChild(li);
      });
      this.listContent.innerHTML=''; this.listContent.appendChild(ul);
    }catch(e){ this.listContent.textContent = t('leader_identity_panel.error_load','Loading error'); }
  }
  async save(){
    if (!this.leader) return;
    const data = {
      display_name: this.form.display_name.value.trim(),
      role: this.form.role.value.trim(),
      persona: this.form.persona.value.trim(),
    };
    try{
      const r = await fetch(`/workers/api/leader_identity?name=${encodeURIComponent(this.leader)}`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data)});
      await r.json();
    }catch(e){ /* noop */ }
  }
}
