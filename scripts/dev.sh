#!/bin/bash
# MCP Server Development Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting MCP Server (Development Mode)${NC}"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: pyproject.toml not found. Run this script from the project root.${NC}"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${YELLOW}🐍 Using Python $python_version${NC}"

# Create venv if needed
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
# shellcheck disable=SC1091
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -e ".[dev]"

# Optional extras used by some tools
if ! python -c "import pypdf" >/dev/null 2>&1; then
  echo -e "${YELLOW}📄 Installing pypdf (PDF support)...${NC}"
  pip install -q "pypdf>=4.2.0"
else
  echo -e "${GREEN}📄 pypdf available${NC}"
fi

if ! python -c "import sympy" >/dev/null 2>&1; then
  echo -e "${YELLOW}🔢 Installing SymPy (symbolic math)...${NC}"
  pip install -q "sympy>=1.12.0"
else
  echo -e "${GREEN}🔢 SymPy available${NC}"
fi

if ! python -c "import requests" >/dev/null 2>&1; then
  echo -e "${YELLOW}🌐 Installing requests (HTTP client)...${NC}"
  pip install -q "requests>=2.31.0"
else
  echo -e "${GREEN}🌐 requests available${NC}"
fi

# Environment variables
export MCP_HOST="${MCP_HOST:-127.0.0.1}"
export MCP_PORT="${MCP_PORT:-8000}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export RELOAD="${RELOAD:-1}"
export EXECUTE_TIMEOUT_SEC="${EXECUTE_TIMEOUT_SEC:-30}"
export AUTO_RELOAD_TOOLS="${AUTO_RELOAD_TOOLS:-1}"

echo -e "${GREEN}🌐 Server Configuration:${NC}"
echo -e "  Host: ${MCP_HOST}"
echo -e "  Port: ${MCP_PORT}"
echo -e "  Log Level: ${LOG_LEVEL}"
echo -e "  Hot Reload (legacy RELOAD): ${RELOAD}"
echo -e "  Auto Reload Tools: ${AUTO_RELOAD_TOOLS}"
echo -e "  Timeout: ${EXECUTE_TIMEOUT_SEC}s"

echo -e "${GREEN}🔗 URLs:${NC}"
echo -e "  API Base: http://${MCP_HOST}:${MCP_PORT}"
echo -e "  Tools: http://${MCP_HOST}:${MCP_PORT}/tools"
echo -e "  Control Panel: http://${MCP_HOST}:${MCP_PORT}/control"
echo -e "  Config: http://${MCP_HOST}:${MCP_PORT}/config"

echo -e "${GREEN}▶️  Starting server...${NC}"
echo -e "${YELLOW}   Press Ctrl+C to stop${NC}"

# Start the server (flat layout)
cd src && python -m server
