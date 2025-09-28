#!/usr/bin/env python3
import os
import sys
import uvicorn
from fastapi import FastAPI

# Development mode: add src to path (if running from project root)
if os.path.isdir('src') and 'src' not in sys.path:
    sys.path.insert(0, 'src')

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
        log_level=os.getenv('LOG_LEVEL', 'info').lower()
    )
