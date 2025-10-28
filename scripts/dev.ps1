#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Always run from repo root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $ScriptDir '..')

# Detect Python
function Get-Python {
  try {
    $v = & python --version 2>$null
    if ($LASTEXITCODE -eq 0) { return 'python' }
  } catch {}
  try {
    $v = & py -3 --version 2>$null
    if ($LASTEXITCODE -eq 0) { return 'py -3' }
  } catch {}
  return 'python'
}

$PY = Get-Python
Write-Host "[dev.ps1] 🔧 Python version:" (& $PY --version)

# Ensure deps (idempotent)
Write-Host "[dev.ps1] 📦 Installation des dépendances (pyproject)"
try { & $PY -m pip install -U pip setuptools wheel *> $null } catch {}
try { & $PY -m pip install -e . } catch { & $PY -m pip install . }

# Playwright browsers (scoped in ./playwright/browsers)
Write-Host "[dev.ps1] 📦 Installation navigateurs Playwright (scopés dans ./playwright/browsers)"
$env:PLAYWRIGHT_BROWSERS_PATH = 'playwright/browsers'
try { & $PY -m playwright install chromium } catch {}

# Generate tools catalog if script exists
if (Test-Path 'scripts/generate_tools_catalog.py') {
  Write-Host "[dev.ps1] 🧠 Génération catalogue tools"
  try { & $PY scripts/generate_tools_catalog.py } catch {}
}

# Start server
Write-Host "[dev.ps1] 🚀 Démarrage serveur"
& $PY src/server.py
