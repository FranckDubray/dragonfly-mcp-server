







(function(global){
  const { h, phaseDot, frPhase, firstFromSlug, resolveAsset } = window.WorkersGridCore;

  function buildCard(rec){
    const avatarUrl = resolveAsset(rec.avatar_url);
    const avatar = h('div',{class:'avatar', title:"Éditer l’identité"},[
      h('div',{class:'img',style: avatarUrl ? `background-image:url('${avatarUrl.replace(/'/g,"%27")}')` : ''}),
      h('span',{class:'state-dot '+phaseDot(rec.phase)})
    ]);
    const disp = (rec.display_name && String(rec.display_name).trim()) || firstFromSlug(rec.worker_name);
    const leaderName = (rec.leader || '').trim();
    const nameLineChildren = [];
    nameLineChildren.push(h('div',{class:'name'}, disp));
    nameLineChildren.push(h('div',{class:'status-chip', title:'Status'}, frPhase(rec.phase) || '—'));
    if (leaderName){ nameLineChildren.push(h('span',{class:'leader-badge', title:`Leader: @${leaderName}`},[ h('span',{class:'at'}, `@${leaderName}`) ])); }
    const who = h('div',{class:'who'},[
      h('div',{class:'name-line'}, nameLineChildren),
      h('div',{class:'meta-sm','data-role':'last-step'}, ''),
    ]);

    const gauge = h('div',{class:'gauge'}, [ h('div',{class:'gval'}, [ h('div',{class:'gnum'}, '0.0'), h('div',{class:'glab'}, 't/s') ]), h('div',{class:'needle'}), h('div',{class:'hub'}) ]);
    const head = h('div',{class:'card-head'},[ avatar, who, gauge ]);

    // Tools row (chips), initially empty; populated live by observe_many updates
    const toolsRow = h('div',{class:'tools'},[
      h('span',{class:'label'},'Tools')
    ]);

    const actions = h('div',{class:'card-actions'},[
      h('button',{class:'btn primary small','data-act':'process'}, `🧭 Processus`),
    ]);

    const card = h('article',{class:'card modern','data-worker':rec.worker_name, role:'article', 'aria-label':`Worker ${disp} — ${frPhase(rec.phase)}`}, [ head, toolsRow, actions ]);

    actions.addEventListener('click', async (e)=>{
      const b = e.target.closest('button[data-act]'); if (!b) return;
      const act = b.getAttribute('data-act')||''; const wn = rec.worker_name;
      if (act==='process'){
        const mod = await import('./process_modal.js');
        await mod.openProcessModal(wn); return;
      }
    });

    avatar.addEventListener('click', async (e)=>{
      e.stopPropagation();
      try{
        const r = await fetch(`/workers/api/identity?worker=${encodeURIComponent(rec.worker_name)}`);
        const js = await r.json();
        const ident = js.identity || {};
        const { openLeaderIdentityModal } = await import('./leader_identity_modal.js');
        openLeaderIdentityModal(rec.worker_name, ident, (nameSlug, identity)=>{
          try{
            const newDisp = (identity.display_name||disp);
            const nameEl = card.querySelector('.name'); if (nameEl) nameEl.textContent = newDisp;
            if (identity.avatar_url){ const av = avatar.querySelector('.img'); const url = resolveAsset(identity.avatar_url); av && (av.style.backgroundImage = `url('${url.replace(/'/g,"%27")}')`); }
          }catch{}
        });
      }catch{}
    });
    avatar.tabIndex = 0;
    avatar.addEventListener('keydown', (e)=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); avatar.click(); }});

    return card;
  }

  global.WorkersGridCard = { buildCard };
})(window);

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
