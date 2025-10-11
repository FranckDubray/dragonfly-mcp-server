













































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

## Available tools (30 complete)

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
- Import Excel (.xlsx) data into SQLite databases
- 5 operations: import_excel, preview, get_sheets, validate_mapping, get_info
- Features: schema detection, sanitization, batch insert, type forcing
- Chroot: project/sqlite3/
- Dependencies: pandas, openpyxl
- Architecture: `_excel_to_sqlite/`

#### **sqlite_db**
- SQLite in `<project>/sqlite3` chroot
- Secure query execution
- Transaction support
- Validated DB names

### 📄 Documents & PDF

#### **office_to_pdf** 🆕⭐
- Convert Office documents to PDF using native Office suite
- Formats: .docx/.doc, .pptx/.ppt
- Engine: docx2pdf (macOS/Windows)
- Input: docs/office/ → Output: docs/pdfs/
- Architecture: `_office_to_pdf/`

#### **pdf_download** 🆕
- Download PDFs from URLs to `docs/pdfs`
- Timeout, validation, unique filenames
- Architecture: `_pdf_download/`

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
- Architecture: `_universal_doc/`

### 🎬 Media & YouTube

#### **youtube_search** 🆕 ⭐
- Search YouTube via Data API v3
- 3 ops: search, get_video_details, get_trending
- Advanced filters: channel_id, order='date', published_after/before
- Architecture: `_youtube_search/`

#### **youtube_download** 🆕 ⚡
- Download videos/audio from YouTube URLs
- Modes: audio (MP3), video (MP4), both
- Chroot: docs/video/
- Architecture: `_youtube_download/`

#### **video_transcribe** 🆕 ⚡
- FFmpeg audio extraction + Whisper API transcription
- Parallel chunking, timing metrics
- Architecture: `_video_transcribe/`

#### **ffmpeg_frames**
- Extract frames + shot detection
- Per-frame debug, export images + timestamps

#### **generate_edit_image** 🆕 ⭐
- Generate and edit images using Gemini API
- 3 operations: generate, edit, describe
- Architecture: `_generate_edit_image/`

### ✈️ Aviation & Transport

#### **ship_tracker** ⭐
- Real-time vessel tracking via AIS WebSocket
- 3 ops: track_ships, get_ship_details, get_port_traffic
- Advanced filters, ports DB, dedup by MMSI

#### **flight_tracker** ⭐
- Real-time aircraft tracking via OpenSky
- Circular search by position+radius, flight phases

#### **aviation_weather** ⭐
- Upper air weather via Open-Meteo
- get_winds_aloft, calculate_tas

#### **velib** 🆕
- Paris bike-sharing data
- SQLite cache + real-time availability

### 🔢 Calcul & Math

#### **math**
- Numerical, symbolic, linear algebra, statistics, optimization, number theory, series
- Architecture: `_math/`

#### **date**
- Date/time helpers: now, today, diff, add, format, parse, weekday, week_number

#### **device_location** 🆕⭐
- Get GPS coordinates and location info for current device
- IP-based geolocation (free, no API key required)
- Returns: latitude, longitude, city, region, country, timezone, ISP, ASN
- 2 providers with automatic fallback: ipapi.co (default), ip-api.com
- Accuracy: city/region level (~1-5 km radius)
- Architecture: `_device_location/`

### 🌐 Networking & API

#### **http_client** 🆕
- Universal REST/API client: methods, auth, retry, proxy, timeout, SSL

### ♟️ Chess / Social

#### **chess_com** ⭐🆕
- Complete Chess.com public API access (no auth)
- 24 operations across players, clubs, tournaments, matches, leaderboards, puzzles, streamers

#### **reddit_intelligence**
- Reddit scraping and analysis: search, comments, sentiment, trending, experts

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

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
