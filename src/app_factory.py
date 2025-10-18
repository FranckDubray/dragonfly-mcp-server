
from __future__ import annotations
import logging
from fastapi import FastAPI
from app_server.app_factory_compact import create_app as create_app_compact

logger = logging.getLogger(__name__)

# Backward-compatible entrypoint
# Splits have been moved to src/app_server/* to keep this file < 7KB.

def create_app() -> FastAPI:
    return create_app_compact()
