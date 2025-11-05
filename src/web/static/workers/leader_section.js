















import { h } from './dom.js';
import { openLeaderIdentityModal } from './leader_identity_modal.js';

function resolveAsset(url){ const u=String(url||'').trim(); if(!u) return ''; if(/^https?:\/\//i.test(u)) return u; if(u.startsWith('/')) return u; return `/docs/images/${u}`; }

export function buildLeaderSection(leader, onOpen){
  const section = h('section',{class:'leader','aria-label':'Leader'});
  const avatarUrl = resolveAsset(leader.avatar_url);
  const avatar = h('div',{class:'avatar aura a--stop-ok', title:'Éditer l’identité (cliquer)'}, avatarUrl ? [ h('img',{src: avatarUrl, alt:`Photo de ${leader.display_name||'Leader'}`}) ] : []);
  avatar.style.cursor = 'pointer';
  avatar.tabIndex = 0;
  avatar.addEventListener('click', async ()=>{
    const name = String(leader.name||'').trim(); if (!name) return;
    let current = {};
    try{ const r = await fetch(`/workers/api/leader_identity?name=${encodeURIComponent(name)}`); const js = await r.json(); current = js?.identity || {}; }catch{}
    openLeaderIdentityModal(name, current, (newSlug, identity)=>{
      // refresh the leader card in place
      try{
        section.querySelector('.title').textContent = identity.display_name || leader.display_name || name;
        const av = section.querySelector('.avatar img'); if (av) av.src = resolveAsset(identity.avatar_url||leader.avatar_url||'');
      }catch{}
      // if slug changed, update leader.name so next edits point to the right DB
      leader.name = newSlug || leader.name;
    });
  });
  avatar.addEventListener('keydown', (e)=>{ if(e.key==='Enter' || e.key===' '){ e.preventDefault(); avatar.click(); }});

  const info = h('div',{class:'info'},[
    h('div',{class:'title'}, `${leader.display_name||'Leader'}`),
    leader.persona ? h('div',{class:'sub'}, leader.persona) : null,
  ].filter(Boolean));
  const btn = h('a',{class:'btn', href:'#','aria-label':'Chat leader'}, ['Chat']);
  btn.addEventListener('click', (e)=>{ e.preventDefault(); onOpen && onOpen(); });
  section.append(avatar, info, btn);
  return section;
}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
