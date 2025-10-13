# Changelog - v1.19.0 to v1.21.1

Releases history from v1.19.0 to v1.21.1 (archived from GitHub releases).

---

## [v1.21.1] - 2025-10-12 - Discord Bot Output Cleanup

### Improved
- **discord_bot**: Massively reduced output verbosity
  - Default limit reduced from 20 to **5 messages** (max remains 50)
  - Aggressive cleaning of null/useless fields (banner, accent_color, avatar_decoration_data, collectibles, display_name_styles, public_flags, flags, components, placeholder, content_scan_version, etc.)
  - Removed empty arrays and null values from response
  - Cleaned user objects: only id, username, global_name, avatar, bot, discriminator (if != "0")
  - Cleaned attachments: only filename, size, url, content_type, width, height
  - Cleaned reactions: only emoji name + count (no burst/me flags)
  - Cleaned threads: only id, name, message_count
  - **Impact**: Output size reduced by ~60-70% for typical messages
  - **Rationale**: Protect LLM context from flooding with metadata noise

### Technical Details
- utils.py: New `_remove_null_fields()` recursive cleaner
- ops_messages.py: `limit` default changed from 20 to 5
- All cleaning functions rewritten for maximum efficiency
- Backward compatible: All essential data preserved

---

## [v1.18.0] - 2025-10-12 - News Aggregator Multi-Sources

### Added
- **news_aggregator** tool with 3 providers
- Parallel query execution (ThreadPoolExecutor - 60% faster)
- Unified article format
- Deduplication + sorting by date
- Pagination support
- Anti-flood protections

### Highlights
**3 Providers** (parallel queries):
- 📰 **NewsAPI**: 100 req/day, 150k+ sources, top headlines only (free tier)
- 📰 **New York Times**: 1000 req/day, complete archive, advanced search
- 📰 **The Guardian**: ~500 req/day, archive since 1999, full content

**Total quotas**: ~1600 requests/day combined

### Operations
- ✅ **search_news**: Multi-criteria search (keywords, dates, language)
- ✅ **top_headlines**: Current news by country/category
- ✅ **list_sources**: Available sources by language/country

### Intelligence
- 🔄 **Parallel queries**: ThreadPoolExecutor (3s vs 9s sequential)
- 🔍 **Deduplication**: Automatic by URL
- 📅 **Sorting**: By date (newest first)
- 📄 **Pagination**: `page` parameter functional
- 🌐 **Unified format**: Cross-provider normalization

### Anti-flood LLM (LLM_DEV_GUIDE compliant)
- ✅ Limit default: 20 articles, max: 100
- ✅ Descriptions: 300 chars max
- ✅ Provider metasimplified (concise status)
- ✅ Sources list: 100 max
- ✅ Worst case: ~15k tokens (8.5x under GPT-4 limit)

### Configuration
```bash
# Get API keys (all free):
NEWS_API_KEY=your_key_here
NYT_API_KEY=your_key_here
GUARDIAN_API_KEY=your_key_here
```

**Important**: NewsAPI free tier supports ONLY `top_headlines` (not `search_news`). Use NYT or Guardian for keyword search.

---

## [v1.17.3] - 2025-10-12 - Ollama Vision Simplified & Output Cleanup

### Highlights

#### Vision Support Simplified
- ✅ **`operation=generate`** is THE way to use images with Ollama
- ❌ **`operation=chat`** explicitly rejects images with helpful error message
- 🔧 Removed broken auto-switch logic (was confusing and non-functional)
- 📸 Tested with **llava:13b** on local images under `docs/`

#### Output Cleanup (70% token reduction)
- 🧹 Removed `context` array (internal tokens - pollution)
- 🧹 Removed raw duration fields (nanoseconds)
- ✅ Keep only 6 essential fields: `success`, `response`/`message`, `model`, `timing`, token counts
- ⏱️ Human-readable durations: `"12.3s"` instead of `12345678901`

