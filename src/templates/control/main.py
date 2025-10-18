
"""
Control UI - main area (status bar + main view container)
Exports: CONTROL_MAIN_HTML
"""

CONTROL_MAIN_HTML = '''
<div class="main-content">
  <div class="main-header">
    <div id="statusBar" class="status-bar">🔧 Ready</div>
  </div>
  <div class="main-body">
    <div id="mainView" class="tool-view">
      <div class="empty-state" style="text-align:center; padding:80px 20px; color:#6b7280;">
        <div class="empty-state-icon" style="font-size:64px; margin-bottom:16px; opacity:.3;">🧰</div>
        <div class="empty-state-text" style="font-size:16px; font-weight:500;">Select a tool to begin</div>
      </div>
    </div>
  </div>
</div>
'''
