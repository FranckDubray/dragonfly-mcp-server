
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

## Available tools (29 complete)

### 🤖 Intelligence & Orchestration

#### **call_llm**
- 2‑step LLM Orchestrator with tool‑calls then final text answer
- Streaming support with usage cumulation across phases
- Configuration: AI_PORTAL_TOKEN, LLM_ENDPOINT

#### **ollama_local** ⭐🆕
- Interface complète avec Ollama local (localhost:11434) + recherche web cloud
- **15 opérations**: list_models, get_version, get_running_models, show_model, pull_model, push_model, create_model, copy_model, delete_model, generate, chat, embeddings, web_search, chat_with_web
- **Local**: Gestion modèles, chat contextuel, génération, embeddings (pas de token requis)
- **Cloud**: Recherche web enrichie via ollama.com/api/web_search (token: OLLAMA_WEB_SEARCH_TOKEN)
- **Hybride**: chat_with_web (recherche web → contexte local)
- **Streaming**: Support pour generate et chat
- **Métriques**: Durées formatées, tailles GB, métadonnées enrichies
- Architecture: `_ollama_local/` (api, core, validators, utils, services/local_client, services/web_search_client)

#### **academic_research_super**
- Complete research pipeline: aggregation, scraping, synthesis
- Multiple sources (arXiv, PubMed, etc.)
- Formatted export

#### **script_executor**
- Sandboxed execution of Python scripts orchestrating tools
- Secure isolation
- Runtime context management

### 📧 Communication & Collaboration

#### **email_send** ⭐🆕
- Send emails via SMTP (Gmail or Infomaniak)
- **Reuses IMAP credentials**: `IMAP_<PROVIDER>_EMAIL`, `IMAP_<PROVIDER>_PASSWORD`
- **SMTP servers hardcoded**: Gmail (smtp.gmail.com:587), Infomaniak (mail.infomaniak.com:587)
- **2 operations**: send (send email), test_connection (test SMTP credentials)
- **Features**: text/HTML body, CC/BCC, attachments (10 max, 25MB), reply-to, from_name, priority
- **No extra dependencies**: smtplib is built-in Python
- Architecture: `_email_send/` (api, core, validators, services/smtp_client)

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

#### **excel_to_sqlite** 🆕⭐
- **Import Excel (.xlsx) data into SQLite databases**
- **5 operations**:
  - `import_excel`: Import complete Excel sheet into SQLite table
  - `preview`: Preview data with type detection (no insertion)
  - `get_sheets`: List all sheets in Excel file
  - `validate_mapping`: Validate column mapping before import
  - `get_info`: Get file metadata and sheet information
- **Features**:
  - **Automatic schema detection**: Infers INTEGER, REAL, TEXT, BLOB types
  - **Column name sanitization**: Converts to SQL-safe names
  - **Batch processing**: 100-10000 rows per batch (default 1000)
  - **Manual column mapping**: Override auto-detected column names
  - **Type forcing**: Force specific columns to INTEGER/REAL/TEXT/BLOB
  - **Skip rows**: Skip N rows at beginning (e.g., skip headers)
  - **Custom header row**: Use different row as column names (default 0)
  - **Table behaviors**: replace (overwrite), append (add rows), fail (error if exists)
- **Chroot**: Excel files from project root, SQLite DBs in `<project>/sqlite3/`
- **Dependencies**: pandas (data manipulation), openpyxl (Excel engine)
- **Preview mode**: Test import with type detection, see first N rows (max 100)
- **Validation**: Check column compatibility before actual import
- **Use cases**:
  - Import spreadsheet data into SQLite for querying with sqlite_db
  - ETL workflows: Excel → SQLite → analysis/transformation
  - Data migration from Excel to structured databases
  - Bulk data import with automatic schema inference
- Architecture: `_excel_to_sqlite/` (api, core, validators, excel_reader)

#### **sqlite_db**
- SQLite in `<project>/sqlite3` chroot
- Secure query execution
- Transaction support
- Validated DB names

### 📄 Documents & PDF

#### **office_to_pdf** 🆕⭐
- **Convert Office documents to PDF** using native Office suite installed on laptop
- **Formats supported**: Word (.docx, .doc), PowerPoint (.pptx, .ppt)
- **Engine**: docx2pdf library leveraging native Office apps
  - macOS: Microsoft Word/PowerPoint via AppleScript
  - Windows: Microsoft Word/PowerPoint via COM automation
