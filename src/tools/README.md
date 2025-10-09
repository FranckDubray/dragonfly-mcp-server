# Tools catalog (src/tools)

This folder contains the MCP tools exposed by the server. Each tool MUST provide:
- A canonical JSON spec file in src/tool_specs/<tool_name>.json (MANDATORY)
- A Python implementation exposing run(...) and spec() (the Python spec() must mirror the JSON)

## Source of truth for specs
- The JSON spec in src/tool_specs/<tool_name>.json is the single source of truth for the OpenAI tool schema.
- The Python spec() should typically load and return that JSON file (do not diverge). If they ever differ, JSON wins.
- Validation: arrays MUST define an `items` schema; parameters MUST be an object.

## Directory‑first tool layout (small files)
- Prefer a package directory per tool with small, focused modules:

  ```
  src/tools/<tool_name>/
    __init__.py        # Thin glue: load spec JSON, expose run()
    api.py             # Input parsing, routing to handlers
    core.py            # Core logic
    validators.py      # Input validation/normalization
    utils.py           # Shared helpers (pure)
    services/          # External I/O (FFmpeg, HTTP, DB), isolated
  ```

- Keep modules small and single‑responsibility. Glue in __init__.py should be minimal (no business logic).
- Security: any file access must be chrooted to the project (no absolute/parent paths). Validate user inputs strictly.

## Available tools (23 complete)

### 🤖 Intelligence & Orchestration

#### **call_llm**
- 2‑step LLM Orchestrator with tool‑calls then final text answer
- Streaming support with usage cumulation across phases
- Configuration: AI_PORTAL_TOKEN, LLM_ENDPOINT

#### **academic_research_super**
- Complete research pipeline: aggregation, scraping, synthesis
- Multiple sources (arXiv, PubMed, etc.)
- Formatted export

#### **script_executor**
- Sandboxed execution of Python scripts orchestrating tools
- Secure isolation
- Runtime context management

### 📧 Communication & Collaboration

#### **imap** ⭐
- Universal IMAP email access (Gmail, Outlook, Yahoo, iCloud, Infomaniak, custom servers)
- **Multi-account support**: separate env vars per provider
  - `IMAP_GMAIL_EMAIL` / `IMAP_GMAIL_PASSWORD`
  - `IMAP_INFOMANIAK_EMAIL` / `IMAP_INFOMANIAK_PASSWORD`
  - etc.
- **13 operations**: connect, list_folders, search_messages, get_message, download_attachments, mark_read/unread (single + batch), move_message (single + batch), mark_spam, delete_message (single + batch)
- **Security**: credentials only in `.env`, never in tool parameters
- Architecture: `_imap/` (presets, connection, operations, parsers, utils)

#### **discord_webhook**
- Complete CRUD with SQLite persistence
- Article publishing (Embeds)
- Automatic content splitting for long messages
- Multiple webhook management
- Architecture: `_discord_webhook/` (db, operations, formatters, validators)

### 🔧 Development & Git

#### **git**
- Unified Git: GitHub API + local Git operations
- **GitHub API**: create_repo, add/delete files, branches, commits, diff, merge, create_release
- **Git local**: status, fetch, pull, rebase, branch_create, checkout, add_paths, commit_all, push, log, remote_info
- **High-level ops**: ensure_repo, config_user, set_remote, sync_repo
- Security: chroot operations to project root
- Conflict detection with helpful hints
- Architecture: `_git/` (gh_ops, local_ops, chroot, high_level)

#### **gitbook**
- GitBook discovery and search
- Automatic site discovery
- Full-text search
- Content extraction
- Architecture: `_gitbook/` (discovery, search, extraction, parsers, utils)

### 🗄️ Databases & Storage

#### **sqlite_db**
- SQLite in `<project>/sqlite3` chroot
- Secure query execution
- Transaction support
- Validated DB names

### 📄 Documents & PDF

