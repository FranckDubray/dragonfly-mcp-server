// =====================================================
// search.js - Search and filter functionality (with tags)
// =====================================================

const TAGS = [
  { key: 'external_sources', label: 'External knowledge' },
  { key: 'knowledge', label: 'Knowledge' },
  { key: 'social', label: 'Social' },
  { key: 'scraping', label: 'Scraping' },
  { key: 'docs', label: 'Docs' },
  { key: 'search', label: 'Search' },
  { key: 'api', label: 'API' },
  { key: 'video', label: 'Video' },
  { key: 'pdf', label: 'PDF' },
];

let activeTag = null;

function initSearch() {
  const searchInput = document.getElementById('searchInput');
  searchInput.addEventListener('input', (e) => {
    renderToolsList(e.target.value);
  });

  // Build tag bar
  const tagBar = document.getElementById('tagBar');
  tagBar.innerHTML = '';

  // All tag
  const allChip = document.createElement('div');
  allChip.className = 'tag-chip active';
  allChip.textContent = 'All';
  allChip.onclick = () => {
    activeTag = null;
    document.querySelectorAll('.tag-chip').forEach(c => c.classList.remove('active'));
    allChip.classList.add('active');
    renderToolsList(document.getElementById('searchInput').value);
  };
  tagBar.appendChild(allChip);

  TAGS.forEach(t => {
    const chip = document.createElement('div');
    chip.className = 'tag-chip';
    chip.textContent = t.label;
    chip.onclick = () => {
      activeTag = t.key;
      document.querySelectorAll('.tag-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      renderToolsList(document.getElementById('searchInput').value);
    };
    tagBar.appendChild(chip);
  });
}

// Inject tag filtering into render flow by wrapping the global function safely
(function wrapGroupByCategoryForTags() {
  const __orig_group = window.groupToolsByCategory; // capture the original defined in categories.js
  if (typeof __orig_group !== 'function') return; // safety
  window.groupToolsByCategory = function(toolsList) {
    let filtered = toolsList;
    if (activeTag) {
      filtered = toolsList.filter(t => {
        try {
          const spec = JSON.parse(t.json);
          const tags = spec?.function?.tags || [];
          return Array.isArray(tags) && tags.includes(activeTag);
        } catch { return false; }
      });
    }
    return __orig_group(filtered);
  };
})();
