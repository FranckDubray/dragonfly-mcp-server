





// Markdown safe render (tiny, dependency-free)
// Supports: headings (#, ##), bold ** **, italic * *, inline code ``, links [text](url),
// lists (-, *), paragraphs and line breaks. Sanitizes to a small whitelist.

function escapeHtml(s){ return String(s||'').replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
function sanitizeHref(url){ try{ const u=String(url||'').trim(); if(!u) return ''; const low=u.toLowerCase(); if(low.startsWith('javascript:')||low.startsWith('data:')) return ''; return u; }catch{return '';} }

function toHtml(md){
  let text = String(md||'');
  // Normalize newlines
  text = text.replace(/\r\n?/g,'\n');

  // Code fences ```lang\n...\n```
  text = text.replace(/```([A-Za-z0-9_-]+)?\n([\s\S]*?)```/g, (m,lang,body)=>{
    const safe = escapeHtml(body);
    const cls = lang ? ` class="lang-${escapeHtml(lang)}"` : '';
    return `<div class="code-toolbar"><pre><code${cls}>${safe}</code></pre><button class="copy-btn" data-act="copy">Copier</button></div>`;
  });

  // Code spans
  text = text.replace(/`([^`]+)`/g, (m,code)=> `<code>${escapeHtml(code)}</code>`);

  // Headings (limited to # and ##)
  text = text.replace(/^##\s+(.+)$/gm, (_,t)=> `<h3>${escapeHtml(t)}</h3>`);
  text = text.replace(/^#\s+(.+)$/gm,  (_,t)=> `<h2>${escapeHtml(t)}</h2>`);

  // Lists (simple)
  text = text.replace(/^(?:- |\* )(.*)$/gm, (_,t)=> `<li>${escapeHtml(t)}</li>`);
  text = text.replace(/(<li>.*<\/li>)(\n<li>.*<\/li>)+/g, (m)=> `<ul>${m}</ul>`);

  // Bold / Italic (basic, non-greedy)
  text = text.replace(/\*\*([^*]+)\*\*/g, (m,t)=> `<strong>${escapeHtml(t)}</strong>`);
  text = text.replace(/\*([^*]+)\*/g, (m,t)=> `<em>${escapeHtml(t)}</em>`);

  // Links [text](url)
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (m,txt,href)=>{
    const safe = sanitizeHref(href);
    const label = escapeHtml(txt);
    return safe? `<a href="${safe}" target="_blank" rel="noopener noreferrer">${label}</a>` : label;
  });

  // Paragraphs & line breaks
  const blocks = text.split(/\n{2,}/).map(b=> b.trim()).filter(Boolean);
  const html = blocks.map(b=>{
    if (/^\s*<(h2|h3|ul|li|p|code|div|pre|button)\b/i.test(b) || /<li>/.test(b)) return b; // already a block
    return `<p>${b.replace(/\n/g,'<br>')}</p>`; // Convert single newlines to <br>
  }).join('\n');
  return html;
}

function sanitizeFinal(html){
  // Remove any tag not in whitelist (a, p, br, code, strong, em, ul, li, h2, h3, pre, div, button)
  const whitelist = /^(a|p|br|code|strong|em|ul|li|h2|h3|pre|div|button)$/i;
  const div = document.createElement('div');
  div.innerHTML = String(html||'');
  const walker = document.createTreeWalker(div, NodeFilter.SHOW_ELEMENT, null);
  const toRemove = [];
  while(walker.nextNode()){
    const el = walker.currentNode;
    if (!whitelist.test(el.tagName)){ toRemove.push(el); continue; }
    if (el.tagName.toLowerCase()==='a'){
      const href = sanitizeHref(el.getAttribute('href')||'');
      if (!href){ el.replaceWith(document.createTextNode(el.textContent||'')); continue; }
      el.setAttribute('href', href);
      el.setAttribute('target','_blank'); el.setAttribute('rel','noopener noreferrer');
    }
    if (el.tagName.toLowerCase()==='button'){
      el.removeAttribute('onclick'); el.setAttribute('type','button');
    }
  }
  toRemove.forEach(n=>{ try{ n.replaceWith(document.createTextNode(n.textContent||'')); }catch{} });
  return div.innerHTML;
}

export function renderMarkdownSafe(mdText){
  try{
    const html = toHtml(mdText);
    return sanitizeFinal(html);
  }catch{ return escapeHtml(mdText||'').replace(/\n/g,'<br>'); }
}

 
 
 
 
 
 
 
 
 
