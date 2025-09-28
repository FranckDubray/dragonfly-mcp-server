CONTROL_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Server Control</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .tool-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 20px; }
        .tool-card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .tool-title { font-size: 1.2em; font-weight: bold; margin-bottom: 10px; color: #333; }
        .tool-description { color: #666; margin-bottom: 15px; font-size: 0.9em; }
        .param-group { margin-bottom: 15px; }
        .param-label { display: block; margin-bottom: 5px; font-weight: bold; color: #555; font-size: 0.9em; }
        .param-input, .param-select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; font-size: 0.9em; }
        .param-select { background: white; cursor: pointer; }
        .param-select:focus, .param-input:focus { border-color: #007bff; outline: none; box-shadow: 0 0 0 2px rgba(0,123,255,0.25); }
        .param-help { font-size: 0.8em; color: #888; margin-top: 2px; line-height: 1.3; }
        .execute-btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 1em; margin-top: 10px; }
        .execute-btn:hover { background: #0056b3; }
        .result-area { margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px; min-height: 20px; border: 1px solid #e9ecef; font-family: monospace; font-size: 0.85em; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
        .error { background: #f8d7da; border-color: #f5c6cb; color: #721c24; }
        .success { background: #d4edda; border-color: #c3e6cb; color: #155724; }
        .status { margin-bottom: 20px; padding: 10px; border-radius: 4px; }
        .loading { opacity: 0.6; pointer-events: none; }
        .enum-options { font-size: 0.75em; color: #007bff; margin-top: 2px; font-style: italic; }
        .required-mark { color: #dc3545; font-weight: bold; }
        .reload-notice { background: #d1ecf1; border-color: #bee5eb; color: #0c5460; margin-bottom: 10px; padding: 8px 12px; border-radius: 4px; font-size: 0.85em; }
        .auto-reload-status { background: #d4edda; border-color: #c3e6cb; color: #155724; margin-bottom: 10px; padding: 8px 12px; border-radius: 4px; font-size: 0.85em; }
        .config-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.75em; background: #eee; color: #333; margin-left: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 MCP Server Control Panel</h1>
            <div id="status" class="status">Loading tools...</div>
            <div class="auto-reload-status">🔄 Auto-reload enabled - New tools detected automatically!</div>
            <button onclick="reloadTools()" class="execute-btn">🔄 Force Reload Tools</button>
            <div class="reload-notice">💡 Form values are preserved when reloading tools</div>
        </div>

        <div class="tool-card">
            <div class="tool-title">🔑 Secrets & Tokens</div>
            <div class="tool-description">Saisissez vos tokens (ils seront stockés dans un fichier .env local non versionné). Les valeurs existantes ne sont pas affichées.</div>
            <div class="config-grid">
                <div class="param-group">
                    <label class="param-label">GitHub Token (GITHUB_TOKEN) <span id="ghBadge" class="badge">checking...</span></label>
                    <input id="GITHUB_TOKEN" type="password" class="param-input" placeholder="nouvelle valeur (laisser vide pour ne pas changer)">
                </div>
                <div class="param-group">
                    <label class="param-label">AI Portal Token (AI_PORTAL_TOKEN) <span id="aiBadge" class="badge">checking...</span></label>
                    <input id="AI_PORTAL_TOKEN" type="password" class="param-input" placeholder="nouvelle valeur (laisser vide pour ne pas changer)">
                </div>
                <div class="param-group" style="grid-column: 1 / span 2;">
                    <label class="param-label">LLM Endpoint (LLM_ENDPOINT)</label>
                    <input id="LLM_ENDPOINT" type="text" class="param-input" placeholder="https://... (optionnel)">
                </div>
            </div>
            <button onclick="saveConfig()" class="execute-btn">💾 Enregistrer la configuration</button>
            <div id="configStatus" class="status" style="margin-top:10px;"></div>
        </div>

        <div id="toolGrid" class="tool-grid">
            <!-- Tools will be loaded here -->
        </div>
    </div>
    <script src="/control.js"></script>
</body>
</html>'''
