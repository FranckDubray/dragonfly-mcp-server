param(
  [string]$Port = $env:PORT, 
  [string]$Workers = $env:WORKERS
)

if (-not $Port) { $Port = "8000" }
if (-not $Workers) { $Workers = "5" }

$ErrorActionPreference = 'Stop'

# Move to repo root
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
Set-Location -Path ..

# Detect Python
function Get-Python {
  if ($env:PYBIN) { return $env:PYBIN }
  if (Test-Path ".\.venv\Scripts\python.exe") { return ".\.venv\Scripts\python.exe" }
  if (Test-Path ".\venv\Scripts\python.exe") { return ".\venv\Scripts\python.exe" }
  if ($env:VIRTUAL_ENV) {
    if (Test-Path "$env:VIRTUAL_ENV\Scripts\python.exe") { return "$env:VIRTUAL_ENV\Scripts\python.exe" }
  }
  $py = (Get-Command python -ErrorAction SilentlyContinue); if ($py) { return $py.Path }
  $py3 = (Get-Command python3 -ErrorAction SilentlyContinue); if ($py3) { return $py3.Path }
  throw "Python introuvable. Active un venv (.\venv) ou assure python dans le PATH."
}

$pybin = Get-Python
Write-Host "[dev.ps1] Python: $($(& $pybin --version)) ($pybin)"

# Deps (best-effort)
try { & $pybin -m pip install -U pip setuptools wheel | Out-Null } catch {}
try { & $pybin -m pip install -e . | Out-Null } catch { try { & $pybin -m pip install . | Out-Null } catch {} }

# Always install TTS extras in best-effort (no env toggle required)
Write-Host "[dev.ps1] Installing TTS extras (best-effort)"
try { & $pybin -m pip install -e ".[tts]" | Out-Null } catch { try { & $pybin -m pip install ".[tts]" | Out-Null } catch {} }

# One-time voice fetch: only if no .onnx found under models/piper
function Test-PiperModel {
  $files = Get-ChildItem -Path "models/piper" -Recurse -Include *.onnx -ErrorAction SilentlyContinue
  return [bool]$files
}

if (-not (Test-PiperModel)) {
  if (Test-Path "scripts/download_piper_fr_voices.py") {
    Write-Host "[dev.ps1] No Piper voices found → downloading FR voices (one-time)"
    try { & $pybin scripts/download_piper_fr_voices.py } catch {}
  }
  if (-not (Test-PiperModel) -and (Test-Path "scripts/bootstrap_speech_assets.py")) {
    Write-Host "[dev.ps1] Voices still missing → legacy bootstrap (best-effort)"
    try { & $pybin scripts/bootstrap_speech_assets.py } catch {}
  }
}

# Optional tools catalog
if (Test-Path "scripts\generate_tools_catalog.py") {
  Write-Host "[dev.ps1] Generating tools catalog"
  try { & $pybin scripts\generate_tools_catalog.py | Out-Null } catch {}
}

Write-Host "[dev.ps1] Start server: PORT=$Port WORKERS=$Workers"

function Have-Cmd($name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }

if (Have-Cmd gunicorn) {
  Write-Host "[dev.ps1] ▶️ gunicorn -w $Workers"
  & $pybin -m gunicorn -k uvicorn.workers.UvicornWorker -w $Workers 'src.app_factory:create_app' -b "0.0.0.0:$Port"
  exit $LASTEXITCODE
}

if (Have-Cmd uvicorn) {
  Write-Host "[dev.ps1] ▶️ uvicorn --workers $Workers"
  & $pybin -m uvicorn src.app_factory:create_app --host 0.0.0.0 --port $Port --workers $Workers
  exit $LASTEXITCODE
}

if (Test-Path "src\server.py") {
  Write-Host "[dev.ps1] ▶️ fallback python src\server.py (single-worker)"
  & $pybin src\server.py
  exit $LASTEXITCODE
}

Write-Host "[dev.ps1] ❌ uvicorn/gunicorn introuvables et aucun src\server.py. Installe uvicorn ou gunicorn, ou fournis src\server.py" -ForegroundColor Red
exit 1
