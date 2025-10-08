# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Tool `imap`: accès universel aux emails via IMAP (Gmail, Outlook, Yahoo, iCloud, Infomaniak, serveurs custom)
  - **Multi-comptes**: support de plusieurs comptes email simultanés via variables d'env par provider
    - `IMAP_GMAIL_EMAIL` / `IMAP_GMAIL_PASSWORD`
    - `IMAP_INFOMANIAK_EMAIL` / `IMAP_INFOMANIAK_PASSWORD`
    - `IMAP_OUTLOOK_EMAIL` / `IMAP_OUTLOOK_PASSWORD`
    - `IMAP_YAHOO_EMAIL` / `IMAP_YAHOO_PASSWORD`
    - `IMAP_ICLOUD_EMAIL` / `IMAP_ICLOUD_PASSWORD`
    - Custom: `IMAP_CUSTOM_EMAIL`, `IMAP_CUSTOM_PASSWORD`, `IMAP_CUSTOM_SERVER`, `IMAP_CUSTOM_PORT`, `IMAP_CUSTOM_USE_SSL`
  - **Providers supportés**: Gmail, Outlook/Hotmail, Yahoo, iCloud, **Infomaniak** (nouveau), custom
  - **Operations**: connect, list_folders, search_messages, get_message, download_attachments, mark_read/unread, move_message, delete_message
  - **Batch operations**: mark_read_batch, mark_unread_batch, move_messages_batch, delete_messages_batch, mark_spam
  - Presets intégrés pour providers populaires (config automatique server/port/SSL)
  - Setup rapide (5 min): App Password + enable IMAP (vs 30+ min pour OAuth/GCP)
  - Parsing MIME complet (headers, body text/html, attachments)
  - Recherche IMAP standard (FROM, SUBJECT, SINCE, UNSEEN…)
  - Normalisation des folders via alias (`inbox`, `sent`, `trash`, `spam`)
  - **Sécurité renforcée**: SSL par défaut, chroot projet pour attachments, passwords masqués, **aucun credential en paramètre d'appel** (tout via `.env` + `provider`)

### Changed
- IMAP tool architecture refactored for multi-account support
  - Variables d'env séparées par provider (ex: `IMAP_GMAIL_EMAIL`, `IMAP_INFOMANIAK_EMAIL`)
  - Paramètre `provider` obligatoire pour sélectionner le compte à utiliser
  - Chaque provider a ses propres credentials isolés
- Documentation complète ajoutée:
  - `/README.md`: section IMAP multi-comptes avec exemples
  - `/src/README.md`: variables d'env et exemples d'appels
  - `/src/tools/README.md`: guide complet du tool IMAP
  - `/src/tools/_imap/README.md`: documentation détaillée avec setup rapide
- .gitignore: ajout de `files/imap/` pour ignorer les données sensibles du tool IMAP

---

## [1.2.0] - 2025-10-08

### Highlights
- FFmpeg frames: native frame-by-frame detection (PyAV) with moving average + hysteresis + NMS + native refinement. Much higher recall on compressed cuts (YouTube-like), plus per-frame similarity debug.

### Added
- ffmpeg_frames: per-frame debug (t, diff, similarity_pct) and avg_similarity_pct.
- ffmpeg_frames: returns exec_time_sec in the API response and in debug.json.
- Native video decode dependencies auto-install in scripts/dev.sh (NumPy + PyAV).
- Refactor for maintainability: split FFmpeg tool into `detect.py` (API), `native.py` (PyAV), and `utils.py` (helpers).

### Changed
- ffmpeg_frames sensitivity (defaults): scale=96x96, ma_window=1, threshold_floor=0.05, NMS=0.2s, refine_window=0.5s, min_scene_frames=3.
- README mentions native detection and debug fields.

### Fixed
- Cases where legacy downsampled CLI missed many hard cuts. Native pass now processes at the video's native FPS.

### Migration notes
- Ensure Python 3.11+ and that scripts/dev.sh reinstalls dependencies to get NumPy + PyAV.
- If results are still too conservative, consider lowering threshold_floor to 0.04 or min_scene_frames to 2.

---

## [1.1.0] - 2025-10-08

