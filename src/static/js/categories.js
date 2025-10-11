// =====================================================
// categories.js - Category definitions and grouping
// =====================================================

// Category metadata (order, emoji, label)
const CATEGORIES = [
    { key: 'intelligence', emoji: '🤖', label: 'Intelligence & AI' },
    { key: 'development', emoji: '🔧', label: 'Development & Automation' },
    { key: 'communication', emoji: '💬', label: 'Communication & Social' },
    { key: 'data', emoji: '📊', label: 'Data & Documents' },
    { key: 'media', emoji: '🎬', label: 'Media & Content' },
    { key: 'infrastructure', emoji: '🌐', label: 'Infrastructure & Real-Time' }
];

// Group tools by category
function groupToolsByCategory(tools) {
    const grouped = {};
    
    // Initialize all categories
    CATEGORIES.forEach(cat => {
        grouped[cat.key] = [];
    });
    
    // Assign tools to categories
    tools.forEach(tool => {
        try {
            const spec = JSON.parse(tool.json);
            const category = spec.function.category || 'infrastructure'; // fallback
            
            if (grouped[category]) {
                grouped[category].push(tool);
            } else {
                console.warn(`Unknown category "${category}" for tool ${tool.name}`);
                grouped['infrastructure'].push(tool);
            }
        } catch (e) {
            console.error(`Failed to parse spec for tool ${tool.name}:`, e);
        }
    });
    
    return grouped;
}

// Get category metadata by key
function getCategoryMeta(key) {
    return CATEGORIES.find(c => c.key === key) || { key, emoji: '🔧', label: key };
}
