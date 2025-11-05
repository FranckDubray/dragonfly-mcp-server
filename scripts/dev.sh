#!/usr/bin/env bash
set -euo pipefail
# Robust whitespace handling (avoid word-splitting on spaces)
IFS=$'\n\t'

# Verbose if DEV_VERBOSE=1
if [[ "${DEV_VERBOSE:-0}" == "1" ]]; then set -x; fi

# Always run from repo root (space-safe)
SCRIPT_FILE="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_FILE}")" && pwd -P)"
cd "${SCRIPT_DIR}/.."

# Detect Python (space-safe)
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  PYBIN="$(command -v python)"
else
  PYBIN="$(command -v python || echo python)"
fi

PYVER="$("$PYBIN" --version 2>&1 || true)"
echo "[dev.sh] Python: ${PYVER}"

# Deps (best-effort)
echo "[dev.sh] Installing deps (best-effort)"
"$PYBIN" -m pip install -U pip setuptools wheel >/dev/null 2>&1 || true
# Prefer editable install when possible
"$PYBIN" -m pip install -e . >/dev/null 2>&1 || "$PYBIN" -m pip install . >/dev/null 2>&1 || true

# Playwright (best-effort)
PLAYWRIGHT_BROWSERS_PATH="playwright/browsers" "$PYBIN" -m playwright install chromium >/dev/null 2>&1 || true

# Optional tools catalog
if [[ -f scripts/generate_tools_catalog.py ]]; then
  echo "[dev.sh] Generating tools catalog"
  "$PYBIN" scripts/generate_tools_catalog.py || true
fi

PORT="${PORT:-8000}"
WORKERS="${WORKERS:-5}"
echo "[dev.sh] Start server: PORT=${PORT} WORKERS=${WORKERS}"

# Error trap
trap 'echo "[dev.sh] ❌ Failed (last command)" >&2' ERR

have_cmd() { command -v "$1" >/dev/null 2>&1; }
have_py_mod() { "$PYBIN" -c "import importlib,sys; sys.exit(0 if importlib.util.find_spec('$1') else 1)" >/dev/null 2>&1; }

# Prefer gunicorn if present (AND uvicorn module for the worker)
if have_cmd gunicorn && have_py_mod uvicorn; then
  echo "[dev.sh] ▶️ gunicorn -w ${WORKERS}"
  exec "$PYBIN" -m gunicorn -k uvicorn.workers.UvicornWorker -w "$WORKERS" 'src.app_factory:create_app' -b "0.0.0.0:${PORT}"
fi

# Else uvicorn CLI
if have_cmd uvicorn; then
  echo "[dev.sh] ▶️ uvicorn --workers ${WORKERS}"
  exec "$PYBIN" -m uvicorn src.app_factory:create_app --host 0.0.0.0 --port "$PORT" --workers "$WORKERS"
fi

# Fallbacks
if [[ -f src/server.py ]]; then
  echo "[dev.sh] ▶️ fallback python src/server.py (single-worker)"
  exec "$PYBIN" src/server.py
fi

echo "[dev.sh] ❌ uvicorn/gunicorn introuvables et aucun src/server.py. Installe uvicorn ou gunicorn, ou fournis src/server.py" >&2
exit 1