### Highlights
- Math tool reliability overhaul: no more generic 500 errors. All failures return explicit, actionable error messages.
- New tool: `ffmpeg_frames` (extract frames/images from a video via FFmpeg).
- Dev scripts now load `.env` automatically (Bash + PowerShell).
- Safer repository hygiene: data/runtime folders ignored by default.

### Added
- Tool: `ffmpeg_frames` with its canonical spec (`src/tool_specs/ffmpeg_frames.json`).
- App core modules:
  - `src/app_core/safe_json.py` – robust JSON sanitizer/response (handles NaN/Infinity/very large ints safely).
  - `src/app_core/tool_discovery.py` – tool discovery and auto‑reload logic.
- Math tool dispatcher (refactor + expansion):
  - New structure:
    - `src/tools/_math/dispatch_core.py` – helpers (error/jsonify/coercions).
    - `src/tools/_math/dispatch_basic.py` – basic ops (arith/trig/complex/log/exp/sqrt) with explicit errors only.
    - `src/tools/_math/dispatcher.py` – high‑level router to advanced modules.
  - Advanced operations routed to existing modules:
    - Symbolic: `derivative`, `integral`, `simplify`, `expand`, `factor`.
    - Calculus: `limit`, `series`, `gradient`, `jacobian`, `hessian`.
    - Linear algebra: `mat_add`, `mat_mul`, `mat_det`, `mat_inv`, `mat_transpose`, `mat_rank`, `mat_solve`, `eig`, `vec_add`, `dot`, `cross`, `norm`.
    - LA extensions: `pinv`, `cond`, `trace`, `nullspace`, `lu`, `qr`.
    - Probability/Stats: `mean`, `median`, `mode`, `stdev`, `variance`, `combination`, `permutation`.
    - Distributions: `normal_cdf`, `normal_ppf`, `poisson_pmf`, `poisson_cdf`, `binomial_cdf`, `uniform_pdf`, `uniform_cdf`, `exponential_pdf`, `exponential_cdf`.
    - Polynomial: `poly_roots`, `poly_factor`, `poly_expand`.
    - Solvers: `solve_eq`, `solve_system`, `nsolve`, `root_find`, `optimize_1d`.
    - Number theory: `nth_prime`, `prime_approx`, `is_prime`, `next_prime`, `prev_prime`, `prime_factors`, `factorize`, `euler_phi`, `primes_range`.
    - Summations: `sum_finite`, `product_finite`, `sum_infinite`.
    - High precision: `eval_precise` (mpmath‑based).

### Changed
- Scripts:
  - `scripts/dev.sh`: now sources `.env` (export), verifies Python 3.11+, creates/activates venv, installs deps + extras (pypdf, sympy, requests), prints config, and launches `python -m server` from `src/`.
  - `scripts/dev.ps1`: same parity as Bash (charge `.env`, venv, deps, config, start).
- README updated:
  - Tools list (incl. `ffmpeg_frames`, `script_executor`, `academic_research_super`).
  - Endpoints/config/security sections refreshed.

### Fixed
- Math tool returning generic HTTP 500 via API:
  - All error cases now return explicit error objects (e.g., `Division by zero`, `Modulo by zero`, `Square root of negative number: set complex=true to get complex result`, `Unknown operation: …`, `Missing numeric inputs …`).
  - Complex results are JSON‑safe as `{re, im}`.
- Ensured `.env` is loaded by both the app and the dev scripts.

### Repository hygiene
- `.gitignore` now ignores non‑source and local runtime folders:
  - `docs/`, `files/`, `script_executor/` (top‑level), `sqlite3/`, `venv/`, `.venv/`, `.DS_Store`, `__pycache__/`, `*.pyc`.
  - Note: source code under `src/tools/_script_executor/` remains tracked.

### Migration notes
- Python 3.11+ is now required (enforced by scripts and project metadata).
- Dev scripts source `.env` before installing dependencies and launching the server.
- If you kept custom scripts under top‑level `script_executor/`, they're now ignored by Git; move them outside the repo or under a non‑tracked path.
- For advanced math features, ensure `sympy` is installed (scripts install it automatically). For high‑precision evaluation, `mpmath` is optional but recommended.
