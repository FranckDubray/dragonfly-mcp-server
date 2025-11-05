




















import { h } from './dom.js';
import { createModal } from './modal.js';
import { t } from './i18n.js';

function resolveAsset(url){ const u=String(url||'').trim(); if(!u) return ''; if(/^https?:\/\//i.test(u)) return u; if(u.startsWith('/')) return u; return `/docs/images/${u}`; }

export function openLeaderIdentityModal(leaderName, current, onSaved, opts={}){
  const mode = String(opts.mode||'edit'); // 'edit' | 'create'
  const modal = createModal({ title: mode==='create' ? t('leader_identity_modal.create_title','Create leader') : `${t('leader_identity_modal.edit_title','Edit leader identity')} @${leaderName}`, width: '680px' });

  // Preview avatar
  const preview = h('div',{class:'avatar-preview'},[
    h('div',{class:'pic'}, h('img',{src: resolveAsset(current?.avatar_url||''), alt:t('leader_identity_modal.avatar_alt','Avatar')})),
    h('div',{class:'hint'}, mode==='create' ? t('leader_identity_modal.pick_below','Choose an image below') : t('leader_identity_modal.avatar_hint','Profile picture preview'))
  ]);

  // Form
  const form = h('form',{class:'form-grid'});
  const formId = 'leader_edit_'+Math.random().toString(36).slice(2);
  form.id = formId;

  let slugBlock = '';
  if (mode==='create'){
    slugBlock = `<label class="field">${t('leader_identity_modal.slug','Identifier (slug)')}<div class="hint">${t('leader_identity_modal.slug_hint','Ex: rolland')}</div><input name="slug" class="input" required/></label>`;
  }

  // Removed the Role field entirely (role is always "Leader")
  form.innerHTML = `
    ${slugBlock}
    <label class="field">${t('leader_identity_modal.display','Display name')}<div class="hint">${t('leader_identity_modal.display_hint','Ex: Rolland')}</div><input name="display_name" class="input"/></label>
    <label class="field">${t('leader_identity_modal.persona','Persona')}<div class="hint">${t('leader_identity_modal.persona_hint','Ex: Orchestrator of workers')}</div><input name="persona" class="input"/></label>
    <label class="field">${t('leader_identity_modal.prompt','Prompt')}<div class="hint">${t('leader_identity_modal.prompt_hint','Leader context (stored in DB)')}</div><textarea name="prompt" class="input" rows="6"></textarea></label>
  `;

  // Avatar gallery
  const galWrap = h('div',{class:'panel'});
  const galTitle = h('h3',{},t('leader_identity_modal.choose_avatar','Choose an avatar'));
  const grid = h('div',{class:'avatar-grid','data-role':'gallery'});
  galWrap.append(galTitle, grid);

  // Pre-fill
  form.display_name.value = current?.display_name || '';
  form.persona.value = current?.persona || t('leader_identity_modal.persona_default','Orchestrator of workers');
  form.prompt.value = current?.prompt || '';

  const picImg = preview.querySelector('.pic img');
  const selected = { name: (current?.avatar_url||'').trim() };
  if (selected.name){ picImg.src = resolveAsset(selected.name); }

  async function loadAvatars(){
    try{
      const r = await fetch('/workers/api/avatars');
      const js = await r.json();
      const items = Array.isArray(js.images) ? js.images : [];
      grid.innerHTML='';
      items.forEach(name=>{
        const it = h('div',{class:'avatar-item','data-name':name, title:name});
        const img = h('img',{src: resolveAsset(name), alt:name});
        it.append(img);
        if (name === selected.name) it.classList.add('selected');
        const choose = ()=>{
          selected.name = name;
          grid.querySelectorAll('.avatar-item.selected').forEach(n=>n.classList.remove('selected'));
          it.classList.add('selected');
          picImg.src = resolveAsset(selected.name);
        };
        it.addEventListener('click', choose);
        it.addEventListener('keydown', (e)=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); choose(); }});
        grid.appendChild(it);
      });
    }catch{
      grid.textContent = t('leader_identity_modal.no_images','No images found');
    }
  }

  // Actions
  const bSave = h('button',{class:'btn primary', type:'submit'}, mode==='create' ? t('leader_identity_modal.create','Create') : t('leader_identity_modal.save','Save'));
  const bClose = h('button',{class:'btn', type:'button'},t('common.close','Close'));
  bSave.setAttribute('form', formId);

  bClose.addEventListener('click', () => modal.close());
  form.addEventListener('submit', async (e)=>{
    e.preventDefault(); bSave.disabled=true; bClose.disabled=true;
    const payload = {
      display_name: form.display_name.value.trim(),
      persona: form.persona.value.trim(),
      avatar_url: selected.name || '',
      prompt: form.prompt.value
    };
    const targetName = (mode==='create') ? (form.slug.value||'').trim() : leaderName;
    if (!targetName){
      try{ const {toast} = await import('./toast.js'); toast(t('leader_identity_modal.slug_required','Identifier required'),'err'); }catch{}
      bSave.disabled=false; bClose.disabled=false; return;
    }

    // Prevent overwrite existing leader on create
    if (mode==='create'){
      try{
        const lr = await fetch('/workers/api/leaders');
        const lj = await lr.json();
        const exists = Array.isArray(lj.leaders) && lj.leaders.some(x => String(x?.name||'').trim() === targetName);
        if (exists){
          try{ const {toast} = await import('./toast.js'); toast(t('leader_identity_modal.slug_exists','Identifier already used. Choose another.'),'err'); }catch{}
          bSave.disabled=false; bClose.disabled=false; return;
        }
      }catch{}
    }

    try{
      const r = await fetch(`/workers/api/leader_identity?name=${encodeURIComponent(targetName)}`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const js = await r.json().catch(()=>({}));
      if (!r.ok || (js && js.accepted===false)){
        try{ const {toast} = await import('./toast.js'); toast(js?.message || t('leader_identity_modal.save_failed','Saving failed'),'err'); }catch{}
      } else {
        try{ const {toast} = await import('./toast.js'); toast(mode==='create'?t('leader_identity_modal.created','Leader created'):t('leader_identity_modal.updated','Identity updated')); }catch{}
        try{ onSaved && onSaved(js?.leader || targetName, payload); }catch{}
        try{ window.dispatchEvent(new CustomEvent('leader:identityUpdated', {detail:{ name: js?.leader || targetName, identity: payload }})); }catch{}
        try{
          const newSlug = js?.leader || targetName;
          sessionStorage.setItem('workers_ui_leader', newSlug);
          if (mode==='create' || (newSlug && newSlug !== (leaderName||''))){
            setTimeout(()=>{ try{ location.reload(); }catch{} }, 60);
          }
        }catch{}
        modal.close();
      }
    }catch{
      try{ const {toast} = await import('./toast.js'); toast(t('common.error_network','Network error'),'err'); }catch{}
    }finally{
      bSave.disabled=false; bClose.disabled=false;
    }
  });

  modal.body.append(preview, form, galWrap);
  modal.footer.append(bClose, bSave);
  modal.open();
  loadAvatars();
}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
