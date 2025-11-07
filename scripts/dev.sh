#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Verbose if DEV_VERBOSE=1
if [[ "${DEV_VERBOSE:-0}" == "1" ]]; then set -x; fi

# Always run from repo root (relative to script location)
SCRIPT_FILE="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(dirname "${SCRIPT_FILE}")"
cd "${SCRIPT_DIR}/.."

# Detect Python
if [[ -n "${PYBIN:-}" ]]; then
  PYBIN="${PYBIN}"
elif [[ -x "venv/bin/python" ]]; then
  PYBIN="venv/bin/python"
elif [[ -x ".venv/bin/python" ]]; then
  PYBIN=".venv/bin/python"
elif [[ -n "${VIRTUAL_ENV:-}" ]]; then
  if [[ -x "${VIRTUAL_ENV}/bin/python" ]]; then
    PYBIN="${VIRTUAL_ENV}/bin/python"
  elif [[ -x "${VIRTUAL_ENV}/bin/python3" ]]; then
    PYBIN="${VIRTUAL_ENV}/bin/python3"
  elif command -v python3 >/dev/null 2>&1; then
    PYBIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYBIN="python"
  else
    echo "[dev.sh] ❌ Python introuvable. Active un venv local (./venv) ou assure python3 dans le PATH." >&2
    exit 1
  fi
else
  if command -v python3 >/dev/null 2>&1; then
    PYBIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYBIN="python"
  else
    echo "[dev.sh] ❌ Python introuvable (ni python3 ni python dans PATH)" >&2
    exit 1
  fi
fi

PYVER="$(${PYBIN} --version 2>&1 || true)"
echo "[dev.sh] Python: ${PYVER} (${PYBIN})"

# Deps (best-effort)
echo "[dev.sh] Installing deps (best-effort)"
"${PYBIN}" -m pip install -U pip setuptools wheel >/dev/null 2>&1 || true
"${PYBIN}" -m pip install -e . >/dev/null 2>&1 || "${PYBIN}" -m pip install . >/dev/null 2>&1 || true

# Always install TTS extras in best-effort (no env toggle required)
echo "[dev.sh] Installing TTS extras (best-effort)"
"${PYBIN}" -m pip install -e ".[tts]" >/dev/null 2>&1 || "${PYBIN}" -m pip install ".[tts]" >/dev/null 2>&1 || true

# One-time voice fetch: only if no .onnx found under models/piper
piper_has_model() {
  # returns 0 if a model exists, 1 otherwise
  if find models/piper -type f -name '*.onnx' -print -quit 2>/dev/null | grep -q .; then
    return 0
  else
    return 1
  fi
}

if ! piper_has_model; then
  if [[ -f scripts/download_piper_fr_voices.py ]]; then
    echo "[dev.sh] No Piper voices found → downloading FR voices (one-time)"
    "${PYBIN}" scripts/download_piper_fr_voices.py || true
  fi
  # Fallback to legacy bootstrap if still empty
  if ! piper_has_model && [[ -f scripts/bootstrap_speech_assets.py ]]; then
    echo "[dev.sh] Voices still missing → legacy bootstrap (best-effort)"
    "${PYBIN}" scripts/bootstrap_speech_assets.py || true
  fi
fi

# Optional tools catalog
if [[ -f scripts/generate_tools_catalog.py ]]; then
  echo "[dev.sh] Generating tools catalog"
  "${PYBIN}" scripts/generate_tools_catalog.py >/dev/null 2>&1 || true
fi

PORT="${PORT:-8000}"
WORKERS="${WORKERS:-5}"
echo "[dev.sh] Start server: PORT=${PORT} WORKERS=${WORKERS}"

trap 'echo "[dev.sh] ❌ Failed (last command)" >&2' ERR

have_cmd() { command -v "$1" >/dev/null 2>&1; }
have_py_mod() { "${PYBIN}" -c "import importlib,sys; sys.exit(0 if importlib.util.find_spec('$1') else 1)" >/dev/null 2>&1; }

if have_cmd gunicorn && have_py_mod uvicorn; then
  echo "[dev.sh] ▶️ gunicorn -w ${WORKERS}"
  exec "${PYBIN}" -m gunicorn -k uvicorn.workers.UvicornWorker -w "${WORKERS}" 'src.app_factory:create_app' -b "0.0.0.0:${PORT}"
fi

if have_cmd uvicorn; then
  echo "[dev.sh] ▶️ uvicorn --workers ${WORKERS}"
  exec "${PYBIN}" -m uvicorn src.app_factory:create_app --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}"
fi

if [[ -f src/server.py ]]; then
  echo "[dev.sh] ▶️ fallback python src/server.py (single-worker)"
  exec "${PYBIN}" src/server.py
fi

echo "[dev.sh] ❌ uvicorn/gunicorn introuvables et aucun src/server.py. Installe uvicorn ou gunicorn, ou fournis src/server.py" >&2
exit 1
