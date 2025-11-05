
// Minimal toast/snackbar
let holder=null; let timer=null;
export function toast(msg, kind='ok', ms=1800){
  try{
    if (!holder){ holder=document.createElement('div'); holder.style.position='fixed'; holder.style.left='50%'; holder.style.bottom='18px'; holder.style.transform='translateX(-50%)'; holder.style.zIndex='9999'; document.body.appendChild(holder); }
    const el=document.createElement('div'); el.textContent=String(msg||''); el.style.cssText='background:#111827;color:#fff;border-radius:8px;padding:8px 12px;margin-top:6px;box-shadow:0 8px 24px rgba(0,0,0,.18);font-size:13px;';
    if (kind==='err'){ el.style.background='#b91c1c'; }
    else if (kind==='warn'){ el.style.background='#f59e0b'; }
    else if (kind==='info'){ el.style.background='#2563eb'; }
    holder.appendChild(el);
    clearTimeout(timer); timer=setTimeout(()=>{ try{ el.remove(); }catch{} }, ms);
  }catch{}
}
