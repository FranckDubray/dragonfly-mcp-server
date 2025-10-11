// =====================================================
// search.js - Text search only (tags removed)
// =====================================================

// Initialize text search input: filters tool list by query
function initSearch() {
  const searchInput = document.getElementById('searchInput');
  if (!searchInput) return;
  searchInput.addEventListener('input', (e) => {
    renderToolsList(e.target.value);
  });
}
