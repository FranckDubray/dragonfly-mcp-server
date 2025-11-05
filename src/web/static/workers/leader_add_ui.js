
import { h } from './dom.js';
import { toast } from './toast.js';
import { createModal } from './modal.js';

export async function openAddLeaderModal(){
  const modal = createModal({ title: 'Créer un leader', width: '560px' });
  const status = h('div',{class:'help-text','aria-live':'polite'});

  const form = h('form',{class:'form-grid'});
  const fieldName = h('input',{ type:'text', placeholder:'Identifiant (slug, ex: rolland)', 'aria-label':'Identifiant leader', class:'input' });
  const fieldDisplay = h('input',{ type:'text', placeholder:"Nom d'affichage (ex: Rolland)", 'aria-label':"Nom d'affichage", class:'input' });
  const fieldRole = h('input',{ type:'text', placeholder:'Rôle (ex: Leader)', 'aria-label':'Rôle', class:'input' });
  const fieldPersona = h('input',{ type:'text', placeholder:'Persona (ex: Orchestrateur des workers)', 'aria-label':'Persona', class:'input' });
  const fieldAvatar = h('select',{ 'aria-label':'Avatar (docs/images)', class:'input' });

  const actions = h('div', {class:'form-actions'});
  const bCreate = h('button',{class:'btn primary', type:'submit'},'Créer');
  const bClose = h('button',{class:'btn ghost', type:'button'},'Fermer');
  actions.append(bClose, bCreate);

  form.append(
    h('label',{},['Identifiant', fieldName]),
    h('label',{},["Nom d'affichage", fieldDisplay]),
    h('label',{},['Rôle', fieldRole]),
    h('label',{},['Persona', fieldPersona]),
    h('label',{},['Avatar', fieldAvatar]),
    actions
  );

  modal.body.append(status, form);

  async function loadAvatars(){
    try{ const r = await fetch('/workers/api/avatars'); const js = await r.json(); const items=(js.images||[]); fieldAvatar.innerHTML=''; const def=document.createElement('option'); def.value=''; def.textContent='(aucun)'; fieldAvatar.appendChild(def); items.forEach(n=>{ const o=document.createElement('option'); o.value=n; o.textContent=n; fieldAvatar.appendChild(o); }); }
    catch{ /* ignore */ }
  }

  bClose.addEventListener('click',()=>{ modal.close(); });
  form.addEventListener('submit', async (e)=>{
    e.preventDefault(); status.textContent='';
    const name=(fieldName.value||'').trim(); const display=(fieldDisplay.value||'').trim();
    const role=(fieldRole.value||'').trim()||'Leader'; const persona=(fieldPersona.value||'').trim()||'Orchestrateur des workers';
    const avatar=(fieldAvatar.value||'').trim();
    if(!name||!display){ status.className='error-text'; status.textContent='Identifiant et nom affiché requis'; return; }
    bCreate.classList.add('loading'); bCreate.disabled=true; bClose.disabled=true;
    try{
      const url = new URL('/workers/api/leader_identity', location.origin); url.searchParams.set('name', name);
      const res = await fetch(url.toString(), {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({display_name:display, role, persona, avatar_url:avatar})});
      const js = await res.json();
      if (!res.ok || (js && js.accepted===false)){
        status.className='error-text'; status.textContent = js?.message||'Création échouée'; return;
      }
      toast('Leader créé');
      modal.close();
      location.reload();
    }catch{ status.className='error-text'; status.textContent='Création échouée'; }
    finally{ bCreate.classList.remove('loading'); bCreate.disabled=false; bClose.disabled=false; }
  });

  modal.open();
  await loadAvatars();
}
