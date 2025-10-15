/**
 * Workers Cards - rendu HTML d'une carte worker (sobre & pro)
 */

function escapeHtml(s){ return String(s||'').replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>'); }
function getWorkerEmoji(workerId){ const emojis = { 'alain': '👨', 'sophie': '👩' }; return emojis[String(workerId||'').toLowerCase()] || '🤖'; }

function renderWorkerCard(worker){
  const avatarUrl = worker.avatar_url;
  const hasGallery = Array.isArray(worker.gallery) && worker.gallery.length;

  const avatarHtml = avatarUrl 
    ? '<img src="'+avatarUrl+'" alt="'+escapeHtml(worker.name)+'" class="worker-avatar-img" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';" />\n       <div class="worker-avatar-emoji" style="display:none;">'+getWorkerEmoji(worker.id)+'</div>'
    : '<div class="worker-avatar-emoji">'+getWorkerEmoji(worker.id)+'</div>';

  const statutHtml = worker.statut ? '<div class="worker-statut">'+escapeHtml(worker.statut)+'</div>' : '';

  const availabilityHtml = (worker.working_hours || worker.timezone)
    ? '<div class="worker-meta-line">Dispo: '+escapeHtml(worker.working_hours || '')+(worker.timezone ? ' ('+escapeHtml(worker.timezone)+')' : '')+'</div>'
    : '';
  const emailInline = worker.email ? '<div class="worker-meta-line">✉️ <a href="mailto:'+encodeURI(worker.email)+'">'+escapeHtml(worker.email)+'</a></div>' : '';
  const tagsHtml = Array.isArray(worker.tags) && worker.tags.length
    ? '<div class="worker-meta-line">'+worker.tags.slice(0,3).map(t => '<span class="chip">'+escapeHtml(t)+'</span>').join(' ')+'</div>'
    : '';

  const metaHtml = ''+
    '<div class="worker-meta">'+
      (worker.job ? '<div class="worker-meta-line">Métier: '+escapeHtml(worker.job)+'</div>' : '')+
      (worker.employeur ? '<div class="worker-meta-line">Employeur: '+escapeHtml(worker.employeur)+(worker.employe_depuis ? ' (depuis '+escapeHtml(worker.employe_depuis)+')' : '')+'</div>' : '')+
      availabilityHtml+
      emailInline+
      tagsHtml+
    '</div>';

  // Barre d'icônes : Process • Galerie • Email
  const icons = [];
  icons.push('<button class="icon-btn" title="Processus" aria-label="Processus" onclick="openProcess(\''+worker.id+'\')">🧭</button>');
  if (hasGallery) icons.push('<button class="icon-btn" title="Galerie" aria-label="Galerie" onclick="toggleGallery(\''+worker.id+'\')">📷</button>');
  if (worker.email) icons.push('<a class="icon-btn" title="Email" aria-label="Email" href="mailto:'+encodeURI(worker.email)+'">✉️</a>');
  const iconbarHtml = '<div class="worker-gallery-toggle"><div class="iconbar">'+icons.join('')+'</div></div>';

  // Galerie (slider discret — RESTORE collapsed)
  const galleryHtml = hasGallery
    ? '<div class="worker-gallery collapsed" id="gallery-'+worker.id+'">\n'
      + '  <button class="gallery-nav prev" onclick="scrollGallery(\''+worker.id+'\', -1)" aria-label="Précédent">‹</button>\n'
      + '  <div class="gallery-track" id="galleryTrack-'+worker.id+'">\n'
      +        worker.gallery.map((u,ix) => {
               const url = String(u || '');
               const safeAlt = String(worker.name || '').replace(/\"/g, '&quot;');
               const safeUrl = url.replace(/\"/g, '&quot;');
               return '<div class="gallery-item" data-index="'+ix+'"><img src="'+safeUrl+'" alt="'+safeAlt+'" loading="lazy" onclick="openLightboxForWorker(\''+worker.id+'\', '+ix+', event)" onerror="this.parentElement.style.display=\'none\';"></div>';
             }).join('')
      + '  </div>\n'
      + '  <button class="gallery-nav next" onclick="scrollGallery(\''+worker.id+'\', 1)" aria-label="Suivant">›</button>\n'
      + '</div>'
    : '';

  // Latency dot (si dispo en DB)
  let latencyHtml = '';
  const lat = Number(worker.latency_hint_ms || 0);
  if (lat > 0) {
    let cls = 'latency-green';
    if (lat >= 400) cls = 'latency-red'; else if (lat >= 150) cls = 'latency-orange';
    const title = '~'+Math.round(lat)+' ms';
    latencyHtml = '<div class="latency-dot '+cls+'" id="latency-'+worker.id+'" title="'+title+'" style="display:none;"></div>';
  }

  const eventsHtml = ''+
    '<div class="worker-events" id="events-'+worker.id+'">'+
      '<div class="events-title">Derniers événements</div>'+
      '<div class="events-list" id="eventsList-'+worker.id+'">—</div>'+
    '</div>';

  const emailBtn = worker.email ? '<a class="btn btn-ghost" href="mailto:'+encodeURI(worker.email)+'" title="Contacter par email">✉️ Email</a>' : '';

  return ''+
    '<div class="worker-card" id="card-'+worker.id+'">'+
      '<div class="worker-avatar">'+
        avatarHtml+
        '<div class="online-dot" id="online-'+worker.id+'"></div>'+
        latencyHtml+
      '</div>'+
      '<div class="worker-name">'+escapeHtml(worker.name)+'</div>'+
      metaHtml+
      iconbarHtml+
      galleryHtml+
      statutHtml+
      eventsHtml+
      '<div class="worker-stats">'+
        '<div class="stat">'+
          '<div class="stat-value" id="stat-'+worker.id+'-tasks">—</div>'+
          '<div class="stat-label">Tâches</div>'+
        '</div>'+
        '<div class="stat">'+
          '<div class="stat-value" id="stat-'+worker.id+'-errors">—</div>'+
          '<div class="stat-label">Erreurs</div>'+
        '</div>'+
      '</div>'+
      '<div class="worker-cta" id="cta-'+worker.id+'">'+
        '<button class="btn btn-primary" onclick="callWorker(\''+worker.id+'\')">📞 Appeler</button>'+
        emailBtn+
      '</div>'+
    '</div>';
}

// Expose
window.renderWorkerCard = renderWorkerCard;
window.escapeHtml = escapeHtml; // util pour autres modules si besoin
