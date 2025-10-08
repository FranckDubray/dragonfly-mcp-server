# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### 🎯 Next steps
- SMTP tool for email sending
- OAuth2 support for IMAP (Gmail, Outlook)
- PDF metadata search (find PDFs by author/title/date)
- Batch PDF download (download multiple PDFs from a list)
- PDF cache (avoid re-downloading identical files)

---

## [1.4.0] - 2025-10-08

### 🎉 Highlights
- **PDF Download Tool** with automatic metadata extraction
- Intelligent filename management with unique naming
- Complete PDF workflow integration (download → extract → search)

### ✨ Added

#### PDF Download Tool 🆕
- **New tool**: `pdf_download` for downloading PDFs from URLs to `docs/pdfs`
- **Features**:
  - HTTP/HTTPS download with configurable timeout (5-300s, default 60s)
  - PDF validation via magic bytes (`%PDF-`)
  - **Automatic metadata extraction**: page count, title, author, creator
  - Automatic unique filename generation (suffixes `_1`, `_2`, etc.)
  - Optional overwrite mode
  - Filename extraction from URL if not provided
  - User-Agent header for compatibility
- **Security**:
  - Chroot to `docs/pdfs` directory
  - URL validation (http/https only)
  - Filename sanitization (no path traversal)
  - Magic bytes verification
- **Architecture**: `_pdf_download/` (api, core, validators, utils, services/downloader)
- **Spec**: `src/tool_specs/pdf_download.json` (canonical source of truth)

### 📚 Documentation
- Updated main README with pdf_download tool (16 tools total)
- Updated src/README.md with pdf_download examples
- Updated src/tools/README.md with complete tool catalog
- Added comprehensive README in `src/tools/_pdf_download/`

### 🔄 Changed
- Tool count increased from 15 to 16
- Enhanced PDF workflow capabilities

### 🐛 Fixed
- No bug fixes in this release (new feature only)

### 📦 Migration notes
- **New users**: Start using the tool immediately (see documentation)
- **Existing users**: No breaking changes, extends existing PDF capabilities
- Requires `pypdf>=4.2.0` (already in dependencies)

---

## [1.3.0] - 2025-10-08

### 🎉 Highlights
- **IMAP multi-account email tool** with 6 providers (Gmail, Outlook, Yahoo, iCloud, Infomaniak, Custom)
- **Git tool enhanced** with pull, fetch, rebase operations and conflict detection
- Complete workflow automation without manual CLI commands

### ✨ Added

#### IMAP Tool (multi-account email access)
- **Universal IMAP access** across 6 providers: Gmail, Outlook, Yahoo, iCloud, **Infomaniak** (new), Custom
- **Multi-account architecture**: separate environment variables per provider
  - `IMAP_GMAIL_EMAIL` / `IMAP_GMAIL_PASSWORD`
  - `IMAP_INFOMANIAK_EMAIL` / `IMAP_INFOMANIAK_PASSWORD`
  - `IMAP_OUTLOOK_EMAIL` / `IMAP_OUTLOOK_PASSWORD`
  - `IMAP_YAHOO_EMAIL` / `IMAP_YAHOO_PASSWORD`
  - `IMAP_ICLOUD_EMAIL` / `IMAP_ICLOUD_PASSWORD`
  - Custom: `IMAP_CUSTOM_EMAIL`, `IMAP_CUSTOM_PASSWORD`, `IMAP_CUSTOM_SERVER`, `IMAP_CUSTOM_PORT`, `IMAP_CUSTOM_USE_SSL`
- **13 operations**:
  - `connect`: test connection and return account info
  - `list_folders`: list all IMAP folders
  - `search_messages`: search by date, sender, subject, seen/unseen, flagged
  - `get_message`: retrieve full message with body and attachments
  - `download_attachments`: save attachments to files/
  - `mark_read` / `mark_unread`: single message operations
  - `mark_read_batch` / `mark_unread_batch`: bulk operations
  - `move_message` / `move_messages_batch`: move to another folder
  - `mark_spam`: move to spam/junk folder (batch)
  - `delete_message` / `delete_messages_batch`: delete with optional expunge
