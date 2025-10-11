// =====================================================
// main.js - Main initialization and auto-reload
// =====================================================

// Initialize application on DOM load
document.addEventListener('DOMContentLoaded', () => {
    // Hide tag bar completely (feature removed)
    const tagsBox = document.querySelector('.tags-box');
    if (tagsBox) tagsBox.style.display = 'none';

    // Load tools on start
    loadTools();
    
    // Initialize search
    initSearch();
});

// Auto-reload tools (check every 5s)
setInterval(async () => {
    try {
        const response = await fetch('/tools', { method: 'HEAD' });
        const newETag = response.headers.get('ETag');
        
        if (newETag && newETag !== currentETag) {
            const loadResponse = await fetch('/tools');
            if (loadResponse.ok) {
                const newTools = await loadResponse.json();
                
                // Check if tools changed
                if (newTools.length !== tools.length || 
                    JSON.stringify(newTools.map(t => t.name).sort()) !== 
                    JSON.stringify(tools.map(t => t.name).sort())) {
                    tools = newTools;
                    renderToolsList();
                    updateStatus(`🔄 Auto-reloaded ${tools.length} tools`, 'success');
                }
            }
            currentETag = newETag;
        }
    } catch (error) {
        // Silent fail for background refresh
        console.log('Auto-reload check failed:', error);
    }
}, 5000);
