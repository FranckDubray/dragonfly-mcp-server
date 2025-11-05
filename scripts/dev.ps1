#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Verbose mode: set $env:DEV_VERBOSE=1 to enable
$Verbose = $env:DEV_VERBOSE -eq '1'

# Always run from repo root (space-safe)
$Root = Join-Path $PSScriptRoot ".."
Set-Location $Root

# Detect Python
$py = $null
try {
  if ($env:VIRTUAL_ENV) { $py = (Get-Command python -ErrorAction Stop).Source }
  else { $py = (Get-Command python -ErrorAction Stop).Source }
} catch {
  $py = 'python'
}

try {
  $ver = & $py --version 2>&1
  Write-Host "[dev.ps1] Python: $ver"
} catch {
  Write-Warning "[dev.ps1] Python introuvable dans PATH. Le script peut échouer."
}

# Deps (best-effort)
Write-Host "[dev.ps1] Installing deps (best-effort)"
try { & $py -m pip install -U pip setuptools wheel | Out-Null } catch {}
try { & $py -m pip install -e . | Out-Null } catch { try { & $py -m pip install . | Out-Null } catch {} }

# Playwright (best-effort)
try { $env:PLAYWRIGHT_BROWSERS_PATH = "playwright/browsers"; & $py -m playwright install chromium | Out-Null } catch {}

# Optional tools catalog
if (Test-Path "scripts/generate_tools_catalog.py") {
  Write-Host "[dev.ps1] Generating tools catalog"
  try { & $py scripts/generate_tools_catalog.py } catch {}
}

$PORT = if ($env:PORT) { $env:PORT } else { '8000' }
$WORKERS = if ($env:WORKERS) { $env:WORKERS } else { '5' }
Write-Host "[dev.ps1] Start server: PORT=$PORT WORKERS=$WORKERS"

function Test-PyModule($module) {
  try {
    & $py -c "import importlib,sys; sys.exit(0 if importlib.util.find_spec('$module') else 1)" | Out-Null
    return $LASTEXITCODE -eq 0
  } catch { return $false }
}

# Prefer uvicorn if available on Windows
if (Test-PyModule 'uvicorn') {
  Write-Host "[dev.ps1] ▶ uvicorn --workers $WORKERS"
  & $py -m uvicorn src.app_factory:create_app --host 0.0.0.0 --port $PORT --workers $WORKERS
  exit $LASTEXITCODE
}

# Fallback to server.py
if (Test-Path "src/server.py") {
  Write-Host "[dev.ps1] ▶ fallback python src/server.py (single-worker)"
  & $py src/server.py
  exit $LASTEXITCODE
}

Write-Error "[dev.ps1] ❌ uvicorn introuvable et aucun src/server.py. Installe uvicorn, ou fournis src/server.py"
exit 1
