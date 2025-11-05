


// Floating context menu for graph nodes (RunUntil / Break / Inspect / Open SG)
import { DebugControls } from './debug_controls.js';
import { t } from './i18n.js';

function deSanitizeId(s){
  // Best-effort: restore SG::STEP from sanitized id (where :: likely became __)
  const id = String(s||'');
  return id.includes('__') ? id.replace(/__/g,'::') : id;
}

export class NodeMenu{
  constructor(worker){ this.worker=worker; this.el=null; this._items=[]; }
  _ensure(){
    if (this.el) return this.el;
    const d = document.createElement('div');
    d.style.position='absolute'; d.style.zIndex='10'; d.style.background='#fff'; d.style.border='1px solid #e5e7eb'; d.style.borderRadius='8px'; d.style.boxShadow='0 8px 24px rgba(0,0,0,.08)'; d.style.padding='8px'; d.style.minWidth='200px'; d.style.display='none';
    d.setAttribute('role','menu');
    d.setAttribute('aria-label', t('node_menu.aria_actions','Node actions'));
    d.innerHTML = `
      <div style="font-size:12px;color:#6b7280;margin-bottom:6px"><strong data-f="id"></strong></div>
      <div style="display:flex;flex-direction:column;gap:6px">
        <button class="btn small tooltip" data-act="open_sg" data-tip="${t('node_menu.open_sg','Open subgraph')}">${t('node_menu.open_sg','Open subgraph')}</button>
        <button class="btn small tooltip" data-act="run" data-tip="${t('node_menu.run_until','Run until')}">${t('node_menu.run_until','Run until')}</button>
        <button class="btn small tooltip" data-act="break_add" data-tip="${t('node_menu.break_add','Add break')}">${t('node_menu.break_add','Add break')}</button>
        <button class="btn small tooltip" data-act="break_remove" data-tip="${t('node_menu.break_remove','Remove break')}">${t('node_menu.break_remove','Remove break')}</button>
        <button class="btn small tooltip" data-act="inspect" data-tip="${t('node_menu.inspect','Inspect')}">${t('node_menu.inspect','Inspect')}</button>
      </div>
    `;
    document.body.appendChild(d);
    this.el = d; return d;
  }
  showAt(stageEl, svg, g){
    const el = this._ensure();
    const sid = g.getAttribute('id')||''; const nodeId = deSanitizeId(sid);
    el.querySelector('[data-f="id"]').textContent = nodeId;
    // Position near node bbox relative to stage
    const bb = g.getBBox();
    const pt = svg.createSVGPoint(); pt.x = bb.x + bb.width + 6; pt.y = bb.y + 6;
    const ctm = g.getScreenCTM();
    const sp = pt.matrixTransform(ctm);
    const rect = stageEl.getBoundingClientRect();
    el.style.left = (sp.x - rect.left) + 'px';
    el.style.top = (sp.y - rect.top) + 'px';
    el.style.display='block';

    // Keyboard focus management
    const buttons = Array.from(el.querySelectorAll('button[data-act]'));
    this._items = buttons;
    buttons.forEach((b,i)=>{ b.setAttribute('role','menuitem'); b.setAttribute('tabindex', i===0 ? '0' : '-1'); });
    buttons[0]?.focus();

    const onKey = (e)=>{
      const idx = this._items.indexOf(document.activeElement);
      if (e.key==='ArrowDown'){ e.preventDefault(); const n=(idx+1)%this._items.length; this._items[n].focus(); }
      else if (e.key==='ArrowUp'){ e.preventDefault(); const n=(idx-1+this._items.length)%this._items.length; this._items[n].focus(); }
      else if (e.key==='Escape'){ e.preventDefault(); this.hide(); }
      else if (e.key==='Enter' || e.key===' '){ e.preventDefault(); document.activeElement?.click(); }
    };
    const onOutside = (e)=>{ if (!el.contains(e.target)) { this.hide(); window.removeEventListener('mousedown', onOutside, true); window.removeEventListener('keydown', onKey, true); } };
    window.addEventListener('keydown', onKey, true);
    window.addEventListener('mousedown', onOutside, true);

    el.onclick = async (e)=>{
      const b = e.target.closest('button[data-act]'); if(!b) return;
      const act = b.dataset.act;
      if (act==='open_sg') {
        const sg = (nodeId.includes('::') ? nodeId.split('::',1)[0] : '');
        if (sg) window.dispatchEvent(new CustomEvent('workers:openSubgraph', {detail:{ subgraph: sg }}));
      }
      if (act==='run') await DebugControls.runUntil(this.worker, nodeId,'always');
      if (act==='break_add') await DebugControls.breakAdd(this.worker, nodeId,'always');
      if (act==='break_remove') await DebugControls.breakRemove(this.worker, nodeId,'always');
      if (act==='inspect') await DebugControls.inspect(this.worker);
      this.hide();
    };
  }
  hide(){ if (this.el){ this.el.style.display='none'; } }
}
