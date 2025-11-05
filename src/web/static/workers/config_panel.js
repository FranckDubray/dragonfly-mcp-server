
























import { t } from './i18n.js';

export class ConfigPanel{
  constructor(root){
    this.box = document.createElement('div');
    this.box.className = 'panel';
    this.title = document.createElement('h3');
    this.title.textContent = t('config.title');

    // Vue "humaine" en 2 colonnes, sans JSON brut
    this.human = document.createElement('div');
    this.human.className = 'config-human';

    // Fallback (debug) si nécessaire
    this.pre = document.createElement('pre'); this.pre.className = 'io-pre'; this.pre.style.display = 'none';

    this.box.append(this.title, this.human, this.pre);
    root.appendChild(this.box);
  }
  async load(worker){
    try{
      const r = await fetch(`/workers/api/config?worker=${encodeURIComponent(worker)}`);
      const js = await r.json();
      this.renderHuman(js||{});
    }catch(e){
      this.pre.style.display='block';
      this.pre.textContent = t('config.none');
    }
  }
  renderHuman(js){
    const meta = js.metadata || {};
    const docs = js.docs || {};
    const sections = [];

    // Section: Général (llm_model, db_path, etc.)
    const general = {
      title: t('config.general'),
      kv: []
    };
    const pushIf = (k, v) => { if (v!==undefined && v!==null && String(v).trim()!=='') general.kv.push([k, v]); };
    pushIf('LLM', meta.llm_model || meta.model || '—');
    pushIf('SQLite', meta.db_file || js.db_path || '—');
    if (general.kv.length) sections.push(general);

    // Section: Paramètres (config.json) — sans les prompts
    const params = {...meta};
    delete params.prompts; delete params.db_file; delete params.llm_model; delete params.model;
    const flat = flattenObject(params);
    const flatKeys = Object.keys(flat);
    if (flatKeys.length){
      sections.push({ title: t('config.params'), kv: flatKeys.map(k => [k, fmt(flat[k])]) });
    }

    // Section: Documentation template (CONFIG_DOC.json)
    const docTitle = docs.title || '';
    const docDesc = docs.description || '';
    if (docTitle || docDesc){
      const dsec = { title: t('config.docs'), kv: [] };
      if (docTitle) dsec.kv.push([t('config.doc_title'), docTitle]);
      if (docDesc) dsec.kv.push([t('config.doc_desc'), docDesc]);
      sections.push(dsec);
    }

    // Render
    this.human.innerHTML = '';
    sections.forEach(sec => {
      const card = document.createElement('div'); card.className = 'cfg-section';
      const h4 = document.createElement('h4'); h4.textContent = sec.title;
      const grid = document.createElement('div'); grid.className = 'kv';
      (sec.kv||[]).forEach(([k,v])=>{
        const kk = document.createElement('div'); kk.className='k'; kk.textContent = String(k);
        const vv = document.createElement('div'); vv.className='v'; vv.textContent = String(v);
        grid.append(kk, vv);
      });
      card.append(h4, grid);
      this.human.appendChild(card);
    });

    // Si rien, fallback texte
    if (!sections.length){
      this.pre.style.display='block';
      this.pre.textContent = t('config.none');
    } else {
      this.pre.style.display='none';
    }
  }
}

function flattenObject(obj, prefix=''){ const out={}; try{ Object.entries(obj||{}).forEach(([k,v])=>{ const nk = prefix? `${prefix}.${k}` : k; if (v && typeof v==='object' && !Array.isArray(v)) Object.assign(out, flattenObject(v, nk)); else out[nk]=v; }); }catch{} return out; }
function fmt(v){ if (Array.isArray(v)) return v.join(', '); if (typeof v==='object' && v) return Object.keys(v).length? '[objet]' : '—'; if (v===true) return 'Oui'; if (v===false) return 'Non'; if (v===''||v==null) return '—'; return v; }
