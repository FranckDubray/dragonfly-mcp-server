
// Utils (tiny)
export const $  = (s, r=document) => r.querySelector(s);
export const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));
export const delay = (ms)=> new Promise(r=>setTimeout(r, ms));
export function clamp(v, a, b){ return Math.max(a, Math.min(b, v)); }
export function copyText(txt){ try{ return navigator.clipboard.writeText(String(txt||'')); }catch{ return Promise.reject(); } }
export function approxTokens(text){ try{ return String(text||'').trim().split(/\s+/).filter(Boolean).length; }catch{ return 0; } }
