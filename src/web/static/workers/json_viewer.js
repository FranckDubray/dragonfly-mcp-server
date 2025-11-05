

















// Lightweight on-demand JSON viewer wrapper with robust fallbacks
// Order: global UMD -> ESM via esm.sh -> inject UMD script (jsDelivr) -> unpkg UMD
let JSONFormatterMod = null;

function hasGlobal(){ try{ return typeof window !== 'undefined' && window.JSONFormatter; }catch{ return false; } }

function loadScript(src){
  return new Promise((resolve, reject)=>{
    try{
      const s = document.createElement('script');
      s.src = src; s.async = true; s.onload = ()=>resolve(); s.onerror = (e)=>reject(e);
      document.head.appendChild(s);
    }catch(e){ reject(e); }
  });
}

export async function ensureJsonFormatter(){
  if (JSONFormatterMod) return true;

  // 1) Global UMD already present
  if (hasGlobal()){
    JSONFormatterMod = window.JSONFormatter;
    return true;
  }

  // 2) ESM via esm.sh (auto-wrap UMD/CJS to ESM)
  try{
    const mod = await import('https://esm.sh/json-formatter-js@2.5.1');
    JSONFormatterMod = (mod && (mod.default || mod)) || null;
    if (JSONFormatterMod) return true;
  }catch{}

  // 3) Inject UMD script from jsDelivr, then unpkg fallback
  const candidates = [
    'https://cdn.jsdelivr.net/npm/json-formatter-js@2.5.1/dist/json-formatter.min.js',
    'https://unpkg.com/json-formatter-js@2.5.1/dist/json-formatter.min.js'
  ];
  for (const url of candidates){
    try{
      await loadScript(url);
      if (hasGlobal()){
        JSONFormatterMod = window.JSONFormatter;
        return true;
      }
    }catch{}
  }

  console.warn('[JSON_VIEWER] json-formatter not available, falling back to plain JSON');
  return false;
}

function prettyString(value){
  try{
    if (value && typeof value === 'object') return JSON.stringify(value, null, 2);
    if (typeof value === 'string'){
      try{ const obj = JSON.parse(value); return JSON.stringify(obj, null, 2); }catch{ return value; }
    }
    return String(value ?? '');
  }catch{ return String(value ?? ''); }
}

function truncateText(text, {maxLines=24, maxChars=4000}={}){
  const t = String(text||'');
  if (!t) return { text:'—', truncated:false, full:'' };
  if (t.length <= maxChars){
    const lines = t.split('\n');
    if (lines.length <= maxLines) return { text:t, truncated:false, full:'' };
  }
  // Truncate by lines then chars as fallback
  let out = t.split('\n').slice(0, maxLines).join('\n');
  if (out.length > maxChars) out = out.slice(0, maxChars);
  return { text: out + '\n…', truncated:true, full: t };
}

function typeInfo(val){
  const v = val;
  const t = (v===null) ? 'null' : Array.isArray(v) ? 'array' : typeof v;
  if (t==='array') return { kind:'Array', extra: `(${v.length})` };
  if (t==='object') return { kind:'Object', extra: `(${Object.keys(v||{}).length} keys)` };
  if (t==='string') return { kind:'String', extra: v.length>0? `(${v.length})`:'' };
  if (t==='number') return { kind:'Number', extra:'' };
  if (t==='boolean') return { kind:'Boolean', extra:'' };
  if (t==='null') return { kind:'Null', extra:'' };
  return { kind: t, extra:'' };
}

function mkToolbar(){
  const bar = document.createElement('div');
  bar.className = 'jsonv-toolbar';
  const left = document.createElement('div'); left.className='left';
  const right = document.createElement('div'); right.className='right';
  bar.append(left, right);
  return { bar, left, right };
}

function mkBtn(label, title){ const b=document.createElement('button'); b.className='btn small'; b.textContent=label; if(title) b.title=title; return b; }

// Render a human-friendly JSON block
export function renderJson(container, value, fallbackText, opts={}){
  const useTree = !!JSONFormatterMod;
  const val = (typeof value==='string') ? ((()=>{ try{ return JSON.parse(value); }catch{ return value; } })()) : value;
  const { kind, extra } = typeInfo(val);

  container.innerHTML = '';
  const wrap = document.createElement('div'); wrap.className='jsonv';

  // Header
  const header = document.createElement('div'); header.className='jsonv-head';
  const badge = document.createElement('span'); badge.className='badge'; badge.textContent = [kind, extra].filter(Boolean).join(' ');
  header.appendChild(badge);

  // Toolbar
  const { bar, right } = mkToolbar();
  const bCopy = mkBtn('Copier','Copier le contenu');
  bar.classList.add('jsonv-tools');
  right.append(bCopy);
  header.appendChild(bar);

  // Body
  const body = document.createElement('div'); body.className='jsonv-body';

  if (useTree && (typeof val==='object' && val!==null)){
    // Tree viewer
    let openDepth = 2;
    const host = document.createElement('div'); host.className='jsonv-tree';
    const renderTree = ()=>{
      host.innerHTML='';
      try{
        const fmt = new JSONFormatterMod(val, openDepth, { hoverPreviewEnabled: true });
        host.appendChild(fmt.render());
      }catch(e){
        // fallback to pre
        const pre = document.createElement('pre'); pre.className='io-pre'; pre.textContent = prettyString(val);
        pre.style.background='#fff'; pre.style.color='#111827'; pre.style.border='1px solid var(--border)'; pre.style.borderRadius='8px'; pre.style.fontSize='12px'; pre.style.lineHeight='1.35'; pre.style.maxHeight='34vh'; pre.style.overflow='auto'; pre.style.margin='0';
        host.appendChild(pre);
      }
    };
    renderTree();

    // Expand/Collapse controls
    const bExpand = mkBtn('Déployer','Déployer tout');
    const bCollapse = mkBtn('Replier','Replier tout');
    bar.querySelector('.left')?.append(bExpand, bCollapse);
    bExpand.onclick = ()=>{ openDepth = 10; renderTree(); };
    bCollapse.onclick = ()=>{ openDepth = 0; renderTree(); };

    body.appendChild(host);

    // Copy: copy the compact JSON (pretty)
    bCopy.onclick = async ()=>{ try{ await navigator.clipboard.writeText(JSON.stringify(val, null, 2)); }catch{} };
  } else {
    // Plain text / string or no library
    const pretty = prettyString(val ?? fallbackText ?? '—');
    const { text, truncated, full } = truncateText(pretty, { maxLines: 34, maxChars: 10000 });
    const pre = document.createElement('pre'); pre.className='io-pre'; pre.textContent = text;
    pre.style.background='#fff'; pre.style.color='#111827'; pre.style.border='1px solid var(--border)'; pre.style.borderRadius='8px'; pre.style.fontSize='12px'; pre.style.lineHeight='1.35'; pre.style.maxHeight='34vh'; pre.style.overflow='auto'; pre.style.margin='0';
    body.appendChild(pre);

    if (truncated){
      const row = document.createElement('div'); row.style.cssText='display:flex; gap:8px; justify-content:flex-end; margin-top:6px;';
      const more = mkBtn('Afficher tout','Afficher le texte complet');
      more.onclick = ()=>{ pre.textContent = full; more.remove(); };
      row.appendChild(more);
      body.appendChild(row);
    }

    bCopy.onclick = async ()=>{ try{ await navigator.clipboard.writeText(pretty); }catch{} };
  }

  wrap.append(header, body);
  container.appendChild(wrap);
}
