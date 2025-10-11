




















CONTROL_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dragonfly MCP Control</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --sidebar-width: 300px;
            --primary: #10b981;
            --primary-hover: #059669;
            --secondary: #6366f1;
            --success: #10b981;
            --error: #ef4444;
            --warning: #f59e0b;
            --bg-main: #fafafa;
            --bg-sidebar: #ffffff;
            --bg-hover: #f3f4f6;
            --bg-card: #ffffff;
            --text-primary: #111827;
            --text-secondary: #6b7280;
            --border: #e5e7eb;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-main);
            color: var(--text-primary);
            overflow: hidden;
            height: 100vh;
            font-size: 14px;
            line-height: 1.5;
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
            box-shadow: var(--shadow-sm);
        }
        
        .sidebar-header {
            padding: 24px 20px;
            border-bottom: 1px solid var(--border);
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }
        
        .logo-container {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }
        
        .logo-emoji {
            font-size: 32px;
            line-height: 1;
        }
        
        .logo-text { flex: 1; }
        .logo { font-size: 20px; font-weight: 700; margin-bottom: 2px; letter-spacing: -0.02em; }
        .subtitle { font-size: 11px; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500; }
        
        /* Configuration button */
        .sidebar-config { padding: 16px; border-bottom: 1px solid var(--border); background: var(--bg-main); }
        .config-btn { 
            width: 100%; 
            padding: 10px 16px; 
            background: white; 
            color: var(--text-primary); 
            border: 1px solid var(--border); 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 13px; 
            font-weight: 600; 
            transition: all 0.2s;
            box-shadow: var(--shadow-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }
        .config-btn:hover { 
            background: var(--bg-hover); 
            border-color: var(--primary);
            box-shadow: var(--shadow);
        }
        
        /* Search box */
        .search-box { padding: 16px; border-bottom: 1px solid var(--border); background: var(--bg-main); }
        .search-input { 
            width: 100%; 
            padding: 10px 12px 10px 36px; 
            border: 1px solid var(--border); 
            border-radius: 8px; 
            font-size: 13px; 
            outline: none; 
            transition: all 0.2s;
            background: white url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="%236b7280" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>') 10px center no-repeat;
            box-shadow: var(--shadow-sm);
        }
        .search-input:focus { 
            border-color: var(--primary); 
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
        }
        .search-input::placeholder { color: var(--text-secondary); }
        
        /* Tools list */
        .tools-list { flex: 1; overflow-y: auto; padding: 12px 0; background: var(--bg-main); }
        
        /* Category section */
        .category-section { 
            margin-bottom: 16px;
        }
        
        .category-header { 
            padding: 10px 20px; 
            font-size: 11px; 
            font-weight: 700; 
            color: var(--text-secondary); 
            text-transform: uppercase; 
            letter-spacing: 0.08em; 
            display: flex; 
            align-items: center; 
            gap: 8px; 
            position: sticky; 
            top: 0; 
            z-index: 10; 
            cursor: pointer; 
            transition: all 0.2s;
            background: var(--bg-main);
        }
        
        .category-header:hover { 
            color: var(--text-primary);
        }
        
        .category-chevron { 
            font-size: 10px; 
            color: var(--text-secondary); 
            transition: transform 0.2s;
            font-weight: bold;
        }
        
        .category-section.collapsed .category-chevron {
            transform: rotate(-90deg);
        }
        
        .category-emoji { 
            font-size: 14px; 
        }
        
        .category-count { 
            margin-left: auto; 
            font-size: 10px; 
            color: var(--text-secondary); 
            font-weight: 600; 
            background: white; 
            padding: 2px 8px; 
            border-radius: 12px;
            border: 1px solid var(--border);
        }
        
        .category-tools { 
            max-height: 2000px; 
            overflow: hidden; 
            transition: max-height 0.3s ease-out, opacity 0.2s ease-out; 
            opacity: 1;
            padding: 0 12px;
        }
        
        .category-section.collapsed .category-tools { 
            max-height: 0; 
            opacity: 0; 
        }
        
        .tool-item { 
            padding: 10px 12px; 
            cursor: pointer; 
            transition: all 0.15s; 
            display: flex; 
            align-items: center; 
            gap: 10px;
            margin: 2px 0;
            border-radius: 8px;
            background: white;
            border: 1px solid transparent;
        }
        
        .tool-item:hover { 
            background: var(--bg-hover);
            border-color: var(--border);
            transform: translateX(2px);
        }
        
        .tool-item.active { 
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
            border-color: var(--primary);
            font-weight: 600;
            box-shadow: var(--shadow-sm);
        }
        
        .tool-icon { 
            font-size: 18px; 
            width: 24px; 
            text-align: center;
            flex-shrink: 0;
        }
        
        .tool-name { 
            flex: 1; 
            font-size: 13px;
            color: var(--text-primary);
            font-weight: 500;
        }
        
        .fav-btn {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 16px;
            padding: 4px;
            color: var(--text-secondary);
            transition: all 0.2s;
            flex-shrink: 0;
        }
        
        .fav-btn:hover {
            color: #fbbf24;
            transform: scale(1.2);
        }
        
        /* Zone principale */
        .main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        
        .main-header { 
            padding: 20px 32px; 
            border-bottom: 1px solid var(--border); 
            background: white;
            box-shadow: var(--shadow-sm);
        }
        
        .status-bar { 
            display: flex; 
            align-items: center; 
            gap: 8px; 
            padding: 10px 16px; 
            background: #eff6ff; 
            border-radius: 8px; 
            font-size: 13px; 
            color: #1e40af;
            border: 1px solid #dbeafe;
        }
        .status-bar.success { background: #f0fdf4; color: #15803d; border-color: #bbf7d0; }
        .status-bar.error { background: #fef2f2; color: #b91c1c; border-color: #fecaca; }
        
        .main-body { flex: 1; overflow-y: auto; padding: 32px; }
        .tool-view { max-width: 900px; margin: 0 auto; }
        
        .tool-header { 
            margin-bottom: 32px;
            padding: 24px;
            background: white;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
        }
        
        .tool-title { 
            font-size: 28px; 
            font-weight: 700; 
            color: var(--text-primary); 
            margin-bottom: 12px; 
            display: flex; 
            align-items: center; 
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .tool-badge { 
            font-size: 11px; 
            padding: 4px 10px; 
            border-radius: 6px; 
            background: var(--bg-hover); 
            color: var(--text-secondary);
            font-weight: 600;
            border: 1px solid var(--border);
        }
        
        .tool-description { 
            font-size: 15px; 
            color: var(--text-secondary); 
            line-height: 1.6;
        }
        
        /* Formulaire */
        .form-section { 
            background: white; 
            border: 1px solid var(--border); 
            border-radius: 12px; 
            padding: 24px; 
            margin-bottom: 24px;
            box-shadow: var(--shadow);
        }
        
        .form-group { margin-bottom: 20px; }
        .form-group:last-child { margin-bottom: 0; }
        
        .form-label { 
            display: block; 
            font-size: 13px; 
            font-weight: 600; 
            color: var(--text-primary); 
            margin-bottom: 8px;
        }
        
        .required-mark { color: var(--error); margin-left: 2px; }
        
        .form-input, .form-select { 
            width: 100%; 
            padding: 10px 12px; 
            border: 1px solid var(--border); 
            border-radius: 8px; 
            font-size: 14px; 
            font-family: inherit; 
            transition: all 0.2s;
            background: white;
            box-shadow: var(--shadow-sm);
        }
        
        .form-input:focus, .form-select:focus { 
            outline: none; 
            border-color: var(--primary); 
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
        }
        
        .form-select { 
            cursor: pointer; 
            appearance: none; 
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="%236b7280" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>');
            background-repeat: no-repeat; 
            background-position: right 12px center; 
            padding-right: 36px;
        }
        
        .form-help { 
            font-size: 12px; 
            color: var(--text-secondary); 
            margin-top: 6px; 
            line-height: 1.5;
        }
        
        .enum-hint { 
            font-size: 12px; 
            color: var(--primary); 
            margin-top: 6px; 
            font-style: italic;
        }
        
        .execute-btn { 
            width: 100%; 
            padding: 12px 24px; 
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
            color: white; 
            border: none; 
            border-radius: 8px; 
            font-size: 14px; 
            font-weight: 600; 
            cursor: pointer; 
            transition: all 0.2s; 
            box-shadow: var(--shadow);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .execute-btn:hover { 
            transform: translateY(-1px); 
            box-shadow: var(--shadow-md);
        }
        
        .execute-btn:active { 
            transform: translateY(0); 
        }
        
        .execute-btn:disabled { 
            opacity: 0.5; 
            cursor: not-allowed; 
            transform: none;
        }
        
        /* Résultat */
        .result-section { 
            background: white; 
            border: 1px solid var(--border); 
            border-radius: 12px; 
            overflow: hidden;
            box-shadow: var(--shadow);
        }
        
        .result-header { 
            padding: 16px 20px; 
            background: var(--bg-main); 
            border-bottom: 1px solid var(--border); 
            display: flex; 
            align-items: center; 
            justify-content: space-between;
        }
        
        .result-title { 
            font-size: 13px; 
            font-weight: 600; 
            color: var(--text-primary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .result-body { 
            padding: 20px; 
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace; 
            font-size: 13px; 
            line-height: 1.6; 
            color: var(--text-primary); 
            white-space: pre-wrap; 
            word-break: break-word; 
            max-height: 500px; 
            overflow-y: auto;
            background: #f9fafb;
        }
        
        .result-body.success { 
            background: #f0fdf4; 
            color: #15803d;
            border-left: 3px solid var(--success);
        }
        
        .result-body.error { 
            background: #fef2f2; 
            color: #b91c1c;
            border-left: 3px solid var(--error);
        }
        
        .result-body.empty { 
            text-align: center; 
            color: var(--text-secondary); 
            font-family: inherit; 
            font-style: italic;
            background: white;
        }
        
        /* Modal Config */
        .modal { 
            display: none; 
            position: fixed; 
            top: 0; left: 0; right: 0; bottom: 0; 
            background: rgba(0, 0, 0, 0.5); 
            z-index: 1000; 
            align-items: center; 
            justify-content: center; 
            padding: 20px;
            backdrop-filter: blur(4px);
        }
        
        .modal.active { display: flex; }
        
        .modal-content { 
            background: white; 
            border-radius: 16px; 
            padding: 32px; 
            max-width: 700px; 
            width: 100%; 
            max-height: 90vh; 
            overflow-y: auto; 
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border);
        }
        
        .modal-header { 
            display: flex; 
            align-items: center; 
            justify-content: space-between; 
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
        }
        
        .modal-title { 
            font-size: 24px; 
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .close-btn { 
            background: none; 
            border: none; 
            font-size: 24px; 
            cursor: pointer; 
            color: var(--text-secondary); 
            width: 32px; 
            height: 32px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            border-radius: 8px; 
            transition: all 0.2s;
        }
        
        .close-btn:hover { 
            background: var(--bg-hover); 
            color: var(--text-primary);
        }
        
        .config-status { 
            padding: 12px 16px; 
            border-radius: 8px; 
            margin-bottom: 20px; 
            font-size: 13px;
            border: 1px solid;
        }
        
        .config-status.success { 
            background: #f0fdf4; 
            color: #15803d;
            border-color: #bbf7d0;
        }
        
        .config-status.error { 
            background: #fef2f2; 
            color: #b91c1c;
            border-color: #fecaca;
        }
        
        .badge { 
            display: inline-block; 
            padding: 4px 8px; 
            border-radius: 6px; 
            font-size: 11px; 
            font-weight: 600; 
            margin-left: 8px;
        }
        
        .badge.present { 
            background: #dcfce7; 
            color: #15803d;
            border: 1px solid #bbf7d0;
        }
        
        .badge.absent { 
            background: #fee2e2; 
            color: #b91c1c;
            border: 1px solid #fecaca;
        }
        
        /* Empty state */
        .empty-state { 
            text-align: center; 
            padding: 80px 20px; 
            color: var(--text-secondary);
        }
        
        .empty-state-icon { 
            font-size: 64px; 
            margin-bottom: 16px; 
            opacity: 0.3;
        }
        
        .empty-state-text { 
            font-size: 16px;
            font-weight: 500;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar { 
                position: fixed; 
                left: -300px; 
                height: 100vh; 
                z-index: 100; 
                transition: left 0.3s;
            }
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
                <div class="logo-container">
                    <div class="logo-emoji">🐉</div>
                    <div class="logo-text">
                        <div class="logo">Dragonfly MCP</div>
                        <div class="subtitle">Control Panel</div>
                    </div>
                </div>
            </div>
            
            <div class="sidebar-config">
                <button class="config-btn" onclick="openConfig()">🔐 Configuration</button>
            </div>
            
            <div class="search-box">
                <input type="text" id="searchInput" class="search-input" placeholder="Search tools...">
            </div>
            
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

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
