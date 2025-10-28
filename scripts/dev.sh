#!/usr/bin/env bash
set -euo pipefail

# Always run from repo root (relative paths only)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

# Detect venv python (no absolute paths required)
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  PYBIN="$(command -v python)"
else
  echo "[dev.sh] ⚠️ Avertissement: aucun venv activé (VIRTUAL_ENV vide). Installation des dépendances sur l'interpréteur courant." >&2
  PYBIN="python"
fi

# Print Python version (path may contain spaces, so quote in command substitution)
PYVER="$("$PYBIN" --version 2>&1)"
echo "[dev.sh] 🔧 Python: ${PYVER}"

# Ensure deps from pyproject are installed (simple, idempotent)
echo "[dev.sh] 📦 Installation des dépendances (pyproject)"
"$PYBIN" -m pip install -U pip setuptools wheel >/dev/null 2>&1 || true
# Mode editable si dispo (dev), sinon installation classique
"$PYBIN" -m pip install -e . || "$PYBIN" -m pip install .

# Playwright browsers (scopés dans ./playwright/browsers)
echo "[dev.sh] 📦 Installation navigateurs Playwright (scopés dans ./playwright/browsers)"
PLAYWRIGHT_BROWSERS_PATH="playwright/browsers" "$PYBIN" -m playwright install chromium || true

# Génération du catalogue tools (si présent)
if [[ -f scripts/generate_tools_catalog.py ]]; then
  echo "[dev.sh] 🧠 Génération catalogue tools"
  "$PYBIN" scripts/generate_tools_catalog.py || true
fi

# Lancement du serveur (chemins relatifs)
echo "[dev.sh] 🚀 Démarrage serveur"
"$PYBIN" src/server.py
