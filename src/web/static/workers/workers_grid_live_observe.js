





(function(global){
  const Core = global.WorkersGridCore || {};
  const LiveCore = global.WorkersGridLiveCore || {};

  function dbg(){ try{ if (global.__WG_DEBUG) console.log('[WG][observe]', ...arguments); }catch{} }

  function updateGauges(card, ev, helpers){
    const g = card.querySelector('.gauge');
    const gnum = card.querySelector('.gnum');
    const glab = card.querySelector('.glab');
    const needle = card.querySelector('.needle');

    let ringColor = '#10b981'; let ringRatio = 0; let centerVal = '0.0'; let centerUnit = 't/s';
    const p = String(ev.phase||'').toLowerCase();
    const rk = String(ev.running_kind||'');
    const rstarted = ev.running_started_at || '';

    if (p==='failed'){ ringColor = '#ef4444'; ringRatio=1; centerVal='ERR'; centerUnit=''; }
    else if (rk==='tool'){
      ringColor = '#8b5cf6';
      const prog = helpers && typeof helpers.getToolProgress==='function' ? helpers.getToolProgress(rstarted, 600) : {ratio:0, percent:0};
      ringRatio = prog.ratio; centerVal = String(prog.percent); centerUnit='%';
      if (g){ if (prog.percent>=100) g.classList.add('pulse'); else g.classList.remove('pulse'); }
    }
    else if (p==='running' || p==='starting'){
      const ar = helpers && typeof helpers.getAdaptiveRate==='function' ? helpers.getAdaptiveRate(ev.worker_name) : {value:0, unit:'t/s', ratio:0};
      ringColor = (ar.value>0 ? '#f59e0b' : '#10b981');
      ringRatio = Math.max(0, Math.min(1, ar.ratio));
      centerVal = String((ar.value||0).toFixed(1));
      centerUnit = ar.unit || 't/s';
    }
    if (g){ g.style.setProperty('--p', String(ringRatio)); g.style.setProperty('--g', ringColor); }
    if (gnum){ gnum.textContent = centerVal; }
    if (glab){ glab.textContent = centerUnit; }
    if (needle){ const angle = -90 + (ringRatio * 180); needle.style.transform = `translate(-50%, -100%) rotate(${angle}deg)`; needle.style.backgroundColor = ringColor; }
  }

  async function applyEvent(card, wn, ev, helpers){
    const dot = card.querySelector('.state-dot');
    const chip = card.querySelector('.status-chip');
    const lastLine = card.querySelector('[data-role="last-step"]');

    const p = String(ev.phase||'').toLowerCase();
    if (dot){ dot.classList.remove('dot-running','dot-idle','dot-error'); dot.classList.add(p==='failed'?'dot-error':(p.match(/running|starting/)?'dot-running':'dot-idle')); }
    if (chip){ chip.textContent = Core.frPhase(p); }

    const iso = String(ev.last_step_at||'');
    if (lastLine){ lastLine.textContent = iso ? `Dernier step: ${Core.formatLocalTs(iso)}` : ''; }

    updateGauges(card, {...ev, worker_name: wn}, helpers);

    try{
      const ar2 = helpers && typeof helpers.getAdaptiveRate==='function' ? helpers.getAdaptiveRate(wn) : {value:0, unit:'t/s', ratio:0};
      const perSec = ar2.unit==='t/s' ? ar2.value : (ar2.unit==='t/10s' ? ar2.value/10 : (ar2.unit==='t/min' ? ar2.value/60 : 0));
      const sleeping = (p==='running' && String(ev.running_kind||'')!=='tool' && perSec===0);
      Core.setAvatarAura(card, { phase:p, running_kind:String(ev.running_kind||''), sleeping });
    }catch{}

    // Tools chips live (use label+tooltip from /tools, with fallback). No hard pre-filter.
    try{
      let toolsRow = card.querySelector('.tools');
      if (!toolsRow){
        toolsRow = document.createElement('div');
        toolsRow.className = 'tools';
        const lab = document.createElement('span'); lab.className = 'label'; lab.textContent = 'Tools'; toolsRow.appendChild(lab);
        const actionsNode = card.querySelector('.card-actions');
        if (actionsNode) card.insertBefore(toolsRow, actionsNode); else card.appendChild(toolsRow);
        dbg('created toolsRow for', wn);
      }
      toolsRow.querySelectorAll('.tool.running').forEach(el => el.classList.remove('running'));
      const rk = String(ev.running_kind||'');
      const rstarted = ev.running_started_at || '';

      const call = ev?.last_io_call || {};
      let rawName = String(call.tool || call.tool_name || '').trim();
      if (!rawName){
        const op = String(call.operation || '').trim();
        if (op) rawName = `${call.tool || 'py_orchestrator'}:${op}`;
      }

      if (rk==='tool' && rawName){
        // Diagnostic: prefilter info
        try{ if (LiveCore.isToolName) dbg('prefilter isToolName', rawName, '=>', LiveCore.isToolName(rawName)); }catch{}

        let chipEl = toolsRow.querySelector(`.tool[data-tool="${CSS.escape(rawName)}"]`);
        if (!chipEl){
          chipEl = document.createElement('div');
          chipEl.className='tool tooltip';
          chipEl.setAttribute('data-tool', rawName);
          toolsRow.appendChild(chipEl);
          dbg('created chip for', wn, rawName);
        }
        try{
          if (LiveCore.resolveToolLabel){
            const { text, tip, kind } = await LiveCore.resolveToolLabel(rawName);
            dbg('resolved label', rawName, '=>', {text, kind});
            if (kind && kind !== 'tool'){ chipEl.remove(); dbg('removed non-tool chip', rawName, kind); return; }
            chipEl.textContent = text || rawName;
            if (tip) chipEl.setAttribute('data-tip', tip); else chipEl.removeAttribute('data-tip');
          } else {
            chipEl.textContent = rawName;
          }
        }catch{ chipEl.textContent = rawName; }
        chipEl.classList.add('running');
        let chrono = chipEl.querySelector('.chrono'); if (!chrono){ chrono = document.createElement('span'); chrono.className='chrono'; chipEl.appendChild(chrono); }
        const started = Date.parse(rstarted || '');
        if (Number.isFinite(started)){
          const elapsed = Math.max(0, Math.floor((Date.now() - started)/1000));
          const mm = Math.floor(elapsed/60), ss = String(elapsed%60).padStart(2,'0');
          chrono.textContent = `${mm}:${ss}`;
          card.dataset.toolStarted = rstarted || '';
          LiveCore.ensureChronoTick && LiveCore.ensureChronoTick();
          dbg('running tool', wn, rawName, 'started', rstarted);
        } else {
          chrono.textContent = '';
          delete card.dataset.toolStarted;
          dbg('running tool without valid started_at', wn, rawName, rstarted);
        }
      } else {
        if (card.dataset.toolStarted) dbg('clear toolStarted for', wn);
        delete card.dataset.toolStarted;
        toolsRow.querySelectorAll('.tool .chrono').forEach(c => c.textContent='');
      }
    }catch(e){ dbg('tools chips error', e); }
  }

  global.WorkersGridLiveObserve = { applyEvent };
})(window);

 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
