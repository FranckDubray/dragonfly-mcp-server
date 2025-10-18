
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
  </style>
</head>
<body>
  <div class="app-container">
    {content}
  </div>
</body>
</html>
'''
