


import { copyText } from './utils.js';
import { t } from './i18n.js';

export class IOPanel{
  constructor(root){
    this.box = document.createElement('div');
    this.box.className = 'panel';

    this.title = document.createElement('h3');
    this.title.textContent = t('io.title');

    // Actions toolbar
    this.actions = document.createElement('div');
    this.actions.style.cssText = 'display:flex; gap:8px; flex-wrap:wrap; align-items:center;';
    this.bCopyIn = mkBtn(t('common.copy_in'), t('common.copy_in'));
    this.bCopyOut = mkBtn(t('common.copy_out'), t('common.copy_out'));
    this.bCopyErr = mkBtn(t('common.copy_err'), t('common.copy_err'));
    this.actions.append(this.bCopyIn, this.bCopyOut, this.bCopyErr);

    // Pre blocks
    this.in = document.createElement('pre'); this.in.className = 'io-pre';
    this.out = document.createElement('pre'); this.out.className = 'io-pre';
    this.err = document.createElement('pre'); this.err.className = 'io-pre'; this.err.style.display='none';

    this.box.append(this.title, this.actions, this.in, this.out, this.err);
    root.appendChild(this.box);

    // Copy handlers
    this.bCopyIn.addEventListener('click', async ()=>{
      try{ await copyText(this._lastInText || ''); }catch{}
    });
    this.bCopyOut.addEventListener('click', async ()=>{
      try{ await copyText(this._lastOutText || ''); }catch{}
    });
    this.bCopyErr.addEventListener('click', async ()=>{
      try{ await copyText(this._lastErrText || ''); }catch{}
    });
  }
  update(evt){
    const call = evt?.io?.in || {};
    const outp = (evt?.io?.out_preview ?? '');
    const errm = (evt?.error?.message || '').trim();

    const inText = safe(call);
    const outText = String(outp);
    const errText = String(errm);
    this._lastInText = inText; this._lastOutText = outText; this._lastErrText = errText;

    this.in.textContent = t('io.in')+':\n' + inText;
    this.out.textContent = t('io.out')+':\n' + outText;

    if (errm){
      this.err.style.display='block'; this.err.textContent = t('io.error')+':\n' + errText;
      this.bCopyErr.style.display = '';
    } else {
      this.err.style.display='none'; this.err.textContent = '';
      this.bCopyErr.style.display = 'none';
    }
  }
}
function safe(o){ try{ return JSON.stringify(o, null, 2); }catch{ return String(o); } }
function mkBtn(label, tip){
  const b = document.createElement('button');
  b.className = 'btn tooltip';
  b.textContent = label;
  if (tip) b.setAttribute('data-tip', tip);
  return b;
}
