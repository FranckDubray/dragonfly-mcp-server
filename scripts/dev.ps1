#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

# Always operate from repo root (relative paths only)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptDir "..")

# Detect venv python
if ($env:VIRTUAL_ENV) {
  $py = (Get-Command python).Source
} else {
  Write-Warning "[dev.ps1] No venv detected (VIRTUAL_ENV empty)."
  $py = "python"
}

Write-Host "[dev.ps1] 🔧 Python: " -NoNewline; & $py --version

Write-Host "[dev.ps1] 📦 Installing Playwright browsers (scoped to ./playwright/browsers)"
$env:PLAYWRIGHT_BROWSERS_PATH = "playwright/browsers"
try { & $py -m playwright install chromium } catch { Write-Warning $_ }

# Generate tools catalog if present
if (Test-Path "scripts/generate_tools_catalog.py") {
  Write-Host "[dev.ps1] 🧠 Generating tools catalog"
  try { & $py scripts/generate_tools_catalog.py } catch { Write-Warning $_ }
}

Write-Host "[dev.ps1] 🚀 Starting server"
& $py src/server.py
