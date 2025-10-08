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
        
        .logo-text {
            flex: 1;
        }
        
        .logo {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 2px;
        }
        
        .subtitle {
            font-size: 11px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .search-box {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
        }
        
        .search-input {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: all 0.2s;
        }
        
        .search-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .tools-list {
            flex: 1;
            overflow-y: auto;
            padding: 8px 0;
        }
        
        .tool-item {
            padding: 12px 20px;
            cursor: pointer;
            border-left: 3px solid transparent;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .tool-item:hover {
            background: var(--bg-hover);
        }
        
        .tool-item.active {
            background: var(--bg-main);
            border-left-color: var(--primary);
            font-weight: 600;
        }
        
        .tool-icon {
            font-size: 18px;
            width: 24px;
            text-align: center;
        }
        
        .tool-name {
            flex: 1;
            font-size: 14px;
        }
        
        .tool-badge {
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            background: var(--border);
            color: var(--text-secondary);
        }
        
        .sidebar-footer {
            padding: 12px 16px;
            border-top: 1px solid var(--border);
        }
        
        .config-btn {
            width: 100%;
            padding: 10px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .config-btn:hover {
            background: var(--primary-hover);
        }
        
        /* Zone principale */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .main-header {
            padding: 20px 32px;
            border-bottom: 1px solid var(--border);
            background: var(--bg-main);
        }
        
        .status-bar {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 16px;
            background: #f0f9ff;
            border-radius: 8px;
            font-size: 13px;
            color: #0369a1;
        }
        
        .status-bar.success { background: #f0fdf4; color: #15803d; }
        .status-bar.error { background: #fef2f2; color: #b91c1c; }
        
        .main-body {
            flex: 1;
            overflow-y: auto;
            padding: 32px;
        }
        
        .tool-view {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .tool-header {
            margin-bottom: 32px;
        }
        
        .tool-title {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .tool-description {
            font-size: 15px;
            color: var(--text-secondary);
            line-height: 1.6;
        }
        
        /* Formulaire */
        .form-section {
            background: var(--bg-main);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group:last-child {
            margin-bottom: 0;
        }
        
        .form-label {
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 6px;
        }
        
        .required-mark {
            color: var(--error);
            margin-left: 2px;
        }
        
        .form-input, .form-select {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
            transition: all 0.2s;
        }
        
        .form-input:focus, .form-select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .form-select {
            cursor: pointer;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M10.293 3.293L6 7.586 1.707 3.293A1 1 0 00.293 4.707l5 5a1 1 0 001.414 0l5-5a1 1 0 10-1.414-1.414z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 12px center;
            padding-right: 36px;
        }
        
        .form-help {
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 4px;
            line-height: 1.4;
        }
        
        .enum-hint {
            font-size: 12px;
            color: var(--primary);
            margin-top: 4px;
            font-style: italic;
        }
        
        .execute-btn {
            width: 100%;
            padding: 14px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: var(--shadow);
        }
        
        .execute-btn:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
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
            background: var(--bg-sidebar);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
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
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .result-body {
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
            color: var(--text-primary);
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .result-body.success {
            background: #f0fdf4;
            color: #15803d;
        }
        
        .result-body.error {
            background: #fef2f2;
            color: #b91c1c;
        }
        
        .result-body.empty {
            text-align: center;
            color: var(--text-secondary);
            font-family: inherit;
            font-style: italic;
        }
        
        /* Modal Config */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .modal.active {
            display: flex;
        }
        
        .modal-content {
            background: var(--bg-main);
            border-radius: 16px;
            padding: 32px;
            max-width: 600px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: var(--shadow-lg);
        }
        
        .modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
        }
        
        .modal-title {
            font-size: 24px;
            font-weight: 700;
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
            border-radius: 6px;
            transition: all 0.2s;
        }
        
        .close-btn:hover {
            background: var(--bg-hover);
        }
        
        .config-status {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        
        .config-status.success {
            background: #f0fdf4;
            color: #15803d;
        }
        
        .config-status.error {
            background: #fef2f2;
            color: #b91c1c;
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
        }
        
        .badge.absent {
            background: #fee2e2;
            color: #b91c1c;
        }
        
        /* Loading */
        .loading {
            opacity: 0.6;
            pointer-events: none;
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
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-secondary);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar {
                position: fixed;
                left: -280px;
                height: 100vh;
                z-index: 100;
                transition: left 0.3s;
            }
            
            .sidebar.mobile-open {
                left: 0;
            }
            
            .main-body {
                padding: 20px;
            }
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
            
            <div class="search-box">
                <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search tools...">
            </div>
            
            <div class="tools-list" id="toolsList">
                <!-- Tools seront injectés ici -->
            </div>
            
            <div class="sidebar-footer">
                <button class="config-btn" onclick="openConfig()">🔑 Configuration</button>
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
    
    <!-- Modal Config (GÉNÉRIQUE - champs générés dynamiquement) -->
    <div id="configModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">🔑 Configuration</h2>
                <button class="close-btn" onclick="closeConfig()">×</button>
            </div>
            
            <div id="configStatus" class="config-status" style="display: none;"></div>
            
            <!-- Form section remplie dynamiquement par JS -->
            <div class="form-section">
                <p class="form-help" style="text-align: center; color: var(--text-secondary);">
                    Loading configuration...
                </p>
            </div>
            
            <button onclick="saveConfig()" class="execute-btn">💾 Save Configuration</button>
        </div>
    </div>
    
    <script src="/control.js"></script>
</body>
</html>'''
