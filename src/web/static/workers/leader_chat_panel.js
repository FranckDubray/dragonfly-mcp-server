


// Leader Chat Panel (scopé worker OU global via event) — envoi immédiat + anim "typing"
import { t } from './i18n.js';

function bubble(role, content){
  const wrap = document.createElement('div');
  wrap.className = 'chat-bubble ' + (role==='user'?'user':'assistant');
  const who = document.createElement('div'); who.className='who'; who.textContent = (role==='user')? t('chat.you','You') : t('chat.assistant','LLM');
  const body = document.createElement('div'); body.className='content'; body.textContent = String(content||'');
  wrap.append(who, body);
  return wrap;
}
function makeTypingBubble(){
  const b = bubble('assistant', '…');
  const body = b.querySelector('.content'); let dots=1, alive=true;
  const timer = setInterval(()=>{ if(!alive) return; dots=(dots%3)+1; body.textContent='.'.repeat(dots); }, 450);
  b.__typingStop = ()=>{ alive=false; clearInterval(timer); };
  return b;
}

export class LeaderChatPanel{
  constructor(root, worker){ this.root=root; this.worker=worker; this.box=document.createElement('div'); this.box.className='panel'; this.title=document.createElement('h3'); this.title.textContent=t('chat.leader_panel_title','Leader Chat'); this.body=document.createElement('div'); this.box.append(this.title, this.body); root.appendChild(this.box); this.init(); }
  async init(){ this.renderShell(); this.loadHistory(); window.addEventListener('leader:openGlobalChat', (e)=>{ const leader = (e.detail||{}).leader||''; if(leader) this.openGlobal(leader); }); }
  renderShell(){
    this.body.innerHTML='';
    const hist = document.createElement('div'); hist.className='chat-list'; hist.style.maxHeight='240px'; hist.style.overflow='auto'; hist.setAttribute('aria-live','polite'); this.hist=hist;
    const form = document.createElement('form'); form.style.marginTop='8px';
    form.innerHTML = `<div style="display:flex;gap:8px"><input name="q" placeholder="${t('chat.placeholder','Message...')}" style="flex:1"><button class="btn primary" type="submit">${t('common.send','Send')}</button></div>`;
    form.addEventListener('submit',(e)=>{ e.preventDefault(); const v=form.q.value.trim(); if(!v) return; this.send(v); form.q.value=''; });
    // Traces tools (collapsible)
    const tracesWrap = document.createElement('div'); tracesWrap.className='collapsible'; tracesWrap.style.marginTop='6px'; this.tracesWrap=tracesWrap;
    const toggle = document.createElement('a'); toggle.href='#'; toggle.className='toggle-link'; toggle.textContent=t('chat.tools_trace','View tools trace'); toggle.onclick=(ev)=>{ ev.preventDefault(); tracesWrap.classList.toggle('more'); };
    this.body.append(hist, form, toggle, tracesWrap);
  }
  async loadHistory(){
    try{ const r = await fetch(`/workers/api/leader_chat?worker=${encodeURIComponent(this.worker)}&limit=20`); const js = await r.json(); this.renderHistory(js.history||[]); }
    catch(e){ this.hist.textContent=t('chat.error_history','Error loading history'); }
  }
  renderHistory(items){
    this.hist.innerHTML = '';
    items.forEach(m=>{ this.hist.appendChild(bubble(m.role||'assistant', m.content||'')); });
    this.hist.scrollTop = this.hist.scrollHeight;
  }
  renderTraces(tools){
    this.tracesWrap.innerHTML = '';
    (tools||[]).forEach(ti=>{ const pre = document.createElement('pre'); pre.className='io-pre'; pre.textContent = JSON.stringify(ti, null, 2); this.tracesWrap.appendChild(pre); });
  }
  async send(msg){
    // 1) append immédiat du message utilisateur
    const userB = bubble('user', msg); this.hist.appendChild(userB); this.hist.scrollTop = this.hist.scrollHeight;
    // 2) anim typing
    const typing = makeTypingBubble(); this.hist.appendChild(typing); this.hist.scrollTop = this.hist.scrollHeight;
    try{
      const r = await fetch(`/workers/api/leader_chat?worker=${encodeURIComponent(this.worker)}&message=${encodeURIComponent(msg)}`, {method:'POST'});
      const js = await r.json();
      // stop anim et remplacer par résultat
      try{ typing.__typingStop && typing.__typingStop(); }catch{}
      const body = typing.querySelector('.content');
      if (!js || js.accepted === false || js.status !== 'ok'){
        const m = (js && (js.message || js.status)) || t('common.error_action','Action failed');
        body.textContent = `❌ ${m}`;
        try{ const mod = await import('./toast.js'); mod.toast(m, 'err'); }catch{}
      } else {
        body.textContent = (js.content||'').trim() || t('chat.empty_reply','(empty reply)');
      }
      // traces
      this.renderTraces(js?.tools_preview||[]);
    }
    catch(e){ try{ typing.__typingStop && typing.__typingStop(); }catch{} const body = typing.querySelector('.content'); body.textContent = `❌ ${t('common.error_network','Network error')}`; }
  }
  // Global chat (leader scope) — mêmes comportements
  async openGlobal(leader){
    this.title.textContent = `Leader — ${t('chat.global','Global chat')} (@${leader})`;
    this._global_leader = leader;
    await this.loadGlobalHistory(leader);
    const form = this.body.querySelector('form');
    form.onsubmit = (e)=>{ e.preventDefault(); const v=form.q.value.trim(); if(!v) return; this.sendGlobal(leader, v); form.q.value=''; };
  }
  async loadGlobalHistory(leader){
    try{ const r = await fetch(`/workers/api/leader_chat_global?name=${encodeURIComponent(leader)}&limit=30`); const js = await r.json(); this.renderHistory(js.history||[]); }
    catch(e){ this.hist.textContent=t('chat.error_history_global','Error loading global history'); }
  }
  async sendGlobal(leader, msg){
    const userB = bubble('user', msg); this.hist.appendChild(userB); this.hist.scrollTop = this.hist.scrollHeight;
    const typing = makeTypingBubble(); this.hist.appendChild(typing); this.hist.scrollTop = this.hist.scrollHeight;
    try{ const r = await fetch(`/workers/api/leader_chat_global?name=${encodeURIComponent(leader)}&message=${encodeURIComponent(msg)}`, {method:'POST'}); const js = await r.json(); try{ typing.__typingStop && typing.__typingStop(); }catch{} const body = typing.querySelector('.content'); if (!js || js.accepted === false || js.status !== 'ok'){ const m = (js && (js.message || js.status)) || t('common.error_action','Action failed'); body.textContent = `❌ ${m}`; try{ const mod = await import('./toast.js'); mod.toast(m, 'err'); }catch{} } else { body.textContent = (js.content||'').trim() || t('chat.empty_reply','(empty reply)'); } this.renderTraces(js?.tools_preview||[]); }
    catch(e){ try{ typing.__typingStop && typing.__typingStop(); }catch{} const body = typing.querySelector('.content'); body.textContent = `❌ ${t('common.error_network','Network error')}`; }
  }
}
