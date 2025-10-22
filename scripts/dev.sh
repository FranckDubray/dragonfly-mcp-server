#!/usr/bin/env bash
set -euo pipefail

# Detect venv python
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  PYBIN="$(command -v python)"
else
  echo "[dev.sh] ⚠️ Avertissement: aucun venv activé (VIRTUAL_ENV vide)." >&2
  PYBIN="python"
fi

echo "[dev.sh] 🔧 Python: $($PYBIN --version)"

echo "[dev.sh] 📦 Installation navigateurs Playwright (confinés dans playwright/browsers)"
PLAYWRIGHT_BROWSERS_PATH="playwright/browsers" "$PYBIN" -m playwright install chromium || true

# Génération du catalogue tools (si le script existe)
if [[ -f scripts/generate_tools_catalog.py ]]; then
  echo "[dev.sh] 🧾 Génération catalogue tools"
  "$PYBIN" scripts/generate_tools_catalog.py || true
fi

# Lancement du serveur
echo "[dev.sh] 🚀 Démarrage serveur"
"$PYBIN" src/server.py