#### **pdf_download** 🆕
- **Download PDFs from URLs** to `docs/pdfs`
- HTTP/HTTPS with timeout control (5-300s)
- **PDF validation** (magic bytes `%PDF-`)
- **Automatic unique filenames** (suffixes `_1`, `_2`, etc.)
- Optional overwrite mode
- Filename extraction from URL
- Architecture: `_pdf_download/` (api, core, validators, utils, services/downloader)

#### **pdf_search**
- Keyword search in PDF files
- Context extraction
- Multi-page support

#### **pdf2text**
- PDF to text conversion
- Structure preservation
- Batch support

#### **universal_doc_scraper**
- Intelligent content extraction from web pages
- Multi-format support
- Automatic cleanup
- Architecture: `_universal_doc/` (scraper, parsers, cleaners)

### 🎬 Media & YouTube

#### **youtube_search** 🆕 ⭐
- **Search YouTube content via YouTube Data API v3** (official)
- **3 operations**:
  - `search`: Find videos/channels/playlists by keyword with filters (order, type, region, safe search)
  - `get_video_details`: Get detailed info (title, description, views, likes, comments, duration, tags, thumbnails)
  - `get_trending`: Get trending videos by region and category
- **Free API key**: 10,000 units/day (100 units per search = ~100 searches/day)
- **Advanced filters**: order (relevance, viewCount, date, rating, title), search type (video, channel, playlist), region code, safe search
- **Complete workflow**: youtube_search → youtube_download → video_transcribe
- **Use cases**: Find content before downloading, research trending topics, get metadata without downloading
- Architecture: `_youtube_search/` (api, core, validators, services/youtube_api)

#### **youtube_download** 🆕 ⚡
- **Download videos/audio from YouTube URLs**
- **Media types**: audio (MP3, perfect for transcription), video (MP4), both (separate files)
- **Quality options**: best, 720p, 480p, 360p
- **Operations**:
  - `download`: Download media to `docs/video/`
  - `get_info`: Get metadata without downloading
- **Features**:
  - URL validation (all YouTube formats supported)
  - Automatic filename sanitization
  - Unique naming (_1, _2 if file exists)
  - Duration check (avoids massive downloads)
  - Metadata extraction (title, duration, uploader, views)
- **Workflow**: YouTube → Audio → video_transcribe → Exploitable text
- **Security**: chroot to `docs/video/`, URL validation, duration limits
- Architecture: `_youtube_download/` (api, core, validators, utils, services/downloader)

#### **video_transcribe** 🆕 ⚡
- **Extract audio from video and transcribe using Whisper API**
- **Parallel processing**: up to 3 chunks simultaneously (3x faster)
- **Performance**: 3 minutes video → 20 seconds transcription
- **Direct extraction**: FFmpeg extracts audio segments on-the-fly (no persistent temp files)
- **Whisper API**: multipart/form-data upload with Bearer token
- **Time-based segmentation**: `time_start`/`time_end` for large videos
- **Configurable chunking**: `chunk_duration` (default 60s)
- **Returns JSON**: segments with timestamps + full_text + metadata
- **Operations**:
  - `transcribe`: Extract audio + Whisper transcription
  - `get_info`: Video metadata (duration, audio codec)
- **Security**: chroot to `docs/video/`, automatic cleanup of temp files
- Architecture: `_video_transcribe/` (api, core, audio_extractor, whisper_client, validators, utils)

#### **ffmpeg_frames**
- Extract images/frames from video via FFmpeg
- **Native PyAV shot detection** (frame-by-frame)
- Moving average + hysteresis + NMS + refinement
- Per-frame debug: time, diff, similarity%
- High precision on compressed videos (YouTube-like)
- Export: images + timestamps + debug.json
- Architecture: `_ffmpeg/` (detect, native, utils)

### ✈️ Aviation & Transport

#### **flight_tracker** ⭐
- **Real-time aircraft tracking** via OpenSky Network API
- **Track flights** by position (lat/lon) + radius (1-500 km)
- **Filters**: altitude min/max, speed min/max, on_ground/in_flight, countries, callsign pattern
- **Automatic flight phase detection**: cruise, climb, descent, approach, final_approach, landing_imminent
- **Sort by**: distance, altitude, speed, callsign
- **Returns**: position, speed, heading, vertical rate, country (registration), squawk, last contact
- **No authentication** required (public API)
- Architecture: `_flight_tracker/` (api, core, validators, utils, services/opensky)

