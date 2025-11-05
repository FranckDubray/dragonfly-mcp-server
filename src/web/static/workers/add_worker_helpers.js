
// Helpers and read-only config renderer for Add Worker modal (split)

export function slugify(s){ return String(s||'').toLowerCase().replace(/[^a-z0-9_]+/g,'_').replace(/^_+|_+$/g,''); }
const isScalar = (v)=> (v===null) || ['string','number','boolean'].includes(typeof v);
const isPlainObject = (v)=> v && typeof v==='object' && !Array.isArray(v);
const isMapOfScalars = (o)=> isPlainObject(o) && Object.values(o).every(isScalar);

// Shorten very long keys (e.g., URLs) for display, keep full key in title
export function shortenKey(k){
  try{
    const s = String(k||'').trim();
    if (/^https?:\/\//i.test(s)){
      const u = new URL(s); const host = u.hostname; const path = u.pathname.replace(/\/+$/,'');
      const tail = path.split('/').filter(Boolean).slice(-2).join('/');
      return tail? `${host}/…/${tail}` : host;
    }
    if (s.length>48){ return s.slice(0,32)+'…'+s.slice(-12); }
    return s;
  }catch{ return String(k||''); }
}

// Redact any key named 'prompt' or 'prompts' (case-insensitive) at any depth
export function redactPromptsDeep(input){
  if (Array.isArray(input)) return input.map(redactPromptsDeep);
  if (!isPlainObject(input)) return input;
  const out = {};
  for (const [k,v] of Object.entries(input)){
    const kl = String(k).toLowerCase();
    if (kl==='prompt' || kl==='prompts') continue; // strip
    out[k] = redactPromptsDeep(v);
  }
  return out;
}

export function renderConfigHuman(host, cfg){
  host.innerHTML = '';
  const container = document.createElement('div');
  container.className = 'config-human';
  const sections = buildSections(cfg);
  sections.forEach(sec => container.appendChild(renderSection(sec)));
  if (!sections.length){ const pre = document.createElement('pre'); pre.className='io-pre'; pre.textContent = 'Aucun paramètre'; host.appendChild(pre); return; }
  host.appendChild(container);
}

export function buildSections(cfg){
  const out = [];
  if (!cfg || typeof cfg!=='object') return out;
  const scalars = []; const nested = [];
  for (const [k,v] of Object.entries(cfg)){
    if (isScalar(v)) scalars.push([k, v]); else nested.push([k,v]);
  }
  if (scalars.length) out.push({ title:'Général', kind:'kv', data: Object.fromEntries(scalars.sort((a,b)=> a[0].localeCompare(b[0]))) });
  nested.sort((a,b)=> a[0].localeCompare(b[0])).forEach(([k, v])=>{
    if (Array.isArray(v)) out.push({ title:k, kind:'list', data:v });
    else if (isMapOfScalars(v)) out.push({ title:k, kind:'kv', data:v });
    else {
      const shallow={};
      Object.entries(v||{}).forEach(([ck,cv])=>{ shallow[ck] = isScalar(cv)? cv : (Array.isArray(cv)? `[liste ${cv.length}]` : '[objet]'); });
      out.push({ title:k, kind:'kv', data:shallow });
    }
  });
  return out;
}

export function renderSection(sec){
  const card = document.createElement('div'); card.className = 'cfg-section';
  const h4 = document.createElement('h4'); h4.textContent = sec.title; card.appendChild(h4);
  if (sec.kind==='kv'){
    const grid = document.createElement('div'); grid.className = 'kv';
    const entries = Object.entries(sec.data||{});
    const MAX_ITEMS = 24; const more = entries.length>MAX_ITEMS ? entries.length-MAX_ITEMS : 0;
    entries.slice(0,MAX_ITEMS).forEach(([k,v])=>{
      const kk = document.createElement('div'); kk.className='k code'; kk.title=String(k);
      kk.textContent = shortenKey(k);
      const vv = document.createElement('div'); vv.className='v'; vv.textContent = String(formatVal(v));
      grid.append(kk, vv);
    });
    if (more){
      const kk = document.createElement('div'); kk.className='k'; kk.textContent = '…';
      const vv = document.createElement('div'); vv.className='v hint'; vv.textContent = `+${more} éléments`;
      grid.append(kk, vv);
    }
    card.appendChild(grid);
  } else if (sec.kind==='list'){
    const ul = document.createElement('ul'); ul.className='list';
    const items = sec.data||[];
    const MAX = 24; const more = items.length>MAX ? items.length-MAX : 0;
    items.slice(0,MAX).forEach(it=>{ const li=document.createElement('li'); li.className='pill'; li.textContent = String(formatVal(it)); ul.appendChild(li); });
    if (more){ const li=document.createElement('li'); li.className='pill hint'; li.textContent = `+${more} éléments`; ul.appendChild(li); }
    card.appendChild(ul);
  }
  return card;
}

function formatVal(v){
  if (Array.isArray(v)) return v.length ? `[liste ${v.length}]` : '[liste vide]';
  if (v && typeof v==='object') return '[objet]';
  if (v===null) return '—';
  if (v===true) return 'Oui'; if (v===false) return 'Non';
  return String(v);
}
