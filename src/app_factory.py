











from __future__ import annotations
import logging
from fastapi import FastAPI
from app_server.app_factory_compact import create_app as create_app_compact

logger = logging.getLogger(__name__)

# Backward-compatible entrypoint
# Splits have been moved to src/app_server/* to keep this file < 7KB.

def create_app() -> FastAPI:
    app = create_app_compact()
    try:
        # Register Workers API facade and pages
        from src.app_server.workers_api.router import router as workers_api_router
        app.include_router(workers_api_router)
    except Exception as e:
        logger.warning("[workers_api] router not registered: %s", e)
    try:
        from src.app_server.workers_pages.router import router as workers_pages_router
        app.include_router(workers_pages_router)
    except Exception as e:
        logger.warning("[workers_pages] router not registered: %s", e)
    return app
