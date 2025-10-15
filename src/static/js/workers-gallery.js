// Workers Gallery & Lightbox (do NOT open by default; toggle with icon)
(() => {
  const qs = (s, r=document) => r.querySelector(s);
  let lightbox, bg, fig, img, caption, closeBtn;
  let isOpen = false;
  let currentThumb = null;

  function setup() {
    lightbox = qs('#photoLightbox');
    if (!lightbox) return;
    bg = lightbox.querySelector('.df-lightbox-bg');
    fig = lightbox.querySelector('.df-lightbox-figure');
    img = lightbox.querySelector('.df-lightbox-img');
    caption = lightbox.querySelector('.df-lightbox-caption');
    closeBtn = lightbox.querySelector('.df-lightbox-close');

    bg.addEventListener('click', close, { passive: true });
    closeBtn.addEventListener('click', close, { passive: true });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
  }

  function getCenter(rect){ return { x: rect.left + rect.width/2, y: rect.top + rect.height/2 }; }

  async function open(src, alt, thumbEl) {
    if (!lightbox) setup(); if (!lightbox) return; if (isOpen) return;
    currentThumb = (thumbEl && thumbEl.getBoundingClientRect) ? thumbEl : null;

    img.style.transition = 'none'; img.style.transform = 'none'; img.style.willChange = 'transform, opacity';
    img.src = src; img.alt = alt || ''; caption.textContent = alt || '';

    lightbox.classList.remove('hidden'); lightbox.setAttribute('aria-hidden', 'false'); document.body.classList.add('df-no-scroll');

    if (!img.complete || img.naturalWidth === 0) await new Promise(r => { img.onload = r; img.onerror = r; });

    const finalRect = img.getBoundingClientRect();
    lightbox.classList.add('show');

    const thumbRect = currentThumb ? currentThumb.getBoundingClientRect() : null;
    if (thumbRect && finalRect.width > 0 && finalRect.height > 0) {
      const from = getCenter(thumbRect), to = getCenter(finalRect);
      const dx = from.x - to.x, dy = from.y - to.y; const sx = thumbRect.width / finalRect.width, sy = thumbRect.height / finalRect.height;
      img.style.transformOrigin = 'center center';
      img.style.transform = `translate(${dx}px, ${dy}px) scale(${sx}, ${sy})`;
      img.style.transition = 'transform 320ms cubic-bezier(.2,.8,.2,1), opacity 200ms ease-out';
      requestAnimationFrame(() => { img.style.transform = 'translate(0,0) scale(1,1)'; img.style.opacity = '1'; });
    } else {
      img.style.opacity = '0'; img.style.transition = 'transform 260ms cubic-bezier(.2,.8,.2,1), opacity 200ms ease-out';
      img.style.transform = 'scale(.94)';
      requestAnimationFrame(() => { img.style.opacity = '1'; img.style.transform = 'scale(1)'; });
    }
    isOpen = true;
  }

  function close() {
    if (!isOpen || !lightbox) return;
    const finalRect = img.getBoundingClientRect(); const thumbRect = (currentThumb && currentThumb.isConnected) ? currentThumb.getBoundingClientRect() : null;
    if (thumbRect && finalRect.width > 0 && finalRect.height > 0) {
      const from = getCenter(finalRect), to = getCenter(thumbRect);
      const dx = to.x - from.x, dy = to.y - from.y; const sx = thumbRect.width / finalRect.width, sy = thumbRect.height / finalRect.height;
      img.style.transition = 'transform 260ms cubic-bezier(.2,.8,.2,1), opacity 160ms ease-in';
      img.style.transform = `translate(${dx}px, ${dy}px) scale(${sx}, ${sy})`; img.style.opacity = '0.85';
    } else { img.style.transition = 'transform 220ms ease, opacity 160ms ease-in'; img.style.transform = 'scale(.96)'; img.style.opacity = '0'; }
    lightbox.classList.remove('show');
    setTimeout(() => {
      lightbox.classList.add('hidden'); lightbox.setAttribute('aria-hidden', 'true'); document.body.classList.remove('df-no-scroll');
      img.style.transition = 'none'; img.style.transform = 'none'; img.style.opacity = ''; img.src = ''; caption.textContent = ''; isOpen = false; currentThumb = null;
    }, 260);
  }

  function toggleGallery(workerId){
    const g = document.getElementById(`gallery-${workerId}`);
    if (!g) return; g.classList.toggle('collapsed');
  }

  // Scroll exactly one full image (including gap) per click
  function scrollGallery(workerId, dir){
    const track = document.getElementById(`galleryTrack-${workerId}`);
    if (!track) return;
    const items = track.querySelectorAll('.gallery-item');
    if (!items.length) return;
    const first = items[0];
    const second = items.length > 1 ? items[1] : null;
    const itemWidth = first.clientWidth || 160;
    let gap = 8;
    try{
      if (second){
        const r1 = first.getBoundingClientRect();
        const r2 = second.getBoundingClientRect();
        gap = Math.max(0, Math.round(r2.left - r1.right));
      }
    }catch(_){ }
    const step = itemWidth + gap;
    const current = Math.round(track.scrollLeft / step);
    const targetIndex = Math.max(0, Math.min(items.length-1, current + (dir||1)));
    const maxLeft = track.scrollWidth - track.clientWidth;
    const targetLeft = Math.max(0, Math.min(targetIndex * step, maxLeft));
    track.scrollTo({ left: targetLeft, behavior: 'smooth' });
  }

  function openLightboxForWorker(workerId, index, ev){
    if (ev && ev.preventDefault) ev.preventDefault();
    try{
      const w = (window.workersData||[]).find(x => String(x.id) === String(workerId));
      const pics = Array.isArray(w?.gallery) ? w.gallery : [];
      const ix = Math.max(0, Math.min(Number(index)||0, Math.max(0, pics.length-1)));
      const src = pics[ix] || '';
      const thumb = document.querySelector(`#galleryTrack-${CSS.escape(workerId)} .gallery-item[data-index="${ix}"] img`);
      if (!src) return;
      open(src, w?.name || '', thumb);
    }catch(_){ }
  }

  function init(){
    setup();
    // Lightbox only for gallery items or explicit data-full images
    document.addEventListener('click', (e) => {
      const t = e.target;
      const isGallery = !!t.closest?.('.gallery-item');
      const isExplicit = t.matches?.('img[data-full]');
      if (!(isGallery || isExplicit)) return;
      const a = t.closest('a'); if (a) e.preventDefault();
      const src = t.dataset.full || t.src; open(src, t.alt || '', t);
    }, true);
  }

  window.initWorkersLightbox = init;
  window.toggleGallery = toggleGallery;
  window.scrollGallery = scrollGallery;
  window.openLightboxForWorker = openLightboxForWorker;
  window.openPhotoLightbox = open;
  window.closePhotoLightbox = close;
})();
