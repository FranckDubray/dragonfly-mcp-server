
# MCP Server Development Script (PowerShell)

param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000,
    [string]$LogLevel = "INFO"
)

Write-Host "🚀 Starting MCP Server (Development Mode)" -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "❌ Error: pyproject.toml not found. Run this script from the project root." -ForegroundColor Red
    exit 1
}

# Check Python version (>= 3.11)
try {
    $version = & python -c @"
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
"@
    if (-not $version) { throw "Python not found" }
    $parts = $version.Split('.')
    $maj = [int]$parts[0]
    $min = [int]$parts[1]
    if ($maj -lt 3 -or ($maj -eq 3 -and $min -lt 11)) {
        Write-Host "❌ Python $version detected, but 3.11+ is required. Aborting." -ForegroundColor Red
        Write-Host "Tip: install via pyenv-win/conda or from python.org" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "🐍 Using Python $version" -ForegroundColor Yellow
} catch {
    Write-Host "❌ Error: Python 3.11+ not found. Please install and add to PATH." -ForegroundColor Red
    exit 1
}

# Create .env from .env.example if not exists
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "📝 No .env found, creating from .env.example..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Created .env from template" -ForegroundColor Green
        Write-Host "⚠️  Please edit .env and fill in your tokens/passwords before starting" -ForegroundColor Yellow
        Write-Host "   notepad .env" -ForegroundColor Yellow
        $null = Read-Host "Press Enter to continue or Ctrl+C to exit and edit .env"
    } else {
        Write-Host "⚠️  Warning: No .env or .env.example found" -ForegroundColor Yellow
        Write-Host "   The server will start with default values" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ Found existing .env" -ForegroundColor Green
}

# Load .env if present (export)
if (Test-Path ".env") {
    Write-Host "🔑 Loading .env..." -ForegroundColor Yellow
    Get-Content .env | ForEach-Object {
        if ($_ -match "^\s*#") { return }
        if (-not ($_ -match "=")) { return }
        $kv = $_.Split("=",2)
        $k = $kv[0].Trim()
        $v = $kv[1].Trim().Trim('"').Trim("'")
        if ($k) { 
            Set-Item -Path "Env:$k" -Value $v
        }
    }
}

# Create venv if needed
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install/upgrade dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install --quiet --upgrade pip
pip install --quiet -e ".[dev]"

# Optional extras (parité avec dev.sh)
python -c "import pypdf" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "📄 Installing pypdf (PDF support)..." -ForegroundColor Yellow
    pip install --quiet "pypdf>=4.2.0"
} else {
    Write-Host "📄 pypdf available" -ForegroundColor Green
}

python -c "import sympy" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "∑ Installing SymPy (symbolic math)..." -ForegroundColor Yellow
    pip install --quiet "sympy>=1.12.0"
} else {
    Write-Host "∑ SymPy available" -ForegroundColor Green
}

python -c "import requests" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "🌐 Installing requests (HTTP client)..." -ForegroundColor Yellow
    pip install --quiet "requests>=2.31.0"
} else {
    Write-Host "🌐 requests available" -ForegroundColor Green
}

# Native video decoding requirements (PyAV + NumPy)
python -c "import numpy" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "🧮 Installing NumPy..." -ForegroundColor Yellow
    pip install --quiet "numpy>=1.23.0"
} else {
    Write-Host "🧮 NumPy available" -ForegroundColor Green
}

python -c "import av" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "🎞️  Installing PyAV (native video decode)..." -ForegroundColor Yellow
    pip install --quiet "av>=10.0.0"
} else {
    Write-Host "🎞️  PyAV available" -ForegroundColor Green
}

# Generate tools catalog (auto)
Write-Host "🧰 Generating tools catalog (src/tools/README.md)..." -ForegroundColor Yellow
python scripts/generate_tools_catalog.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: failed to generate tools catalog" -ForegroundColor Yellow
}

# Environment variables (use .env values if already set)
if (-not $env:MCP_HOST) { $env:MCP_HOST = "127.0.0.1" }
if (-not $env:MCP_PORT) { $env:MCP_PORT = "8000" }
if (-not $env:LOG_LEVEL) { $env:LOG_LEVEL = "INFO" }
if (-not $env:AUTO_RELOAD_TOOLS) { $env:AUTO_RELOAD_TOOLS = "1" }
if (-not $env:EXECUTE_TIMEOUT_SEC) { $env:EXECUTE_TIMEOUT_SEC = "300" }

Write-Host "🌐 Server Configuration:" -ForegroundColor Green
Write-Host "  Host: $($env:MCP_HOST)"
Write-Host "  Port: $($env:MCP_PORT)"
Write-Host "  Log Level: $($env:LOG_LEVEL)"
Write-Host "  Auto Reload Tools: $($env:AUTO_RELOAD_TOOLS)"
Write-Host "  Timeout: $($env:EXECUTE_TIMEOUT_SEC)s"

Write-Host "🔗 URLs:" -ForegroundColor Green
Write-Host "  API Base: http://$($env:MCP_HOST):$($env:MCP_PORT)"
Write-Host "  Tools: http://$($env:MCP_HOST):$($env:MCP_PORT)/tools"
Write-Host "  Control Panel: http://$($env:MCP_HOST):$($env:MCP_PORT)/control"
Write-Host "  Config: http://$($env:MCP_HOST):$($env:MCP_PORT)/config"

Write-Host "▶️  Starting server..." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Yellow

# Start the server (flat layout)
Set-Location src
python -m server