- **Presets**: automatic server/port/SSL configuration for popular providers
- **Setup time**: 5 minutes (App Password + enable IMAP) vs 30+ minutes for OAuth/GCP
- **MIME parsing**: complete headers, body (text/html), attachments metadata
- **IMAP search**: standard criteria (FROM, SUBJECT, SINCE, UNSEEN, FLAGGED, etc.)
- **Folder normalization**: aliases (`inbox`, `sent`, `trash`, `spam`) mapped to provider-specific names
- **Security**:
  - SSL by default (port 993)
  - Project-chroot for attachments (`files/imap/`)
  - Passwords masked in logs
  - **Zero credentials in tool parameters** (all via `.env` + `provider` selector)
- Architecture: `src/tools/_imap/` (presets, connection, operations, parsers, utils)
- Complete documentation: `src/tools/_imap/README.md` with quick setup guides

#### Git Tool Enhanced
- **New operations**:
  - `fetch`: fetch updates from remote without merging (with `--prune` option)
  - `pull`: fetch + merge or rebase (configurable `rebase`, `ff_only` flags)
  - `rebase`: rebase current branch with `continue`, `abort`, `skip` support
  - `log`: commit history with `max_count`, `one_line`, `graph` options
  - `remote_info`: get remote repository information
- **Conflict detection**: automatic detection for pull/rebase/merge with helpful hints
- **Error handling**: explicit messages for conflicts with resolution commands
- Enable complete git workflow without leaving the tool environment

### 🔄 Changed

#### IMAP multi-account refactor
- Variables d'env séparées par provider (ex: `IMAP_GMAIL_EMAIL`, `IMAP_INFOMANIAK_EMAIL`)
- Paramètre `provider` obligatoire pour sélectionner le compte
- Chaque provider a ses propres credentials isolés
- Architecture modulaire: presets, connection, operations, parsers, utils

#### Documentation updates
- `/README.md`: complete tools catalog (15 tools) with detailed descriptions
- `/src/README.md`: IMAP multi-account env vars and examples
- `/src/tools/README.md`: comprehensive tool guide with architectures
- `/src/tools/_imap/README.md`: detailed IMAP setup and usage guide

#### Git ignore
- Added `files/imap/` to ignore sensitive email data

