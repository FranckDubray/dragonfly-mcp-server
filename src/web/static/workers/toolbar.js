























export function createToolbar(opts){
  // Ne pas utiliser await ici: lire t via window.__i18n__ si dispo
  let tt = (k, fb) => (fb || k);
  try{
    const mod = window.__i18n__ || null;
    if (mod && typeof mod.t === 'function') tt = mod.t;
  }catch{}

  const div = document.createElement('div');
  div.className = 'graph-toolbar';
  div.setAttribute('role','toolbar');
  div.innerHTML = `
    <div class="group" aria-label="Navigation process">
      <button class="btn primary" data-act="process">${tt('toolbar.process')}</button>
      <button class="btn" data-act="current">${tt('toolbar.current')}</button>
      <button class="btn" data-act="overview">${tt('toolbar.overview')}</button>
      <span class="sep" aria-hidden="true"></span>
      <span style="margin-left:4px; color:#6b7280; font-size:12px">${tt('toolbar.display')}</span>
      <label class="btn tooltip" data-tip="${tt('toolbar.hide_start')}"><input type="checkbox" data-opt="hide_start" ${opts.hide_start?'checked':''}> ${tt('toolbar.hide_start')}</label>
      <label class="btn tooltip" data-tip="${tt('toolbar.hide_end')}"><input type="checkbox" data-opt="hide_end" ${opts.hide_end?'checked':''}> ${tt('toolbar.hide_end')}</label>
      <label class="btn tooltip" data-tip="${tt('toolbar.labels')}"><input type="checkbox" data-opt="labels" ${opts.labels?'checked':''}> ${tt('toolbar.labels')}</label>
      <label class="btn tooltip" data-tip="${tt('toolbar.follow_sg')}"><input type="checkbox" data-opt="follow_sg" ${opts.follow_sg?'checked':''}> ${tt('toolbar.follow_sg')}</label>
      <label class="btn tooltip" data-tip="${tt('toolbar.auto_center','Auto-center graph on the active node')}"><input type="checkbox" data-opt="auto_center" ${opts.auto_center?'checked':''}> ${tt('toolbar.auto_center','Auto-center')}</label>
      <span class="sep" aria-hidden="true"></span>
      <span style="margin-left:4px; color:#6b7280; font-size:12px">Zoom</span>
      <button class="btn tooltip" data-act="zoom-out" data-tip="-${tt('common.zoom','Zoom')}">-</button>
      <button class="btn tooltip" data-act="zoom-in" data-tip="+${tt('common.zoom','Zoom')}">+</button>
      <button class="btn tooltip" data-act="zoom-reset" data-tip="${tt('common.reset','Reset')}">\u27f2</button>
      <button class="btn tooltip" data-act="zoom-fit-height" data-tip="${tt('common.fit_height','Fit height')}">\u2195\ufe0e</button>
      <span class="sep" aria-hidden="true"></span>
      <span style="margin-left:4px; color:#6b7280; font-size:12px">${tt('toolbar.mode')}</span>
      <button class="btn tooltip" data-act="mode-observe" data-tip="${tt('toolbar.mode_observe')}">${tt('toolbar.mode_observe')}</button>
      <button class="btn tooltip" data-act="mode-debug-stream" data-tip="${tt('toolbar.mode_debug')}">${tt('toolbar.mode_debug')}</button>
      <button class="btn tooltip" data-act="mode-replay" data-tip="${tt('replay.title','Replay (time machine)')}">${tt('replay.title','Replay (time machine)')}</button>
      <span class="sep" aria-hidden="true"></span>
      <span style="margin-left:4px; color:#6b7280; font-size:12px">${tt('toolbar.play_speed','Speed')}</span>
      <div class="btn-group" data-role="speed">
        <button class="btn tooltip" data-speed="0.5" data-tip="x0.5">0.5×</button>
        <button class="btn tooltip" data-speed="1" data-tip="x1 (default)">1×</button>
        <button class="btn tooltip" data-speed="2" data-tip="x2">2×</button>
      </div>
    </div>
    <div class="group" aria-label="Contrôles debug">
      <button class="btn primary" data-act="start-observe">${tt('common.start_observe','Start (observe)')}</button>
      <button class="btn" data-act="start-debug">${tt('common.start_debug')}</button>
      <button class="btn" data-act="step">${tt('common.step')}</button>
      <button class="btn" data-act="cont">${tt('common.continue')}</button>
      <button class="btn" data-act="break-list">${tt('common.breakpoints')}</button>
      <button class="btn" data-act="inspect">${tt('common.inspect')}</button>
      <button class="btn danger" data-act="stop">${tt('common.stop')}</button>
    </div>`;
  return div;
}

 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
