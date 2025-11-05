// Lightweight Config Editor with Simple and JSON modes
// - Simple: render basic scalar fields (string/number/boolean). Enums -> select. Others -> JSON-only notice.
// - JSON: textarea with beautify/validate. Emits parsed object via onChange.

export class ConfigEditor{
  constructor({schema=null, initial={}, onChange=null}={}){
    this.schema = schema || null;
    this.value = (initial && typeof initial==='object') ? structuredClone(initial) : {};
    this.onChange = typeof onChange==='function'? onChange : null;
    this.mode = 'simple'; // 'simple' | 'json'
    this._complexKeys = new Set();
    this.el = document.createElement('div');
    this.el.className = 'cfg-editor';
    this._build();
    this.render();
  }
  setSchema(schema){ this.schema = schema||null; this.render(); }
  setValue(obj){ this.value = (obj && typeof obj==='object')? structuredClone(obj) : {}; this.render(); }
  getValue(){ return structuredClone(this.value); }
  _build(){
    // Tabs
    const tabs = document.createElement('div'); tabs.className = 'tabs';
    const bSimple = document.createElement('button'); bSimple.className='tab'; bSimple.textContent='Simple';
    const bJson = document.createElement('button'); bJson.className='tab'; bJson.textContent='JSON';
    tabs.append(bSimple, bJson);
    this.el.appendChild(tabs);

    bSimple.addEventListener('click', ()=>{ this.mode='simple'; this.render(); });
    bJson.addEventListener('click', ()=>{ this.mode='json'; this.render(); });

    // Body containers
    const body = document.createElement('div'); body.className='cfg-body'; this._body=body; this.el.appendChild(body);
  }
  render(){
    // Tabs active state
    const [bSimple, bJson] = this.el.querySelectorAll('.tab');
    if (bSimple && bJson){
      bSimple.classList.toggle('active', this.mode==='simple');
      bJson.classList.toggle('active', this.mode==='json');
    }
    this._body.innerHTML='';
    if (this.mode==='simple') this._renderSimple(); else this._renderJson();
  }
  _renderSimple(){
    const wrap = document.createElement('div'); wrap.className='cfg-grid';
    const note = document.createElement('div'); note.className='hint';
    const keys = Object.keys(this.value||{}).sort();
    this._complexKeys.clear();

    const getProp = (k)=>{ try{ return (this.schema && this.schema.properties && this.schema.properties[k]) || null; }catch{return null;} };
    const getEnum = (p)=>{ try{ const e=p && Array.isArray(p.enum) ? p.enum : null; return e; }catch{return null;} };

    keys.forEach(k=>{
      const v = this.value[k];
      const prop = getProp(k);
      const en = getEnum(prop);
      const row = document.createElement('div'); row.className='cfg-row';
      const lab = document.createElement('label'); lab.className='k'; lab.textContent = String(k);
      const cell = document.createElement('div'); cell.className='v';
      let handled=false;

      if (en && (typeof v==='string' || typeof v==='number')){
        const sel = document.createElement('select'); sel.className='input';
        en.forEach(x=>{ const o=document.createElement('option'); o.value=String(x); o.textContent=String(x); if(String(v)===String(x)) o.selected=true; sel.appendChild(o); });
        sel.addEventListener('change', ()=>{ this.value[k] = sel.value; this._emit(); });
        cell.appendChild(sel); handled=true;
      } else if (typeof v==='boolean'){
        const chk=document.createElement('input'); chk.type='checkbox'; chk.checked=!!v; chk.addEventListener('change',()=>{ this.value[k]=!!chk.checked; this._emit(); });
        cell.appendChild(chk); handled=true;
      } else if (typeof v==='number'){
        const num=document.createElement('input'); num.type='number'; num.className='input'; num.value=String(v);
        num.addEventListener('input',()=>{ const n = Number(num.value); if (!Number.isNaN(n)) { this.value[k]=n; this._emit(); } });
        cell.appendChild(num); handled=true;
      } else if (typeof v==='string'){
        const inp=document.createElement('input'); inp.type='text'; inp.className='input'; inp.value=String(v);
        inp.addEventListener('input',()=>{ this.value[k]=inp.value; this._emit(); });
        cell.appendChild(inp); handled=true;
      } else {
        this._complexKeys.add(k);
        const badge = document.createElement('span'); badge.className='badge'; badge.textContent='JSON seulement';
        cell.appendChild(badge);
      }
      row.append(lab, cell); wrap.appendChild(row);
    });

    if (this._complexKeys.size){
      note.textContent = `Certains champs complexes ne sont modifiables qu'en JSON: ${Array.from(this._complexKeys).slice(0,6).join(', ')}${this._complexKeys.size>6?'…':''}`;
      this._body.append(note);
    }
    this._body.append(wrap);
  }
  _renderJson(){
    const tools = document.createElement('div'); tools.className='cfg-tools';
    const bBeautify = document.createElement('button'); bBeautify.className='btn small'; bBeautify.textContent='Beautify';
    const bMinify = document.createElement('button'); bMinify.className='btn small'; bMinify.textContent='Minify';
    const bValidate = document.createElement('button'); bValidate.className='btn small'; bValidate.textContent='Valider';
    tools.append(bBeautify, bMinify, bValidate);

    const ta = document.createElement('textarea'); ta.className='input'; ta.rows=16;
    try{ ta.value = JSON.stringify(this.value||{}, null, 2); }catch{ ta.value = '{}'; }

    const msg = document.createElement('div'); msg.className='hint';

    bBeautify.addEventListener('click', ()=>{
      try{ const obj=JSON.parse(ta.value); ta.value=JSON.stringify(obj,null,2); msg.textContent='OK'; msg.className='hint'; }
      catch(e){ msg.textContent=String(e.message||'JSON invalide'); msg.className='error-text'; }
    });
    bMinify.addEventListener('click', ()=>{
      try{ const obj=JSON.parse(ta.value); ta.value=JSON.stringify(obj); msg.textContent='OK'; msg.className='hint'; }
      catch(e){ msg.textContent=String(e.message||'JSON invalide'); msg.className='error-text'; }
    });
    bValidate.addEventListener('click', ()=>{
      try{ const obj=JSON.parse(ta.value); this.value=obj; this._emit(); msg.textContent='JSON valide'; msg.className='ok-text'; }
      catch(e){ msg.textContent=String(e.message||'JSON invalide'); msg.className='error-text'; }
    });

    this._body.append(tools, ta, msg);
  }
  _emit(){ try{ this.onChange && this.onChange(this.getValue()); }catch{} }
}
