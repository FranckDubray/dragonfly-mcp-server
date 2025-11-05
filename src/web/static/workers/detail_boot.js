
import { GraphView } from './graph_view.js';
import { IOPanel } from './io_panel.js';
import { ConfigPanel } from './config_panel.js';
import { StatusPanel } from './status_panel.js';
import { LeaderIdentityPanel } from './leader_identity_panel.js';
// Leader chat panel removed as requested
import { ReplayPanel } from './replay_panel.js';
import { api } from './api.js';

const worker = window.__WORKER_NAME__;
const root = document.getElementById('app-worker-detail');

let headerAvatar = null;

function setAura(el, {phase}){
  try{
    const p = String(phase||'').toLowerCase();
    el.classList.add('aura');
    el.classList.remove('a--running','a--tool','a--sleep','a--stop-ok','a--stop-err');
    if (p==='failed'){ el.classList.add('a--stop-err'); }
    else if (p==='running' || p==='starting'){ el.classList.add('a--running'); }
    else { el.classList.add('a--stop-ok'); }
  }catch{}
}

// Cosmetic banner title: "{display_name} — Worker" + avatar aura + status dot
async function renderTitleBanner(){
  try{
    const r = await fetch(`/workers/api/identity?worker=${encodeURIComponent(worker)}`);
    const js = await r.json();
    const dn = (js && js.identity && js.identity.display_name) ? String(js.identity.display_name).trim() : '';
    const avatarUrl = (js && js.identity && js.identity.avatar_url) ? String(js.identity.avatar_url).trim() : '';

    const banner = document.createElement('div');
    banner.className = 'panel';

    const head = document.createElement('div');
    head.style.cssText = 'display:flex; align-items:center; gap:10px; flex-wrap:wrap;';

    // Mini avatar with aura
    headerAvatar = document.createElement('div');
    headerAvatar.className = 'avatar aura a--stop-ok';
    headerAvatar.style.width = '36px';
    headerAvatar.style.height = '36px';
    headerAvatar.style.borderWidth = '2px';
    const pic = document.createElement('div');
    pic.className = 'img';
    if (avatarUrl){
      const url = (/^https?:\/\//i.test(avatarUrl) || avatarUrl.startsWith('/') ? avatarUrl : `/docs/images/${avatarUrl}`);
      pic.style.backgroundImage = `url('${url.replace(/'/g,"%27")}')`;
    }
    headerAvatar.appendChild(pic);

    const h = document.createElement('h2');
    h.textContent = dn ? `${dn} — Worker` : 'Worker';

    const dot = document.createElement('span');
    dot.className = 'state-dot dot-idle';
    dot.setAttribute('title','Status');

    head.append(headerAvatar, h, dot);
    banner.appendChild(head);
    root.prepend(banner);

    startHeaderStatusLoop(dot);
  }catch{}
}

async function startHeaderStatusLoop(dotEl){
  async function tick(){
    try{
      const st = await api.status(worker);
      const ph = String(st.phase || st.status || '').toLowerCase();
      // dot
      dotEl.classList.remove('dot-running','dot-idle','dot-error');
      if (ph === 'failed') dotEl.classList.add('dot-error');
      else if (ph === 'running' || ph === 'starting') dotEl.classList.add('dot-running');
      else dotEl.classList.add('dot-idle');
      // aura
      if (headerAvatar) setAura(headerAvatar, {phase: ph});
    }catch{}
    setTimeout(tick, 4000);
  }
  tick();
}

await renderTitleBanner();

// Panels
const io = new IOPanel(root);
new ConfigPanel(root);
new StatusPanel(root, worker);
new LeaderIdentityPanel(root, worker);
// new LeaderChatPanel(root, worker); // removed
new ReplayPanel(root, worker);

// Graph view (handles toolbar, graph, highlight, observe/debug modes)
const gv = new GraphView(worker, root, io);
gv.attach();