### 🐛 Fixed
- Git tool now properly handles pull/rebase conflicts with actionable error messages
- IMAP folder normalization works across all providers (Gmail's `[Gmail]/` syntax, etc.)

### 📦 Migration notes
- **IMAP users**: update `.env` with provider-specific variables (see documentation)
- **Git workflows**: `pull`, `fetch`, `rebase` now available directly through the tool
- No breaking changes for existing tools

### 🎯 Next steps
- OAuth2 support for IMAP (Gmail, Outlook) as alternative to App Passwords
- Email composition and sending (SMTP tool)
- Advanced filtering and rules engine for email automation

---

## [1.2.0] - 2025-10-08

### Highlights
- FFmpeg frames: native frame-by-frame detection (PyAV) with moving average + hysteresis + NMS + native refinement
- Much higher recall on compressed cuts (YouTube-like), plus per-frame similarity debug

### Added
- ffmpeg_frames: per-frame debug (t, diff, similarity_pct) and avg_similarity_pct
- ffmpeg_frames: returns exec_time_sec in the API response and in debug.json
- Native video decode dependencies auto-install in scripts/dev.sh (NumPy + PyAV)
- Refactor for maintainability: split FFmpeg tool into `detect.py` (API), `native.py` (PyAV), and `utils.py` (helpers)

### Changed
- ffmpeg_frames sensitivity (defaults): scale=96x96, ma_window=1, threshold_floor=0.05, NMS=0.2s, refine_window=0.5s, min_scene_frames=3
- README mentions native detection and debug fields

### Fixed
- Cases where legacy downsampled CLI missed many hard cuts. Native pass now processes at the video's native FPS

### Migration notes
- Ensure Python 3.11+ and that scripts/dev.sh reinstalls dependencies to get NumPy + PyAV
- If results are still too conservative, consider lowering threshold_floor to 0.04 or min_scene_frames to 2

---

## [1.1.0] - 2025-10-08

### Highlights
- Math tool reliability overhaul: no more generic 500 errors
- New tool: `ffmpeg_frames` (extract frames/images from a video via FFmpeg)
- Dev scripts now load `.env` automatically (Bash + PowerShell)
- Safer repository hygiene: data/runtime folders ignored by default

### Added
- Tool: `ffmpeg_frames` with its canonical spec (`src/tool_specs/ffmpeg_frames.json`)
- App core modules:
  - `src/app_core/safe_json.py` – robust JSON sanitizer/response (handles NaN/Infinity/very large ints safely)
  - `src/app_core/tool_discovery.py` – tool discovery and auto‑reload logic
- Math tool dispatcher (refactor + expansion):
  - New structure:
    - `src/tools/_math/dispatch_core.py` – helpers (error/jsonify/coercions)
    - `src/tools/_math/dispatch_basic.py` – basic ops (arith/trig/complex/log/exp/sqrt) with explicit errors only
    - `src/tools/_math/dispatcher.py` – high‑level router to advanced modules
  - Advanced operations routed to existing modules:
    - Symbolic: `derivative`, `integral`, `simplify`, `expand`, `factor`
    - Calculus: `limit`, `series`, `gradient`, `jacobian`, `hessian`
    - Linear algebra: `mat_add`, `mat_mul`, `mat_det`, `mat_inv`, `mat_transpose`, `mat_rank`, `mat_solve`, `eig`, `vec_add`, `dot`, `cross`, `norm`
    - LA extensions: `pinv`, `cond`, `trace`, `nullspace`, `lu`, `qr`
    - Probability/Stats: `mean`, `median`, `mode`, `stdev`, `variance`, `combination`, `permutation`
    - Distributions: `normal_cdf`, `normal_ppf`, `poisson_pmf`, `poisson_cdf`, `binomial_cdf`, `uniform_pdf`, `uniform_cdf`, `exponential_pdf`, `exponential_cdf`
    - Polynomial: `poly_roots`, `poly_factor`, `poly_expand`
    - Solvers: `solve_eq`, `solve_system`, `nsolve`, `root_find`, `optimize_1d`
    - Number theory: `nth_prime`, `prime_approx`, `is_prime`, `next_prime`, `prev_prime`, `prime_factors`, `factorize`, `euler_phi`, `primes_range`
    - Summations: `sum_finite`, `product_finite`, `sum_infinite`
    - High precision: `eval_precise` (mpmath‑based)

### Changed
- Scripts:
  - `scripts/dev.sh`: now sources `.env` (export), verifies Python 3.11+, creates/activates venv, installs deps + extras (pypdf, sympy, requests), prints config, and launches `python -m server` from `src/`
  - `scripts/dev.ps1`: same parity as Bash (charge `.env`, venv, deps, config, start)
- README updated:
  - Tools list (incl. `ffmpeg_frames`, `script_executor`, `academic_research_super`)
  - Endpoints/config/security sections refreshed

### Fixed
- Math tool returning generic HTTP 500 via API:
  - All error cases now return explicit error objects
- Ensured `.env` is loaded by both the app and the dev scripts

### Repository hygiene
- `.gitignore` now ignores non‑source and local runtime folders:
  - `docs/`, `files/`, `script_executor/` (top‑level), `sqlite3/`, `venv/`, `.venv/`, `.DS_Store`, `__pycache__/`, `*.pyc`
  - Note: source code under `src/tools/_script_executor/` remains tracked

### Migration notes
- Python 3.11+ is now required (enforced by scripts and project metadata)
- Dev scripts source `.env` before installing dependencies and launching the server
- If you kept custom scripts under top‑level `script_executor/`, they're now ignored by Git; move them outside the repo or under a non‑tracked path
- For advanced math features, ensure `sympy` is installed (scripts install it automatically). For high‑precision evaluation, `mpmath` is optional but recommended
