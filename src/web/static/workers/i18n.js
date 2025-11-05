











// i18n bootstrap: dynamic per-language modules under ./i18n/*.js
// Exports: t, setLang, getLang, initI18n, isRTL, listAvailableLangs, listAvailableLangsDetailed

const STORE_KEY = 'workers_ui_lang';
// Candidate language modules to probe (standalone packs under ./i18n)
// EU + global major languages; only codes we actually ship below
const CANDIDATES = [
  // Core EU (alpha)
  'bg','cs','da','de','el','en','es','et','fi','fr','ga','hr','hu','it','lt','lv','mt','nl','pl','pt','ro','sk','sl','sv',
  // Global set
  'ar','he','ru','ja','zh-Hans','zh-Hant','yue-Hant-HK','nan-Hant-TW',
  'hi','bn','ur','id','vi','ko','ta','fa','th','my','uk','fil','ms','km',
  // India large
  'pa-IN','pa-Arab-PK','mr','te','gu','ml','kn','or','sd-Arab-PK',
  // Regional widely used
  'ps','sw','am','om','ha-Latn','yo','ig','ne','ff-Latn',
  // SEA languages
  'jv','su-Latn',
  // Central Asia / Caucasus
  'uz-Latn','az-Latn','kmr-Latn','ckb-Arab-IQ',
  // Fun/extras kept
  'tlh','grc'
];

let currentLang = null;
let dict = {};            // active language dictionary (merged with FR fallback)
let available = null;     // cached available language codes
let availableDetailed = null; // cached detailed list [{code, flag, native, label}]
let defaultLangFromEnv = null; // set during init (from /config)

function _safe(obj, path){ try{ return path.split('.').reduce((o,k)=> (o||{})[k], obj); }catch{ return undefined; } }

function normalizeLangCode(code){
  // Map legacy or ambiguous tags to shipped packs
  const m = String(code||'').trim();
  if (m === 'zh') return 'zh-Hans';
  if (m === 'ha') return 'ha-Latn';
  if (m === 'su') return 'su-Latn';
  if (m === 'uz') return 'uz-Latn';
  if (m === 'az') return 'az-Latn';
  if (m === 'pa-PK') return 'pa-Arab-PK';
  if (m === 'sd' || m === 'sd-PK') return 'sd-Arab-PK';
  return m;
}

// Deep merge utility to overlay language packs over the FR base
function deepMerge(target, source){
  if (source == null) return target;
  const isObj = (v)=> v && typeof v === 'object' && !Array.isArray(v);
  for (const key of Object.keys(source)){
    const sv = source[key];
    if (isObj(sv)){
      if (!isObj(target[key])) target[key] = {};
      deepMerge(target[key], sv);
    }else{
      target[key] = sv;
    }
  }
  return target;
}

export function getLang(){
  try{
    const savedRaw = localStorage.getItem(STORE_KEY);
    const saved = normalizeLangCode(savedRaw);
    if (saved && (available||[]).includes(saved)) return saved;
  }catch{}
  // Env default first, then FR, then first available
  if (defaultLangFromEnv){
    const n = normalizeLangCode(defaultLangFromEnv);
    if ((available||[]).includes(n)) return n;
  }
  return (available&&available.includes('fr')) ? 'fr' : ((available&&available[0]) || 'fr');
}
export function setLang(lang){
  let n = normalizeLangCode(lang);
  if (!(available||[]).includes(n)) n = getLang();
  currentLang = n;
  try{ localStorage.setItem(STORE_KEY, n); }catch{}
  try{ document.documentElement.lang = n; document.documentElement.dir = isRTL(n) ? 'rtl' : 'ltr'; }catch{}
}
export function isRTL(lang){
  const l = String(lang||'').toLowerCase();
  // Base RTL + any tag using Arabic script ("-arab-")
  if (/^(ar|he|fa|ur|ps)($|-)/.test(l)) return true;
  if (l.startsWith('ckb')) return true; // Kurdish Sorani
  if (/-arab-/.test(l)) return true;    // e.g., pa-Arab-PK, sd-Arab-PK
  return false;
}

export async function listAvailableLangs(){
  if (available) return available.slice();
  const detailed = await listAvailableLangsDetailed();
  // sort by label asc
  detailed.sort((a,b)=> String(a.label||a.native||a.code).localeCompare(String(b.label||b.native||b.code)));
  available = detailed.map(it=>it.code);
  return available.slice();
}

export async function listAvailableLangsDetailed(){
  if (availableDetailed) return availableDetailed.slice();
  const out = [];
  for (const code of CANDIDATES){
    try{
      const mod = await import(`./i18n/${code}.js`);
      const meta = (mod && (mod.__meta || mod.meta || null)) || null;
      if (!meta || meta.standalone !== true) continue;
      const flag = String(meta.flag||'').trim();
      const native = String(meta.native||'').trim() || code;
      const label = `${flag?flag+' ':''}${native}`.trim();
      out.push({code, flag, native, label});
    }catch{ /* skip */ }
  }
  // alphabetical by label for the UI
  out.sort((a,b)=> String(a.label||a.native||a.code).localeCompare(String(b.label||b.native||b.code)));
  availableDetailed = out;
  return out.slice();
}

export async function initI18n(){
  // Discover language files (no server /config call)
  await listAvailableLangs();
  // Try to read default language from meta tag if provided
  try{
    const meta = document.querySelector('meta[name="workers-ui-lang-default"]');
    const envDefault = String(meta && meta.getAttribute('content') || '').trim().toLowerCase();
    if (envDefault) defaultLangFromEnv = envDefault;
  }catch{}
  let lang = getLang();
  setLang(lang);

  // Always load FR as the complete fallback base, then overlay the selected language
  const BASE_LANG = 'fr';
  let base = {};
  try{
    const baseMod = await import(`./i18n/${BASE_LANG}.js`);
    base = (baseMod && baseMod.default) || {};
  }catch{ base = {}; }

  let overlay = {};
  try{
    const mod = await import(`./i18n/${lang}.js`);
    overlay = (mod && mod.default) || {};
  }catch{ overlay = {}; }

  // Deep merge (FR -> selected)
  try{
    // clone base to avoid mutating the module object
    const clonedBase = JSON.parse(JSON.stringify(base));
    dict = deepMerge(clonedBase, overlay);
  }catch{
    // if anything fails, at least fall back to base
    dict = base || {};
  }

  try{ window.__i18n__ = { t, getLang, setLang }; }catch{}
}

export function t(key, fallback){
  const val = _safe(dict, key);
  if (typeof val === 'string') return val;
  return fallback || key;
}
