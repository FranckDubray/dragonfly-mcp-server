// =====================================================
// search.js - Search and filter functionality
// =====================================================

// Initialize search functionality
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        filterTools(query);
    });
}

// Filter tools by search query
function filterTools(query) {
    // Get all category sections
    const categorySections = document.querySelectorAll('.category-section');
    
    categorySections.forEach(section => {
        const tools = section.querySelectorAll('.tool-item');
        let visibleCount = 0;
        
        tools.forEach(item => {
            const toolName = item.querySelector('.tool-name').textContent.toLowerCase();
            
            if (toolName.includes(query)) {
                item.style.display = 'flex';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });
        
        // Hide category if no visible tools
        if (visibleCount === 0) {
            section.style.display = 'none';
        } else {
            section.style.display = 'block';
            
            // Update count in category header
            const countBadge = section.querySelector('.category-count');
            if (countBadge) {
                countBadge.textContent = visibleCount;
            }
        }
    });
}