### Fixed
- **ollama_local**: Vision support clarified
  - `generate` = images OK ✅
  - `chat` = text only, rejects images with actionable error
- **ollama_local**: Massive output cleanup for LLM token efficiency
  - Before: 15+ fields including internal state
  - After: 6 essential fields
  - ~70% fewer tokens per response

### Breaking Change
- `operation=chat` no longer accepts `image_files` or `image_urls`
- **Migration:** Use `operation=generate` for image analysis

---

## [v1.17.2] - 2025-10-12 - Critical fixes for call_llm and ollama_local

### Critical Fixes

#### call_llm - Image path resolution
- **Fixed**: Hardcoded `/docs` (system root) causing "file not found" errors
- **Now**: Dynamic path resolution using `Path(__file__).parent.parent.parent`
- Images under `docs/` now correctly accessible without DOCS_ABS_ROOT env var
- Support for `DOCS_ABS_ROOT` override maintained for custom setups

#### ollama_local - Massive log flooding
- **Fixed**: `pull_model` and `push_model` returning 500-2000 lines of progress logs
- **Now**: Concise summaries (5-8 lines) with aggregated progress
- New `_handle_streaming_response()` function filters streaming output
- Output reduction: **98-99.6%** 🎉
- Includes download summary with layer count, total size, and completion percentage
- Prevents LLM context window saturation and improves token efficiency

### Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| call_llm images | ❌ File not found | ✅ Works perfectly | 100% |
| ollama pull_model output | 500-2000 lines | 5-8 lines | 98-99.6% reduction |
| LLM context saturation | ❌ Flooded | ✅ Clean | Token cost ÷ 100 |

---

## [v1.17.1] - 2025-10-11 - Changelog housekeeping + tool cleanup

### Changes
- Remove finnhub tool (insufficient free-tier coverage for Euronext)
- Remove FINNHUB_API_KEY from .env.example
- README back to 37 tools
- Start changelog archival strategy (keep latest at root; archive older entries under changelogs/)
- Remove stray archived changelog placeholder

No tool behavior changes for existing endpoints.

---

## [v1.17.0] - 2025-10-11 - Trivia API

### Added
**trivia_api** - Complete Open Trivia Database API access

**6 Operations:**
- `get_questions` - Get trivia questions with advanced filters
- `list_categories` - Browse 24 available categories
- `get_category_count` - Question counts by difficulty level
- `get_global_count` - Global database statistics
- `create_session_token` - Generate token to avoid duplicate questions
- `reset_session_token` - Reset token to replay all questions

**24 Categories:**
General Knowledge, Science, History, Sports, Entertainment (Books, Film, Music, TV, Video Games, Board Games, Comics, Anime), Mythology, Geography, Politics, Art, Celebrities, Animals, Vehicles, and more!

**Key Features:**
- ✅ **100% FREE** - No API key required, unlimited access
- ✅ **Multiple choice** and **true/false** questions
- ✅ **Session token management** - Avoid duplicate questions in quizzes
- ✅ **Automatic rate limit handling** - 5s retry on 429 errors
- ✅ **Multiple encoding support** - base64, url3986, urlLegacy with automatic decoding
- ✅ **HTML entity decoding** - Clean special characters
- ✅ **Shuffled answers** - Correct answer index provided for quiz validation
- ✅ **Question counts** - By category and difficulty level

### Architecture
Complete implementation following Dragonfly standards:
- `_trivia_api/` package (api, core, validators, utils, services/api_client)
- Comprehensive error handling and validation
- Rate limiting with automatic retry
- Clean separation of concerns

**Category**: entertainment  
**Tags**: quiz, games, educational, trivia

---

## Summary (v1.19.0 to v1.21.1)

- **5 major releases**
- **Key additions**: News aggregator (3 providers), Trivia API (24 categories)
- **Critical fixes**: Ollama output cleanup (98% reduction), call_llm image paths
- **Output optimizations**: Discord bot (-60%), Ollama vision clarified
- **Total tools**: 37 (at v1.17.1 cleanup)
