/**
 * Workers Process - Render (Mermaid) + sanitize labels + repair pass
 * Sans template literals complexes (évite erreurs de parsing)
 */

function escapeHtml(s){ return String(s||'').replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>'); }

function stripCodeFences(text){
  var t = String(text||'').trim();
  if (t.indexOf('```') === 0){
    t = t.replace(/^```[a-zA-Z]*\n?/, '').replace(/```$/, '');
  }
  return t;
}

function buildIdLabelMap(diagram){
  var map = new Map();
  var lines = String(diagram||'').split(/\r?\n/);
  var re = /^\s*([A-Za-z][A-Za-z0-9_]*)\s*(\[.*?\]|\(.*?\)|\{.*?\}|\(\(.*?\)\)|\[\[.*?\]\])/;
  for (var i=0;i<lines.length;i++){
    var line = lines[i];
    var m = line.match(re);
    if (!m) continue;
    var id = m[1];
    var shape = m[2];
    var label = shape.slice(1, -1);
    if ((shape.indexOf('((')===0 && /\)\)$/.test(shape)) || (shape.indexOf('[[')===0 && /\]\]$/.test(shape))){
      label = shape.slice(2, -2);
    }
    var norm = normalizeLabel(label);
    if (norm) map.set(norm, id);
  }
  return map;
}

function normalizeLabel(s){
  return String(s||'').trim().replace(/^\"|\"$/g,'').replace(/^'|'$/g,'');
}

function normalizeKey(s){
  return String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,'');
}

function escapeMermaidLabel(label){
  return String(label||'').replace(/\\/g,'\\\\').replace(/\"/g,'\\"').replace(/`/g,'\`');
}

function sanitizeMermaid(diagram){
  var lines = String(diagram||'').split(/\r?\n/);
  var re = /(\b[A-Za-z][A-Za-z0-9_]*)(\s*)(\[.*?\]|\(.*?\)|\{.*?\}|\(\(.*?\)\)|\[\[.*?\]\])/g;
  var out = lines.map(function(line){
    return line.replace(re, function(full, id, space, shape){
      var open = shape[0], close = shape[shape.length-1];
      var content = shape.slice(1,-1);
      if ((shape.indexOf('((')===0 && /\)\)$/.test(shape)) || (shape.indexOf('[[')===0 && /\]\]$/.test(shape))){
        content = shape.slice(2,-2);
      }
      var esc = escapeMermaidLabel(normalizeLabel(content));
      if (shape.indexOf('((')===0 && /\)\)$/.test(shape)) return id + space + '(("' + esc + '"))';
      if (shape.indexOf('[[')===0 && /\]\]$/.test(shape)) return id + space + '[["' + esc + '"]]';
      return id + space + open + '"' + esc + '"' + close;
    });
  });
  return out.join('\n');
}

function repairMermaid(diagram){
  // Répare des flèches manquantes courantes: ") -\nX" → ") --> X"
  var lines = String(diagram||'').split(/\r?\n/);
  var fixed = [];
  for (var i=0;i<lines.length;i++){
    var line = lines[i];
    // si une ligne se termine par ' -' sans '>'
    if (/\s-\s*$/.test(line) && line.indexOf('->')===-1 && line.indexOf('-->')===-1){
      // tenter de joindre avec la prochaine ligne si elle commence par un id
      var next = lines[i+1]||'';
      var m = next.match(/^\s*([A-Za-z][A-Za-z0-9_]*)\b/);
      if (m){
        // fusionner en une seule ligne avec '-->'
        line = line.replace(/-\s*$/, '') + ' --> ' + m[1];
        // supprimer le début de la prochaine ligne (l'identifiant), le reste reste
        lines[i+1] = next.replace(/^\s*[A-Za-z][A-Za-z0-9_]*\b\s*/, '');
      } else {
        // sinon, remplacer par '-->' à la fin de la ligne
        line = line.replace(/-\s*$/, ' -->');
      }
    }
    fixed.push(line);
  }
  return fixed.join('\n');
}

async function renderMermaid(mermaidText, container, highlightNode){
  var attempt = 0;
  var lastError = null;
  var id = 'mmd-' + Math.random().toString(36).slice(2);
  var base = String(mermaidText||'');
  var variants = [];
  try { variants.push(sanitizeMermaid(stripCodeFences(base))); } catch(_){ variants.push(stripCodeFences(base)); }
  try { variants.push(repairMermaid(variants[0])); } catch(_){ }

  // Injection de style/classe pour le highlight
  function tryRender(diagram){
    return window.mermaid.render(id, diagram + '\nclassDef current stroke:#2563eb,stroke-width:3px,fill:#eaf1ff;');
  }

  while (attempt < variants.length){
    try {
      var diagram = variants[attempt];
      var out = await tryRender(diagram);
      container.innerHTML = '';
      var wrapper = document.createElement('div');
      wrapper.className = 'mermaid-graph';
      wrapper.innerHTML = out.svg || '';
      container.appendChild(wrapper);
      return; // success
    } catch (e) {
      lastError = e;
      attempt++;
    }
  }
  console.error('[Mermaid] render failed:', lastError);
  container.innerHTML = '<pre class="code">' + escapeHtml(mermaidText||'') + '</pre>';
}

window.renderMermaid = renderMermaid;
window.escapeHtml = escapeHtml;
