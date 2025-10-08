# Changelog

All notable changes to this project will be documented in this file.

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
- If you kept custom scripts under top‑level `script_executor/`, they’re now ignored by Git; move them outside the repo or under a non‑tracked path.
- For advanced math features, ensure `sympy` is installed (scripts install it automatically). For high‑precision evaluation, `mpmath` is optional but recommended.

