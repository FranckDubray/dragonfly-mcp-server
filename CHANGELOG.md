
















# Changelog

All notable changes to this project will be documented in this file.

---

## [Unreleased]

### Removed
- Control panel (/control): removed non-working tag filters (chips) and tag bar entirely
  - Tags are no longer displayed, used, or loaded in the UI
  - HTML markup for tags box removed from ui_html.py
  - JavaScript tag filtering logic removed from search.js
- Tool list sidebar: removed technical name badge for cleaner appearance
  - Technical name still visible in detailed tool view header

### Changed
- Control panel search simplified to text-only filtering
  - Clean text search across tool names and categories
  - No tag chips, no complex filtering UI
- UI/UX improvements for category and tool distinction
  - Category headers: bolder typography, gradient backgrounds, left border accent, shadow
  - Tool items: white background, subtle indent, smooth hover animations
  - Clear visual hierarchy: categories stand out, tools clearly nested
- Complete design overhaul to match portal branding
  - Primary color: green (#10b981) matching portal badges
  - Header: gradient green background with Dragonfly emoji (🐉)
  - Clean white/light gray color scheme (#fafafa, #ffffff)
  - Soft shadows and subtle borders throughout
  - Modern card-based layout with professional spacing
  - Typography and transitions aligned with portal aesthetic

---

## [1.14.2] - 2025-10-11

### Added
- UI (/control) tag filters for external knowledge tools (chips): `external_sources`, `knowledge`, `social`, `scraping`, `docs`, `search`, `api`, `video`, `pdf`.
- Tags in tool specs for external knowledge cluster:
  - academic_research_super: [knowledge, research, external_sources]
  - reddit_intelligence: [social, knowledge, scraping, external_sources]
  - gitbook: [knowledge, docs, search]

### Fixed
- sqlite_db category explicitly set to `data`.
- discord_webhook category consistently set to `communication` in JSON and Python spec_def.

### Changed
- LLM_DEV_GUIDE.md clarifies use of `tags` to mark external knowledge base tools while keeping the 10 canonical categories unchanged.
- README updated: control panel UX notes and canonical categories fully reflected.

---

## [1.14.1] - 2025-10-11

### Fixed
- Categories alignment across all tools — enforced the 10 canonical categories in all JSON specs
  - math, date → utilities
  - http_client → networking
  - ship_tracker → transportation (and added `timeout.default: 10`)
  - velib → transportation (was "infrastructure")
  - pdf_download, pdf_search, pdf2text, office_to_pdf, universal_doc_scraper → documents
  - generate_edit_image → media (category added)
- UI (/control): professional ergonomics improvements
  - Clear separation of categories vs tools
  - Categories are collapsed by default (clean overview)
  - Favorites (★/☆) with persistence
  - Category badges in tool header, technical name badge
  - Keyboard shortcuts: `/` focus search, Ctrl/Cmd+Enter execute
  - Last selected tool restored

### Changed
- README.md and src/tools/README.md updated to reflect the exact 10 canonical categories
- LLM_DEV_GUIDE.md clarified: categories are mandatory, must be chosen from the 10 canonical keys; UI label for `entertainment` is "Social & Entertainment"

---

## [1.14.0] - 2025-01-11

### Added
- **chess_com** tool: Complete Chess.com public API access (no authentication required)
  - **24 operations** covering all public endpoints
  - ...


 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
