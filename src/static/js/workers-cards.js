
/**
 * Workers Cards - rendu HTML d'une carte worker (sobre & pro)
 */

function escapeHtml(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function getWorkerEmoji(workerId){ const emojis = { 'alain': '👨', 'sophie': '👩' }; return emojis[String(workerId||'').toLowerCase()] || '🤖'; }

function phoneIconSvg(size=18){
  return '<svg xmlns="http://www.w3.org/2000/svg" width="'+size+'" height="'+size+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.08 4.18 2 2 0 0 1 4.06 2h3a2 2 0 0 1 2 1.72c.12.81.31 1.6.57 2.36a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.72-1.72a2 2 0 0 1 2.11-.45c.76.26 1.55.45 2.36.57A2 2 0 0 1 22 16.92z"/></svg>';
}
function phoneDownIconSvg(size=18){
  return '<svg xmlns="http://www.w3.org/2000/svg" width="'+size+'" height="'+size+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2c-3.22-.37-6.27-1.55-8.63-3.07a19.5 19.5 0 0 1-6-6C3.67 10.49 2.49 7.44 2.12 4.22A2 2 0 0 1 4.06 2h3a2 2 0 0 1 2 1.72c.12.81.31 1.6.57 2.36a2 2 0 0 1-.45 2.11L8.09 9.91"/><path d="M23 1 1 23"/></svg>';
}

function renderWorkerCard(worker){
  const avatarUrl = worker.avatar_url;
  const hasGallery = Array.isArray(worker.gallery) && worker.gallery.length;

  const avatarCore = avatarUrl 
    ? '<img src="'+avatarUrl+'" alt="'+escapeHtml(worker.name)+'" class="worker-avatar-img" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';" />\n       <div class="worker-avatar-emoji" style="display:none;">'+getWorkerEmoji(worker.id)+'</div>'
    : '<div class="worker-avatar-emoji">'+getWorkerEmoji(worker.id)+'</div>';

  // Badge statut runtime (placeholder, sera rempli par refresh)
  const statusBadge = '<div class="status-badge chip" id="runtime-'+worker.id+'" title="Statut">—</div>';

  // Meta
  const metaHtml = ''+
    '<div class="worker-meta">'+
      (worker.job ? '<div class="worker-meta-line">Métier: '+escapeHtml(worker.job)+'</div>' : '')+
      (worker.employeur ? '<div class="worker-meta-line">Employeur: '+escapeHtml(worker.employeur)+(worker.employe_depuis ? ' (depuis '+escapeHtml(worker.employe_depuis)+')' : '')+'</div>' : '')+
    '</div>';

  // Barre d'icônes (Process • Galerie)
  const icons = [];
  icons.push('<button class="icon-btn" title="Processus" aria-label="Processus" onclick="openProcess(\''+worker.id+'\')">🧭</button>');
  if (hasGallery) icons.push('<button class="icon-btn" title="Galerie" aria-label="Galerie" onclick="toggleGallery(\''+worker.id+'\')">📷</button>');
  const iconbarHtml = '<div class="iconbar right">'+icons.join('')+'</div>';

  // Galerie
  const galleryHtml = hasGallery
    ? '<div class="worker-gallery collapsed" id="gallery-'+worker.id+'">\n'
      + '  <button class="gallery-nav prev" onclick="scrollGallery(\''+worker.id+'\', -1)" aria-label="Précédent">‹</button>\n'
      + '  <div class="gallery-track" id="galleryTrack-'+worker.id+'">\n'
      +        worker.gallery.map(function(u,ix){
               const url = String(u || '');
               const safeAlt = String(worker.name || '').replace(/\"/g, '&quot;');
               const safeUrl = url.replace(/\"/g, '&quot;');
               return '<div class="gallery-item" data-index="'+ix+'"><img src="'+safeUrl+'" alt="'+safeAlt+'" loading="lazy" onclick="openLightboxForWorker(\''+worker.id+'\', '+ix+', event)" onerror="this.parentElement.style.display=\'none\';"></div>';
             }).join('')
      + '  </div>\n'
      + '  <button class="gallery-nav next" onclick="scrollGallery(\''+worker.id+'\', 1)" aria-label="Suivant">›</button>\n'
      + '</div>'
    : '';

  const eventsHtml = ''+
    '<div class="worker-events" id="events-'+worker.id+'">'
      + '<div class="events-title">Derniers événements</div>'
      + '<div class="events-list" id="eventsList-'+worker.id+'">—</div>'
    + '</div>';

  const statsHtml = ''+
    '<div class="worker-stats">'
      + '<div class="stat">'
        + '<div class="stat-value" id="stat-'+worker.id+'-tasks">—</div>'
        + '<div class="stat-label">Tâches</div>'
      + '</div>'
      + '<div class="stat">'
        + '<div class="stat-value" id="stat-'+worker.id+'-errors">—</div>'
        + '<div class="stat-label">Erreurs</div>'
      + '</div>'
    + '</div>';

  const ctaHtml = ''+
    '<div class="worker-cta" id="cta-'+worker.id+'">'
      + '<button class="icon-btn" title="Appeler" aria-label="Appeler" onclick="callWorker(\''+worker.id+'\')" style="background:#10b981;color:#fff;border-color:#0e8f6f;">'+phoneIconSvg(18)+'</button>'
    + '</div>';

  // Structure
  return ''+
    '<div class="worker-card" id="card-'+worker.id+'" data-worker-id="'+worker.id+'">'
      + '<div class="worker-avatar">'
        + '<div class="avatar-wrap">'
        +   avatarCore
        +   '<div class="avatar-ring"></div>'
        + '</div>'
      + '</div>'
      + '<div class="worker-name">'+escapeHtml(worker.name)+'</div>'
      + statusBadge
      + metaHtml
      + iconbarHtml
      + galleryHtml
      + eventsHtml
      + statsHtml
      + ctaHtml
    + '</div>';
}

// Expose
window.renderWorkerCard = renderWorkerCard;
window.escapeHtml = escapeHtml; // util pour autres modules si besoin
