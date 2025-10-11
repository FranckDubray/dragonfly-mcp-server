// =====================================================
// categories.js - Canonical categories and grouping
// =====================================================

// Canonical category metadata (order, emoji, label)
const CATEGORIES = [
  { key: 'intelligence',   emoji: '📊', label: 'Intelligence & Orchestration' },
  { key: 'development',    emoji: '🔧', label: 'Development' },
  { key: 'communication',  emoji: '📧', label: 'Communication' },
  { key: 'data',           emoji: '🗄️', label: 'Data & Storage' },
  { key: 'documents',      emoji: '📄', label: 'Documents' },
  { key: 'media',          emoji: '🎬', label: 'Media' },
  { key: 'transportation', emoji: '✈️', label: 'Transportation' },
  { key: 'networking',     emoji: '🌐', label: 'Networking' },
  { key: 'utilities',      emoji: '🔢', label: 'Utilities' },
  { key: 'entertainment',  emoji: '🎮', label: 'Social & Entertainment' },
];

// Build fast lookup set of valid keys
const VALID_CATEGORY_KEYS = new Set(CATEGORIES.map(c => c.key));

// Group tools by canonical category
function groupToolsByCategory(tools) {
  const grouped = {};
  // Initialize all categories empty
  CATEGORIES.forEach(cat => { grouped[cat.key] = []; });

  tools.forEach(tool => {
    try {
      const spec = JSON.parse(tool.json);
      let category = (spec?.function?.category || '').trim();
      if (!VALID_CATEGORY_KEYS.has(category)) {
        // Fallback: bucket unknown into 'utilities' (never 'infrastructure')
        category = 'utilities';
      }
      grouped[category].push(tool);
    } catch (e) {
      // If spec parse fails, bucket into utilities as a safe default
      grouped['utilities'].push(tool);
    }
  });

  // Return grouped object (each array can be sorted by caller)
  return grouped;
}

// Get category metadata by key
function getCategoryMeta(key) {
  return CATEGORIES.find(c => c.key === key) || { key, emoji: '🧰', label: key };
}
