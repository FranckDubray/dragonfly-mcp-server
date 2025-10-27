
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
        # Register Python Orchestrator live observation streaming endpoints (SSE/NDJSON)
        from src.tools._py_orchestrator.api_observe_stream import router as py_orch_observe_router
        app.include_router(py_orch_observe_router)
    except Exception as e:
        logger.warning("[py_orchestrator] observe stream router not registered: %s", e)
    return app
