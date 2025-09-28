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

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "🐍 Using $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "❌ Error: Python not found. Please install Python 3.8+ and add it to PATH." -ForegroundColor Red
    exit 1
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

# Environment variables
$env:MCP_HOST = $Host
$env:MCP_PORT = $Port.ToString()
$env:LOG_LEVEL = $LogLevel
$env:RELOAD = "1"
$env:AUTO_RELOAD_TOOLS = "1"
$env:EXECUTE_TIMEOUT_SEC = "30"

Write-Host "🌐 Server Configuration:" -ForegroundColor Green
Write-Host "  Host: $($env:MCP_HOST)"
Write-Host "  Port: $($env:MCP_PORT)"
Write-Host "  Log Level: $($env:LOG_LEVEL)"
Write-Host "  Hot Reload: $($env:RELOAD)"
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
