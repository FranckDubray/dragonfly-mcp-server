




"""
Control UI - layout shell (header/footer) and CSS/JS includes
Exports: CONTROL_LAYOUT_HTML (format string with {content})
"""

CONTROL_LAYOUT_HTML = '''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dragonfly MCP Control</title>
  <link rel="icon" type="image/svg+xml" href="https://ai.dragonflygroup.fr/assets/dragonflygroup/mobile-logo.svg?v=20251016-2">
  <link rel="stylesheet" href="/static/css/control.css">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    :root {
      --sidebar-width: 300px; --primary: #10b981; --primary-hover: #059669; --secondary: #6366f1;
      --success: #10b981; --error: #ef4444; --warning: #f59e0b; --bg-main: #fafafa; --bg-sidebar: #ffffff;
      --bg-hover: #f3f4f6; --bg-card: #ffffff; --text-primary: #111827; --text-secondary: #6b7280; --border: #e5e7eb;
      --shadow-sm: 0 1px 2px 0 rgba(0,0,0,.05); --shadow: 0 1px 3px 0 rgba(0,0,0,.1), 0 1px 2px -1px rgba(0,0,0,.1);
      --shadow-md: 0 4px 6px -1px rgba(0,0,0,.1), 0 2px 4px -2px rgba(0,0,0,.1); --shadow-lg: 0 10px 15px -3px rgba(0,0,0,.1), 0 4px 6px -4px rgba(0,0,0,.1);
    }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: var(--bg-main); color: var(--text-primary); overflow: hidden; height: 100vh; font-size: 14px; line-height: 1.5; }
    .app-container { display: flex; height: 100vh; }
    .main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
    .main-header { padding: 20px 32px; border-bottom: 1px solid var(--border); background: white; box-shadow: var(--shadow-sm); }
    .status-bar { display:flex; align-items:center; gap:8px; padding:10px 16px; background:#eff6ff; border-radius:8px; font-size:13px; color:#1e40af; border:1px solid #dbeafe; }
    .status-bar.success { background:#f0fdf4; color:#15803d; border-color:#bbf7d0; }
    .status-bar.error { background:#fef2f2; color:#b91c1c; border-color:#fecaca; }
    .main-body { flex:1; overflow-y:auto; padding:32px; }

    /* Basic modal styling for configuration */
    #configModal { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: none; z-index: 9999; }
    #configModal.active { display: block; }
    #configModal .modal-dialog { width: min(720px, 92vw); margin: 8vh auto; background: #fff; border-radius: 12px; box-shadow: var(--shadow-lg); overflow: hidden; }
    #configModal .modal-header { padding: 16px 20px; border-bottom: 1px solid var(--border); font-weight: 700; }
    #configModal .modal-body { padding: 16px 20px; max-height: 60vh; overflow: auto; }
    #configModal .modal-footer { padding: 12px 20px; border-top: 1px solid var(--border); display:flex; gap:8px; justify-content:flex-end; }
    #configModal .form-section { display: flex; flex-direction: column; gap: 12px; }
    #configStatus { display:none; margin-bottom: 10px; font-size: 13px; }
    .config-status.success { color: #15803d; }
    .config-status.error { color: #b91c1c; }

    .btn { cursor: pointer; padding: 8px 14px; border-radius: 8px; border: 1px solid var(--border); background: #fff; }
    .btn.primary { background: var(--primary); color: #fff; border-color: var(--primary); }
    .btn.primary:hover { background: var(--primary-hover); }
  </style>
</head>
<body>
  <div class="app-container">
    {content}
  </div>

  <!-- Config Modal (consumed by /static/js/config.js) -->
  <div id="configModal">
    <div class="modal-dialog" role="dialog" aria-modal="true">
      <div class="modal-header">Configuration</div>
      <div class="modal-body">
        <div id="configStatus" class="config-status"></div>
        <div class="form-section"></div>
      </div>
      <div class="modal-footer">
        <button class="btn" onclick="closeConfig()">Close</button>
        <button class="btn primary" onclick="saveConfig()">Save</button>
      </div>
    </div>
  </div>

  <!-- Control Panel scripts -->
  <script src="/static/js/categories.js"></script>
  <script src="/static/js/tools.js"></script>
  <script src="/static/js/search.js"></script>
  <script src="/static/js/config.js"></script>
  <script src="/static/js/main.js"></script>
</body>
</html>
'''
