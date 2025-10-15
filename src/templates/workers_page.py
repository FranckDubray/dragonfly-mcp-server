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
    <link rel="stylesheet" href="/static/css/workers.css">
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
            <input type="range" min="0" max="1" step="0.01" value="1" oninput="setVolume(this.value)" />
        </div>
    </div>

    <!-- Scripts (ordre important) -->
    <script src="/static/js/workers-ringback.js"></script>
    <script src="/static/js/workers-status.js"></script>
    <script src="/static/js/workers-gallery.js"></script>
    <script src="/static/js/workers-cards.js"></script>
    <script src="/static/js/workers-grid.js"></script>
    <script src="/static/js/workers-calls.js"></script>
    <script src="/static/js/workers-vu.js"></script>
    <script src="/static/js/workers-audio.js"></script>
    <!-- Session split (nouveau) -->
    <script src="/static/js/workers-session-state.js"></script>
    <script src="/static/js/workers-session-core.js"></script>
    <script src="/static/js/workers-session-ws.js"></script>
    <script src="/static/js/workers-session-tools.js"></script>
    <script src="/static/js/workers-session-audio.js"></script>
    <!-- Process split (mermaid render sanitize) -->
    <script src="/static/js/workers-process-render.js"></script>
    <script src="/static/js/workers-process.js"></script>

    <script>
        // Init au chargement
        window.addEventListener('DOMContentLoaded', () => {
            loadWorkers();
        });
    </script>
</body>
</html>
'''
