
"""
Control UI - sidebar (logo, search, categories container)
Exports: CONTROL_SIDEBAR_HTML
"""

CONTROL_SIDEBAR_HTML = '''
<div class="sidebar">
  <div class="sidebar-header" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color:white; padding:24px 20px; border-bottom:1px solid #0ea5e9;">
    <div class="logo-container" style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
      <img src="https://ai.dragonflygroup.fr/assets/dragonflygroup/mobile-logo.svg?v=20251016-2" alt="Dragonfly" referrerpolicy="no-referrer" crossorigin="anonymous" style="width:28px;height:28px;">
      <div class="logo-text" style="flex:1;">
        <div class="logo" style="font-size:20px; font-weight:700; letter-spacing:-0.02em;">Dragonfly MCP</div>
        <div class="subtitle" style="font-size:11px; opacity:.9; text-transform:uppercase; letter-spacing:.05em; font-weight:500;">Control Panel</div>
      </div>
    </div>
  </div>

  <div class="sidebar-config" style="padding:16px; border-bottom:1px solid #e5e7eb; background:#fafafa;">
    <button class="config-btn" onclick="openConfig()" style="width:100%; padding:10px 16px; background:white; color:#111827; border:1px solid #e5e7eb; border-radius:8px; cursor:pointer; font-size:13px; font-weight:600; display:flex; align-items:center; justify-content:center; gap:6px;">
      ⚙️ Configuration
    </button>
  </div>

  <div class="search-box" style="padding:16px; border-bottom:1px solid #e5e7eb; background:#fafafa;">
    <input id="searchInput" class="search-input" type="text" placeholder="Search tools..." style="width:100%; padding:10px 12px; border:1px solid #e5e7eb; border-radius:8px; font-size:13px; outline:none; background:white;">
  </div>

  <div id="toolsList" class="tools-list" style="flex:1; overflow-y:auto; padding:12px 0; background:#fafafa;"></div>
</div>
'''