- **Operations**:
  - `convert`: Convert Office file to PDF
  - `get_info`: Get file metadata without converting
- **Features**:
  - Input chroot: `docs/office/`
  - Output chroot: `docs/pdfs/`
  - Auto-generated output names
  - Unique naming (_1, _2 if file exists)
  - Overwrite option
- **Dependencies**: docx2pdf (included in pyproject.toml)
- **Test verified**: Successfully converted Word → PDF (90KB → 60KB)
- Architecture: `_office_to_pdf/` (api, core, validators, utils, services/office_converter)

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
- **Advanced filters**:
  - `channel_id`: Filter to specific channel (get latest videos from channel)
  - `order`: date (chronological), viewCount, relevance, rating, title
  - `published_after` / `published_before`: Filter by date range (ISO 8601)
- **Free API key**: 10,000 units/day (100 units per search = ~100 searches/day)
- **Complete workflow**: youtube_search → youtube_download → video_transcribe
- **Use cases**: Find content before downloading, research trending topics, get metadata without downloading, find latest videos from specific channel
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
- **Returns JSON**: segments with timestamps + full_text + metadata + **timing**
- **Timing metrics**: processing_time_seconds, processing_time_formatted, started_at, completed_at, average_time_per_second
- **Operations**:
  - `transcribe`: Extract audio + Whisper transcription (returns timing)
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

#### **ship_tracker** ⭐
- **Real-time vessel tracking** via AISStream.io WebSocket API
- **3 operations**:
  - `track_ships`: Find ships in geographic area with filters
  - `get_ship_details`: Get detailed ship info by MMSI
  - `get_port_traffic`: Monitor traffic near major ports
- **Filters**: ship type, size, speed, navigation status
- **Ports**: Rotterdam, Singapore, Le Havre, Hamburg, Marseille, etc.
- **Timeout**: 3-60s (controls data collection duration)
- **No authentication** required (free API with API key)
- Architecture: `_ship_tracker/` (api, core, validators, utils, services/aisstream)

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

### ♟️ Chess

#### **chess_com** ⭐🆕
- **Complete Chess.com public API access** (no authentication required)
- **24 operations** covering all public endpoints:

**Players (9 ops)**:
- `get_player_profile`: Public profile (title, rating, country, etc.)
- `get_player_stats`: Statistics by game type (blitz, bullet, rapid, daily)
- `get_player_games_current`: Ongoing games
- `get_player_games_archives_list`: Available monthly archives
- `get_player_games_archives`: Games from specific month
- `get_player_clubs`: Clubs player is member of
- `get_player_matches`: Team matches player participated in
- `get_player_tournaments`: Current tournaments
- `get_titled_players`: List by title (GM, IM, FM, etc.)

**Clubs (3 ops)**:
- `get_club_details`: Club information
- `get_club_members`: Members list
- `get_club_matches`: Team matches

**Tournaments (3 ops)**:
- `get_tournament_details`: Tournament info
- `get_tournament_round`: Specific round details
- `get_tournament_round_group`: Specific group in round

**Countries (3 ops)**:
- `get_country_details`: Country information
- `get_country_players`: Players from country
- `get_country_clubs`: Clubs from country

**Matches (2 ops)**:
- `get_match_details`: Team match details
- `get_match_board`: Specific board from match

**Leaderboards (1 op)**:
- `get_leaderboards`: Global rankings by category

**Puzzles (2 ops)**:
- `get_daily_puzzle`: Daily puzzle
- `get_random_puzzle`: Random puzzle

**Streamers (1 op)**:
- `get_streamers`: Live streamers list

**Features**:
- Rate limiting: 100ms delay between requests (configurable)
- User-Agent: Required by Chess.com API (included)
- Error handling: Detailed HTTP error messages
- No authentication: All endpoints are public
- Data formats: JSON-LD, PGN, FEN

**Use cases**:
- Player analysis and statistics
- Game archives and analysis
- Club management and monitoring
- Tournament tracking
- Leaderboard research
- Training with puzzles
- Live streaming discovery

**Configuration** (optional):
```bash
CHESS_COM_RATE_LIMIT_DELAY=0.1  # Delay between requests (seconds)
```

Architecture: `_chess_com/` (api, core, validators, utils, services/chess_client)

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
