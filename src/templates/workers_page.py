

"""
HTML page Workers Realtime
Mode téléphone simple : click et allo
"""

WORKERS_HTML = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workers Vocaux - Dragonfly MCP</title>
    <link rel="stylesheet" href="/static/css/workers.css?v=20251015-3">
    <style>
      /* Inline fallback (minimal) to guarantee avatar sizing even if external CSS fails */
      .worker-card .avatar-wrap { position: relative; display: inline-grid; place-items: center; }
      .worker-card img.worker-photo,
      .worker-card img.worker-avatar-img { width: 64px; height: 64px; border-radius: 50%; object-fit: cover; display: block; }
      .worker-card .avatar-ring { position: absolute; inset: -6px; border-radius: 50%; pointer-events: none; --level: 0; }
    </style>
    <!-- Preload Mermaid early to avoid first-render delay -->
    <script>
      (function(){
        try{
          if (!document.querySelector('script[data-mermaid]')){
            var s=document.createElement('script');
            s.src='https://unpkg.com/mermaid@10/dist/mermaid.min.js';
            s.async=true; s.defer=true; s.setAttribute('data-mermaid','1');
            s.onload=function(){ try{ window.mermaid.initialize({ startOnLoad:false, theme:'neutral', securityLevel:'loose' }); }catch(e){} };
            document.head.appendChild(s);
          }
        }catch(_){ }
      })();
    </script>
</head>
<body>
    <div class="app-container">
        <!-- Header -->
        <header class="header">
            <div class="header-left">
                <h1 class="logo">🐉 Dragonfly MCP</h1>
                <span class="header-subtitle">Workers Vocaux Temps Réel</span>
            </div>
            <div class="header-right">
                <a href="/control" class="btn btn-ghost">← Retour Control Panel</a>
            </div>
        </header>

        <!-- Grid Workers -->
        <div class="workers-container">
            <div class="workers-grid" id="workersGrid">
                <!-- Chargement -->
                <div class="loading-state">
                    <div class="spinner"></div>
                    <p>Chargement des workers...</p>
                </div>
            </div>
        </div>

        <!-- Call Overlay (conservé, mais non utilisé pour inline) -->
        <div class="call-overlay" id="callOverlay"></div>

        <!-- Audio element (hidden) -->
        <audio id="remoteAudio" autoplay playsinline></audio>

        <!-- Mini transcripts (petite fonte, discret) -->
        <div class="mini-transcripts" id="miniTranscripts">
            <div class="mini-title">Transcripts (session)</div>
            <div class="mini-body" id="miniTranscriptsBody"></div>
        </div>

        <!-- Volume slider (call only) -->
        <div id="volumeSlider" style="display:none">
            <label>Volume</label>
            <input type="range" min="0" max="1" step="0.01" value="0.5" oninput="setVolume(this.value)" />
        </div>
    </div>

    <!-- Photo Lightbox (overlay) -->
    <div id="photoLightbox" class="df-lightbox hidden" aria-hidden="true">
      <div class="df-lightbox-bg"></div>
      <figure class="df-lightbox-figure">
        <img class="df-lightbox-img" alt="">
        <figcaption class="df-lightbox-caption"></figcaption>
        <button class="df-lightbox-close" aria-label="Fermer">×</button>
      </figure>
    </div>

    <!-- Scripts (ordre important) -->
    <script src="/static/js/workers-ringback.js?v=20251015-3"></script>
    <script src="/static/js/workers-status.js?v=20251015-3"></script>
    <script src="/static/js/workers-gallery.js?v=20251015-3"></script>
    <script src="/static/js/workers-cards.js?v=20251015-3"></script>
    <script src="/static/js/workers-grid.js?v=20251015-3"></script>
    <script src="/static/js/workers-calls.js?v=20251015-3"></script>
    <script src="/static/js/workers-vu.js?v=20251015-3"></script>
    <script src="/static/js/workers-audio.js?v=20251015-3"></script>
    <!-- Session split -->
    <script src="/static/js/workers-session-state.js?v=20251015-3"></script>
    <script src="/static/js/workers-session-core.js?v=20251015-3"></script>
    <script src="/static/js/workers-session-ws.js?v=20251015-3"></script>
    <script src="/static/js/workers-session-tools.js?v=20251015-3"></script>
    <script src="/static/js/workers-session-audio.js?v=20251015-3"></script>
    <!-- Process split (mermaid render sanitize + modules) -->
    <script src="/static/js/workers-process-render.js?v=20251015-3"></script>
    <script src="/static/js/workers-process-state.js?v=20251015-3"></script>
    <script src="/static/js/workers-process-overlay.js?v=20251015-3"></script>
    <script src="/static/js/workers-process-data.js?v=20251015-3"></script>
    <script src="/static/js/workers-process-consistency.js?v=20251015-3"></script>
    <script src="/static/js/workers-process-ui-side.js?v=20251015-3"></script>
    <script src="/static/js/workers-process-ui-core.js?v=20251015-3"></script>
    <script src="/static/js/workers-process-ui-replay.js?v=20251015-3"></script>
    <script src="/static/js/workers-process.js?v=20251015-3"></script>

    <script>
        // Init au chargement
        window.addEventListener('DOMContentLoaded', () => {
            // Progressive enhancement: ensure avatars have ring wrapper
            document.querySelectorAll('.worker-card img.worker-photo, .worker-card img.worker-avatar-img').forEach((img) => {
              const wrap = img.closest('.avatar-wrap');
              if (!wrap) {
                const w = document.createElement('div');
                w.className = 'avatar-wrap';
                const ring = document.createElement('div');
                ring.className = 'avatar-ring';
                const parent = img.parentElement;
                parent.insertBefore(w, img);
                w.appendChild(img);
                w.appendChild(ring);
              } else if (!wrap.querySelector('.avatar-ring')) {
                const ring = document.createElement('div');
                ring.className = 'avatar-ring';
                wrap.appendChild(ring);
              }
              // S'assure des dimensions même sans CSS externe
              img.style.width = '64px'; img.style.height = '64px'; img.style.borderRadius = '50%'; img.style.objectFit = 'cover';
            });

            // Gallery init if available (n'ouvre pas sur l'avatar sans data-full)
            if (window.initWorkersLightbox) window.initWorkersLightbox();

            // Charger les workers
            if (typeof loadWorkers === 'function') {
              loadWorkers();
            }
        });
    </script>
</body>
</html>
'''