#### **aviation_weather** ⭐
- **Upper air weather data** via Open-Meteo API (free, no API key)
- **2 operations**:
  - `get_winds_aloft`: Wind speed, direction, and temperature at specific altitude/coordinates
  - `calculate_tas`: Calculate True Airspeed from ground speed and wind
- **All flight levels**: 1000-20000m (FL30-FL650)
- **Automatic conversions**: km/h ↔ knots, meters ↔ feet, °C ↔ °F
- **Wind components**: headwind/tailwind, crosswind
- **Use cases**: Explain aircraft speed records, flight planning, performance analysis
- Architecture: `_aviation_weather/` (api, core, validators, utils, services/openmeteo)

#### **velib** 🆕
- **Vélib' Métropole Paris bike-sharing data**
- SQLite cache for ~1494 stations (static data)
- Real-time availability API (bikes mechanical/electric, docks free)
- 3 operations: `refresh_stations`, `get_availability`, `check_cache`
- Integration with `sqlite_db` tool for complex searches
- Open Data API (no authentication required)
- Architecture: `_velib/` (api, core, db, fetcher, validators, utils)

### 🔢 Calcul & Math

#### **math**
- **Numerical**: arithmetic, trig, log, exp, sqrt
- **High-precision**: mpmath for large precision
- **Symbolic**: derivatives, integrals, simplification (sympy)
- **Linear algebra**: matrices, vectors, eigenvalues, SVD, LU, QR
- **Probabilities**: stats, distributions (normal, Poisson, binomial, etc.)
- **Polynomials**: roots, factorization
- **Solvers**: equations, systems, optimization
- **Number theory**: nth_prime, factorization, Euler phi
- **Series**: finite/infinite sums, products
- Architecture: `_math/` (dispatcher, basic, symbolic, proba, linalg, hp, etc.)

#### **date**
- Date/time helpers
- Operations: now, today, diff, add, format, parse, weekday, week_number
- Timezone aware
- Multiple formats

### 🌐 Networking & API

#### **http_client** 🆕
- **Universal REST/API client**
- All HTTP methods: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- Authentication: Basic, Bearer, API Key
- Body formats: JSON, Form data, Raw text/XML
- Advanced features: Retry with backoff, Proxy, Timeout (up to 600s), SSL verification
- Response parsing: auto-detect, JSON, text, raw
- Optional response saving
- Architecture: `_http_client/` (api, core, auth, retry, validators, utils)

### 🌐 Social Media

#### **reddit_intelligence**
- Reddit scraping and analysis
- Post/comment extraction
- Sentiment analysis
- Trending topics
- Architecture: `_reddit/` (scraper, analyzer, parsers, utils)

---

## Spec JSON location and naming
- Location: src/tool_specs/<tool_name>.json
- The `function.name` must match the Python tool package/module name exposed by the server.
- Example Python adapter to load JSON spec:

  ```python
  def spec():
      import json, os
      here = os.path.dirname(__file__)
      spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', '<tool_name>.json'))
      with open(spec_path, 'r', encoding='utf-8') as f:
          return json.load(f)
  ```

## Adding a new tool (required steps)
1) Create src/tools/<tool_name>/ as a package with __init__.py exposing run() and spec().
2) Add src/tool_specs/<tool_name>.json (MANDATORY) describing the OpenAI function schema.
3) Implement small modules under src/tools/<tool_name>/ (api.py, core.py, validators.py, utils.py, services/*).
4) Enforce security (sandbox, path validations) and explicit errors (no generic 500s).
5) Start the server and GET /tools to see the tool registered.

## Notes
- Tests and examples are recommended but kept outside the repo's ignored data paths (e.g., not under docs/ unless explicitly whitelisted).
- Do not commit user data or runtime outputs; use chrooted, ignored folders.
