




















// Worker Identity Modal: edit worker_identity via /workers/api/identity
import { createModal } from './modal.js';
import { t } from './i18n.js';

function resolveAsset(url){ const u=String(url||'').trim(); if(!u) return ''; if(/^https?:\/\//i.test(u)) return u; if(u.startsWith('/')) return u; return `/docs/images/${u}`; }

export function openWorkerIdentityModal(workerName, current, onSaved){
  const display = (current && current.display_name) ? String(current.display_name).trim() : '';
  const titleName = display || workerName;
  const modal = createModal({ title: `${t('worker_identity_modal.title','Edit worker identity')} ${titleName}`, width: '680px' });

  // Preview avatar
  const preview = document.createElement('div');
  preview.className = 'avatar-preview';
  const picWrap = document.createElement('div'); picWrap.className = 'pic';
  const picImg = document.createElement('img'); picImg.alt = t('worker_identity_modal.avatar_alt','Avatar'); picImg.src = resolveAsset(current?.avatar_url||'');
  picWrap.appendChild(picImg);
  const hint = document.createElement('div'); hint.className = 'hint'; hint.textContent = t('worker_identity_modal.avatar_hint','Profile picture preview');
  preview.append(picWrap, hint);

  // Form
  const form = document.createElement('form'); form.className = 'form-grid';
  form.innerHTML = `
    <label class="field">${t('worker_identity_modal.display','Display name')}<div class="hint">${t('worker_identity_modal.display_hint','Ex: Alice')}</div><input name="display_name" class="input"/></label>
    <label class="field">${t('worker_identity_modal.role','Role')}<div class="hint">${t('worker_identity_modal.role_hint','Ex: Curator')}</div><input name="role" class="input"/></label>
    <label class="field">${t('worker_identity_modal.mission','Mission')}<div class="hint">${t('worker_identity_modal.mission_hint','Short description')}</div><input name="mission" class="input"/></label>
    <label class="field">${t('worker_identity_modal.status','Status')}<div class="hint">${t('worker_identity_modal.status_hint','Ex: Idle, Active…')}</div><input name="status" class="input"/></label>
    <label class="field">${t('worker_identity_modal.spm','SPM')}<div class="hint">${t('worker_identity_modal.spm_hint','Score/min (number)')}</div><input name="spm" class="input" type="number" step="1"/></label>
    <label class="field">Leader<div class="hint">Slug du leader (ex: machin). Laisser vide pour enlever l’attache.</div><input name="leader" class="input" placeholder="machin"/></label>
  `;
  form.display_name.value = current?.display_name || '';
  form.role.value = current?.role || '';
  form.mission.value = current?.mission || '';
  form.status.value = current?.status || '';
  form.spm.value = (current?.spm!=null? String(current.spm) : '');
  form.leader.value = (current?.leader!=null? String(current.leader) : '');

  // Avatar gallery (simple)
  const galWrap = document.createElement('div'); galWrap.className = 'panel';
  const galTitle = document.createElement('h3'); galTitle.textContent = t('worker_identity_modal.choose_avatar','Choose an avatar');
  const grid = document.createElement('div'); grid.className = 'avatar-grid'; grid.setAttribute('data-role','gallery');
  galWrap.append(galTitle, grid);

  let selected = String(current?.avatar_url || '').trim();
  async function loadAvatars(){
    grid.innerHTML = '';
    try{
      const r = await fetch('/workers/api/avatars'); const js = await r.json();
      const items = Array.isArray(js.images)? js.images : [];
      items.forEach(name=>{
        const it = document.createElement('div'); it.className='avatar-item'; it.dataset.name=name; it.tabIndex=0;
        const img = document.createElement('img'); img.src = resolveAsset(name); img.alt=name; it.appendChild(img);
        if (name===selected) it.classList.add('selected');
        const choose = ()=>{ selected = name; grid.querySelectorAll('.avatar-item.selected').forEach(n=>n.classList.remove('selected')); it.classList.add('selected'); picImg.src = resolveAsset(selected); };
        it.addEventListener('click', choose);
        it.addEventListener('keydown', (e)=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); choose(); }});
        grid.appendChild(it);
      });
    }catch{ grid.textContent = t('worker_identity_modal.no_images','No images found'); }
  }

  const bSave = document.createElement('button'); bSave.className='btn primary'; bSave.textContent=t('common.save','Save');
  const bClose = document.createElement('button'); bClose.className='btn'; bClose.textContent=t('common.close','Close');
  bClose.type='button';

  bClose.addEventListener('click', () => modal.close());
  bSave.addEventListener('click', async (e)=>{
    e.preventDefault(); bSave.disabled=true; bClose.disabled=true;
    const payload = {
      display_name: form.display_name.value.trim(),
      role: form.role.value.trim(),
      mission: form.mission.value.trim(),
      status: form.status.value.trim(),
      avatar_url: selected || '',
    };
    const spmStr = form.spm.value.trim();
    if (spmStr!==''){ const n = Number(spmStr); if (!Number.isNaN(n)) payload.spm = n; }
    const leaderStr = form.leader.value.trim();
    // autoriser vider pour détacher
    payload.leader = leaderStr;

    try{
      const url = new URL('/workers/api/identity', location.origin);
      url.searchParams.set('worker', workerName);
      const res = await fetch(url.toString(), { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const js = await res.json().catch(()=>({}));
      if (!res.ok || (js && js.accepted===false)){
        alert(js?.message || t('worker_identity_modal.save_failed','Saving failed'));
      } else {
        try{ onSaved && onSaved(workerName, payload); }catch{}
        modal.close();
      }
    }catch{
      alert(t('common.error_network','Network error'));
    }finally{
      bSave.disabled=false; bClose.disabled=false;
    }
  });

  modal.body.append(preview, form, galWrap);
  modal.footer.append(bClose, bSave);
  modal.open();
  loadAvatars();
}
