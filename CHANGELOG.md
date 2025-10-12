# Changelog

All notable changes to this project will be documented in this file.

Note: Older entries have been archived under changelogs/ (range-based files).

---

## [1.19.0] - 2025-10-12

### Fixed
- **generate_edit_image**: Critical fix for stream mode handling
  - Fixed 404 error caused by inconsistent payload (stream=true with non-streaming request)
  - `_single_call()` now explicitly sets stream=false for non-stream attempts
  - Fallback correctly uses stream=true as expected by backend
  - Both generate and edit operations now work reliably

### Added
- **generate_edit_image**: Local file support for image inputs (completed)
  - New `image_files` parameter: accepts local image paths relative to `./docs`
  - Examples: `"test.png"`, `"images/photo.jpg"`, `"subdir/image.webp"`
  - Supports PNG, JPEG, WebP with automatic MIME type detection
  - Can be combined with `images` parameter (URLs/data URLs) — max 3 total
  - Intelligent path resolution using same strategy as `call_llm`
  - Security: Path traversal protection (chroot to ./docs)
  - Optional `DOCS_ABS_ROOT` env var override

### Changed
- **Changelog management**: Implemented rotation policy
  - Archived versions 1.14.3 to 1.18.2 in `changelogs/CHANGELOG_1.14.3_to_1.18.2.md`
  - Root CHANGELOG.md now contains only latest release (1.19.0)
  - Follows LLM_DEV_GUIDE archival strategy (keep latest 10 versions at root)

### Technical Details
- generate_edit_image: validators.py enhanced with local file loading
  - `load_local_images()`: reads files from ./docs and converts to data URLs
  - `_get_docs_root()`: intelligent project root detection
  - Path resolution: `Path(__file__).parent.parent.parent.parent / "docs"`
  - Error handling: clear messages for missing files, path traversal attempts
- Total improvements since 1.18.0:
  - Code complexity reduced by 36% (403 → 259 lines in core.py)
  - Debug payload reduced by 80% (40KB → 8KB)
  - 3 input types supported: local files, URLs, data URLs/base64
  - Backward compatible with all existing integrations

---

For older versions, see: [changelogs/](changelogs/) (range-based archives).
