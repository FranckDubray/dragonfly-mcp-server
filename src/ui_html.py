




















CONTROL_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dragonfly MCP Control</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --sidebar-width: 280px;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --success: #10b981;
            --error: #ef4444;
            --warning: #f59e0b;
            --bg-main: #ffffff;
            --bg-sidebar: #f8fafc;
            --bg-hover: #f1f5f9;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border: #e2e8f0;
            --shadow: 0 1px 3px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 25px rgba(0,0,0,0.15);
            --chip-bg: #eef2ff;
            --chip-text: #3730a3;
            --chip-active-bg: #c7d2fe;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-main);
            color: var(--text-primary);
            overflow: hidden;
            height: 100vh;
        }
        
        /* Layout principal */
        .app-container {
            display: flex;
            height: 100vh;
        }
        
        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .logo-img {
            width: 48px;
            height: 48px;
            object-fit: contain;
            background: #ffffff;
            padding: 4px;
            border-radius: 8px;
            box-shadow: var(--shadow);
        }
        
        .logo-text { flex: 1; }
        .logo { font-size: 20px; font-weight: 700; color: var(--text-primary); margin-bottom: 2px; }
        .subtitle { font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* Configuration button */
        .sidebar-config { padding: 12px 16px; border-bottom: 1px solid var(--border); }
        .config-btn { width: 100%; padding: 10px; background: var(--primary); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.2s; }
        .config-btn:hover { background: var(--primary-hover); }
        
        /* Search box */
        .search-box { padding: 12px 16px; border-bottom: 1px solid var(--border); }
        .search-input { width: 100%; padding: 10px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; outline: none; transition: all 0.2s; }
        .search-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1); }
        
        /* Tools list */
        .tools-list { flex: 1; overflow-y: auto; padding: 8px 0; }
        
        /* Category section */
        .category-section { 
            margin-bottom: 12px; 
            border-bottom: 2px solid var(--border);
        }
        
        .category-header { 
            padding: 12px 20px; 
            font-size: 13px; 
            font-weight: 800; 
            color: var(--text-primary); 
            text-transform: uppercase; 
            letter-spacing: 1px; 
            display: flex; 
            align-items: center; 
            gap: 10px; 
            background: linear-gradient(to right, #e2e8f0, #f8fafc);
            position: sticky; 
            top: 0; 
            z-index: 10; 
            cursor: pointer; 
            transition: all 0.2s;
            border-left: 4px solid var(--primary);
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        
        .category-header:hover { 
            background: linear-gradient(to right, #cbd5e1, #f1f5f9);
        }
        
        .category-chevron { 
            font-size: 12px; 
            color: var(--primary); 
            transition: transform 0.2s;
            font-weight: bold;
        }
        
        .category-section.collapsed .category-chevron {
            transform: rotate(-90deg);
        }
        
        .category-emoji { 
            font-size: 16px; 
        }
        
        .category-count { 
            margin-left: auto; 
            font-size: 11px; 
            color: white; 
            font-weight: 700; 
            background: var(--primary); 
            padding: 3px 8px; 
            border-radius: 12px;
            box-shadow: 0 1px 2px rgba(37, 99, 235, 0.3);
        }
        
        .category-tools { 
            max-height: 1000px; 
            overflow: hidden; 
            transition: max-height 0.3s ease-out, opacity 0.3s ease-out; 
            opacity: 1;
            background: #ffffff;
            padding: 4px 0;
        }
        
        .category-section.collapsed .category-tools { 
            max-height: 0; 
            opacity: 0; 
            padding: 0;
        }
        
        .tool-item { 
            padding: 10px 20px 10px 28px; 
            cursor: pointer; 
            border-left: 3px solid transparent; 
            transition: all 0.2s; 
            display: flex; 
            align-items: center; 
            gap: 10px;
            margin: 2px 0;
        }
        
        .tool-item:hover { 
            background: var(--bg-hover); 
            border-left-color: var(--primary);
            padding-left: 32px;
        }
        
        .tool-item.active { 
            background: #eff6ff; 
            border-left-color: var(--primary); 
            font-weight: 600;
            border-left-width: 4px;
        }
        
        .tool-icon { 
            font-size: 18px; 
            width: 24px; 
            text-align: center; 
        }
        
        .tool-name { 
            flex: 1; 
            font-size: 13px;
            color: var(--text-primary);
        }
        
        .tool-badge { 
            font-size: 9px; 
            padding: 2px 6px; 
            border-radius: 4px; 
            background: #f1f5f9; 
            color: var(--text-secondary);
            font-family: 'Courier New', monospace;
        }
        
        /* Zone principale */
        .main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .main-header { padding: 20px 32px; border-bottom: 1px solid var(--border); background: var(--bg-main); }
        .status-bar { display: flex; align-items: center; gap: 12px; padding: 10px 16px; background: #f0f9ff; border-radius: 8px; font-size: 13px; color: #0369a1; }
        .status-bar.success { background: #f0fdf4; color: #15803d; }
        .status-bar.error { background: #fef2f2; color: #b91c1c; }
        .main-body { flex: 1; overflow-y: auto; padding: 32px; }
        .tool-view { max-width: 800px; margin: 0 auto; }
        .tool-header { margin-bottom: 32px; }
        .tool-title { font-size: 28px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; display: flex; align-items: center; gap: 12px; }
        .tool-description { font-size: 15px; color: var(--text-secondary); line-height: 1.6; }
        
        /* Formulaire */
        .form-section { background: var(--bg-main); border: 1px solid var(--border); border-radius: 12px; padding: 24px; margin-bottom: 24px; }
        .form-group { margin-bottom: 20px; }
        .form-group:last-child { margin-bottom: 0; }
        .form-label { display: block; font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; }
        .required-mark { color: var(--error); margin-left: 2px; }
        .form-input, .form-select { width: 100%; padding: 10px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; font-family: inherit; transition: all 0.2s; }
        .form-input:focus, .form-select:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1); }
        .form-select { cursor: pointer; appearance: none; background-repeat: no-repeat; background-position: right 12px center; padding-right: 36px; }
        .form-help { font-size: 13px; color: var(--text-secondary); margin-top: 4px; line-height: 1.4; }
        .enum-hint { font-size: 12px; color: var(--primary); margin-top: 4px; font-style: italic; }
        .execute-btn { width: 100%; padding: 14px; background: var(--primary); color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s; box-shadow: var(--shadow); }
        .execute-btn:hover { background: var(--primary-hover); transform: translateY(-1px); box-shadow: var(--shadow-lg); }
        .execute-btn:active { transform: translateY(0); }
        .execute-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        
        /* Résultat */
        .result-section { background: var(--bg-sidebar); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
        .result-header { padding: 16px 20px; background: var(--bg-main); border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; }
        .result-title { font-size: 14px; font-weight: 600; color: var(--text-primary); }
        .result-body { padding: 20px; font-family: 'Courier New', monospace; font-size: 13px; line-height: 1.6; color: var(--text-primary); white-space: pre-wrap; word-break: break-word; max-height: 400px; overflow-y: auto; }
        .result-body.success { background: #f0fdf4; color: #15803d; }
        .result-body.error { background: #fef2f2; color: #b91c1c; }
        .result-body.empty { text-align: center; color: var(--text-secondary); font-family: inherit; font-style: italic; }
        
        /* Modal Config */
        .modal { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }
        .modal.active { display: flex; }
        .modal-content { background: var(--bg-main); border-radius: 16px; padding: 32px; max-width: 600px; width: 100%; max-height: 90vh; overflow-y: auto; box-shadow: var(--shadow-lg); }
        .modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
        .modal-title { font-size: 24px; font-weight: 700; }
        .close-btn { background: none; border: none; font-size: 24px; cursor: pointer; color: var(--text-secondary); width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 6px; transition: all 0.2s; }
        .close-btn:hover { background: var(--bg-hover); }
        .config-status { padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; }
        .config-status.success { background: #f0fdf4; color: #15803d; }
        .config-status.error { background: #fef2f2; color: #b91c1c; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; margin-left: 8px; }
        .badge.present { background: #dcfce7; color: #15803d; }
        .badge.absent { background: #fee2e2; color: #b91c1c; }
        
        /* Loading */
        .loading { opacity: 0.6; pointer-events: none; }
        
        /* Empty state */
        .empty-state { text-align: center; padding: 80px 20px; color: var(--text-secondary); }
        .empty-state-icon { font-size: 64px; margin-bottom: 16px; opacity: 0.3; }
        .empty-state-text { font-size: 16px; }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar { position: fixed; left: -280px; height: 100vh; z-index: 100; transition: left 0.3s; }
            .sidebar.mobile-open { left: 0; }
            .main-body { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sidebar -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <img src="/logo" alt="Dragonfly" class="logo-img">
                <div class="logo-text">
                    <div class="logo">Dragonfly</div>
                    <div class="subtitle">MCP Control Panel</div>
                </div>
            </div>
            
            <div class="sidebar-config">
                <button class="config-btn" onclick="openConfig()">🔐 Configuration</button>
            </div>
            
            <div class="search-box">
                <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search tools...">
            </div>

            <!-- Tags box removed -->
            
            <div class="tools-list" id="toolsList">
                <!-- Tools seront injectés ici par catégorie -->
            </div>
        </aside>
        
        <!-- Zone principale -->
        <main class="main-content">
            <div class="main-header">
                <div id="statusBar" class="status-bar">
                    ⏳ Loading tools...
                </div>
            </div>
            
            <div class="main-body">
                <div id="mainView">
                    <div class="empty-state">
                        <div class="empty-state-icon">🔧</div>
                        <div class="empty-state-text">Select a tool from the sidebar to get started</div>
                    </div>
                </div>
            </div>
        </main>
    </div>
    
    <!-- Modal Config -->
    <div id="configModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">🔐 Configuration</h2>
                <button class="close-btn" onclick="closeConfig()">×</button>
            </div>
            
            <div id="configStatus" class="config-status" style="display: none;"></div>
            
            <div class="form-section">
                <p class="form-help" style="text-align: center; color: var(--text-secondary);">
                    Loading configuration...
                </p>
            </div>
            
            <button onclick="saveConfig()" class="execute-btn">💾 Save Configuration</button>
        </div>
    </div>
    
    <!-- Load JavaScript modules in order -->
    <script src="/static/js/categories.js"></script>
    <script src="/static/js/config.js"></script>
    <script src="/static/js/tools.js"></script>
    <script src="/static/js/search.js"></script>
    <script src="/static/js/main.js"></script>
</body>
</html>'''

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
