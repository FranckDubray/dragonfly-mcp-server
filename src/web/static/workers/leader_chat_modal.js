





















import { h } from './dom.js';
import { renderMarkdownSafe } from './sanitize_markdown.js';
import { createModal } from './modal.js';

function fmtTime(d){ try{ const t=(d instanceof Date)?d:new Date(d); const p=n=>String(n).padStart(2,'0'); return `${p(t.getHours())}:${p(t.getMinutes())}:${p(t.getSeconds())}`; }catch{ return ''; } }
const storeKey = (leader)=> `leader_chat_history:${leader||''}`;

function bubble(role, content, toolsCalls, ts){
  const root = h('div',{class:`chat-bubble ${role==='user'?'user':'assistant'}`, tabindex:'0'});
  const who = h('div',{class:'who'}, [ role==='user'?'Vous':'LLM', h('span',{class:'time'}, fmtTime(ts||new Date())) ]);
  root.append(who);
  const body = h('div',{class:'content markdown'});
  body.innerHTML = renderMarkdownSafe(content||'');
  root.append(body);
  if (Array.isArray(toolsCalls) && toolsCalls.length){
    const ul = document.createElement('ul'); ul.className='tools-calls';
    toolsCalls.forEach(tc=>{
      const li = document.createElement('li');
      li.innerHTML = `<div class="t-head"><span class="t-name">${String(tc.name||'tool')}</span><span class="t-badge">${String(tc.status||'ok')}</span></div><div class="t-args">${JSON.stringify(tc.args||{}, null, 2)}</div>`;
      ul.appendChild(li);
    });
    root.append(ul);
  }
  return root;
}

export function buildChatModal(opts={}){
  const modal = createModal({ title: String(opts.title||'').trim() || 'Chat', width: '860px' });
  modal.panel.classList.add('chat-fixed');

  const list = h('div',{class:'chat-list', role:'log','aria-live':'polite'});

  function makeTypingBubble(){
    const root = bubble('assistant', '…');
    const body = root.querySelector('.content');
    let dots = 1; let alive = true;
    const timer = setInterval(()=>{ if(!alive) return; dots = (dots%3)+1; body.innerHTML = renderMarkdownSafe('.'.repeat(dots)); }, 450);
    root.__typingStop = ()=>{ alive=false; clearInterval(timer); };
    return root;
  }
  function scrollBottom(){ try{ list.scrollTop = list.scrollHeight; }catch{} }

  const tools = document.createElement('div'); tools.className='cfg-tools';
  const bReset = document.createElement('button'); bReset.className='btn small'; bReset.textContent='Reset conversation';
  tools.appendChild(bReset);

  const form = h('div',{class:'chat-form'});
  const input = h('textarea',{rows:'2','aria-label':'Message',placeholder:'Écrire un message... (Entrée pour envoyer, Shift+Entrée pour retour)'});
  const send = h('button',{class:'btn primary'},'Envoyer');
  form.append(input, send);

  modal.body.append(list, tools, form);

  let leaderSlug = '';

  function setLeader(slug){
    leaderSlug = String(slug||'').trim();
    refresh(); // recharger l'historique pour ce leader
  }

  async function refresh(){
    try{
      list.innerHTML='';
      const raw = sessionStorage.getItem(storeKey(leaderSlug));
      const arr = raw? JSON.parse(raw) : [];
      if (Array.isArray(arr)){
        arr.forEach(m=>{ list.appendChild(bubble(m.role||'assistant', m.content||'', [], m.ts||new Date())); });
        scrollBottom();
      }
    }catch{}
  }

  function persistMessage(role, content){
    try{
      const key = storeKey(leaderSlug);
      const raw = sessionStorage.getItem(key);
      const arr = raw? JSON.parse(raw) : [];
      arr.push({role, content, ts: new Date().toISOString()});
      sessionStorage.setItem(key, JSON.stringify(arr.slice(-100)));
    }catch{}
  }

  async function sendMsg(postFn){
    const msg = (input.value||'').trim(); if (!msg) return;
    const tsUser = new Date();
    const userB = bubble('user', msg, [], tsUser);
    list.appendChild(userB); scrollBottom();
    persistMessage('user', msg);
    input.value=''; input.focus();

    const typing = makeTypingBubble();
    list.appendChild(typing); scrollBottom();

    send.disabled = true;
    try{
      const js = await postFn(msg);
      try{ typing.__typingStop && typing.__typingStop(); }catch{}
      const body = typing.querySelector('.content');
      const timeEl = typing.querySelector('.who .time'); if (timeEl) timeEl.textContent = fmtTime(new Date());
      if (!js || js.accepted === false || js.status !== 'ok'){
        const m = (js && (js.message || js.status)) || 'LLM/serveur indisponible';
        body.innerHTML = renderMarkdownSafe(`❌ ${m}`);
      } else {
        const content = (js.content||'').trim() || '(réponse vide)';
        body.innerHTML = renderMarkdownSafe(content);
        persistMessage('assistant', content);
      }
      scrollBottom();
    }
    catch(e){
      try{ typing.__typingStop && typing.__typingStop(); }catch{}
      const body = typing.querySelector('.content');
      const timeEl = typing.querySelector('.who .time'); if (timeEl) timeEl.textContent = fmtTime(new Date());
      body.innerHTML = renderMarkdownSafe('❌ Erreur réseau');
      scrollBottom();
    }
    finally{ send.disabled = false; input.focus(); }
  }

  list.addEventListener('click', async (e)=>{
    const btn = e.target.closest('button.copy-btn'); if (!btn) return;
    const pre = btn.closest('.code-toolbar')?.querySelector('pre code');
    if (!pre) return;
    try{ await navigator.clipboard.writeText(pre.innerText || pre.textContent || ''); btn.textContent='Copié'; setTimeout(()=>btn.textContent='Copier', 1200); }catch{}
  });

  input.addEventListener('keydown',(e)=>{ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); send.click(); }});

  bReset.addEventListener('click', ()=>{
    try{ sessionStorage.removeItem(storeKey(leaderSlug)); list.innerHTML=''; }catch{}
  });

  return {
    overlay: modal.overlay, panel: modal.panel, list, input, send,
    open: modal.open, closeModal: modal.close,
    setTitle: (t)=>{ try{ modal.setTitle(t); }catch{} },
    refresh,
    setLeader,
    attach: (postFn)=>{ send.onclick = ()=> sendMsg(postFn); },
  };
}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 