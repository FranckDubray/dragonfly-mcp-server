#!/usr/bin/env python3
import os
import sys
import logging
import uvicorn
from fastapi import FastAPI

# --- Load .env as early as possible (no external deps required) ---
# Tries python-dotenv if available, otherwise a tiny fallback parser.
try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
    _dotenv_path = find_dotenv(usecwd=True)
    if _dotenv_path:
        load_dotenv(_dotenv_path, override=False)
except Exception:
    # Fallback: minimal .env loader (KEY=VALUE, ignores # comments)
    env_path = os.path.join(os.getcwd(), '.env')
    if os.path.isfile(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith('#'):
                        continue
                    if '=' in s:
                        k, v = s.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        os.environ.setdefault(k, v)
        except Exception:
            pass

# Development mode: add src to path (if running from project root)
if os.path.isdir('src') and 'src' not in sys.path:
    sys.path.insert(0, 'src')

# Configure logging BEFORE importing app
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO').upper(),
    format='%(levelname)s:     %(message)s',
    handlers=[logging.StreamHandler()]
)

# Flat layout import only (old packaged layout removed)
from app_factory import create_app  # src/app_factory.py

MCP_HOST = os.getenv('MCP_HOST', '127.0.0.1')
MCP_PORT = int(os.getenv('MCP_PORT', '8000'))

app: FastAPI = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=MCP_HOST,
        port=MCP_PORT,
        reload=False,
        log_level=os.getenv('LOG_LEVEL', 'info').lower(),
        access_log=False  # Disable Uvicorn access logs (we have custom logs)
    )
