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

## Available tools (15 complete)

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

#### **imap** ⭐ NOUVEAU
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
- **GitHub API**: create_repo, add/delete files, branches, commits, diff, merge
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

### 🎬 Media & FFmpeg

#### **ffmpeg_frames**
- Extract images/frames from video via FFmpeg
- **Native PyAV shot detection** (frame-by-frame)
- Moving average + hysteresis + NMS + refinement
- Per-frame debug: time, diff, similarity%
- High precision on compressed videos (YouTube-like)
- Export: images + timestamps + debug.json
- Architecture: `_ffmpeg/` (detect, native, utils)

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
