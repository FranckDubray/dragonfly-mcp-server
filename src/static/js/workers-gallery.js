/**
 * Workers Gallery & Lightbox (discret)
 */

function toggleGallery(workerId){
  const gal = document.getElementById(`gallery-${workerId}`);
  const chev = document.getElementById(`galleryChevron-${workerId}`); // legacy (inutile si absent)
  if (!gal) return;
  const willOpen = gal.classList.contains('collapsed');
  gal.classList.toggle('collapsed', !willOpen);
  if (chev) chev.textContent = willOpen ? '▾' : '▸';
}

function scrollGallery(workerId, dir){
  const track = document.getElementById(`galleryTrack-${workerId}`);
  if (!track) return;
  const first = track.querySelector('img');
  const step = first ? (first.clientWidth + 10) : Math.round(track.clientWidth * 0.8);
  track.scrollBy({ left: dir * step, behavior: 'smooth' });
}

// Lightbox
let _lightboxEl = null;
let _lightboxState = { list: [], index: 0, title: '' };
function ensureLightbox(){
  if (_lightboxEl) return _lightboxEl;
  const overlay = document.createElement('div');
  overlay.className = 'lightbox-overlay';
  overlay.innerHTML = `
    <div class="lightbox-content">
      <button class="lightbox-close" aria-label="Fermer" title="Fermer">×</button>
      <button class="lightbox-nav prev" aria-label="Précédent">‹</button>
      <div class="lightbox-frame">
        <img class="lightbox-img" alt="aperçu" />
      </div>
      <button class="lightbox-nav next" aria-label="Suivant">›</button>
    </div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', (e)=>{ if (e.target === overlay) closeLightbox(); });
  overlay.querySelector('.lightbox-close').addEventListener('click', closeLightbox);
  overlay.querySelector('.lightbox-nav.prev').addEventListener('click', ()=>showLightboxIndex(_lightboxState.index-1));
  overlay.querySelector('.lightbox-nav.next').addEventListener('click', ()=>showLightboxIndex(_lightboxState.index+1));
  document.addEventListener('keydown', (e)=>{
    if (!overlay.classList.contains('open')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') showLightboxIndex(_lightboxState.index-1);
    if (e.key === 'ArrowRight') showLightboxIndex(_lightboxState.index+1);
  });
  _lightboxEl = overlay;
  return overlay;
}

function openLightboxForWorker(workerId, index, ev){
  const worker = (window.workersData||[]).find(w=>String(w.id)===String(workerId));
  if (!worker || !Array.isArray(worker.gallery) || !worker.gallery.length) return;
  _lightboxState.list = worker.gallery.map(String);
  _lightboxState.index = Math.max(0, Math.min(index||0, _lightboxState.list.length-1));
  _lightboxState.title = worker.name || '';
  const el = ensureLightbox();
  try {
    const x = (ev?.clientX || window.innerWidth/2) / window.innerWidth * 100;
    const y = (ev?.clientY || window.innerHeight/2) / window.innerHeight * 100;
    el.style.setProperty('--lb-origin-x', x + '%');
    el.style.setProperty('--lb-origin-y', y + '%');
  } catch(_){}
  el.classList.add('open');
  showLightboxIndex(_lightboxState.index, true);
}

function showLightboxIndex(ix){
  if (!_lightboxEl) return;
  const n = _lightboxState.list.length;
  if (n===0) return;
  if (ix<0) ix = n-1; if (ix>=n) ix = 0;
  _lightboxState.index = ix;
  const img = _lightboxEl.querySelector('.lightbox-img');
  try { img.style.opacity = '0'; } catch(_){ }
  const url = _lightboxState.list[ix];
  img.onload = ()=>{ try{ img.style.opacity = '1'; }catch(_){} };
  img.src = url; img.alt = _lightboxState.title ? `${_lightboxState.title} – ${ix+1}/${n}` : `Image ${ix+1}/${n}`;
}

function closeLightbox(){ if (_lightboxEl) { _lightboxEl.classList.remove('open'); } }

// Expose
window.toggleGallery = toggleGallery;
window.scrollGallery = scrollGallery;
window.openLightboxForWorker = openLightboxForWorker;
window.closeLightbox = closeLightbox;
