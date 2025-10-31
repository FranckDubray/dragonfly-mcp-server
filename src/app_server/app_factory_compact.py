
from __future__ import annotations
import os
import json
import time
import asyncio
import logging
from hashlib import sha1
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from config import (
    load_env_file, 
    save_env_vars, 
    get_all_env_vars,
    find_project_root
)
from app_core.safe_json import SafeJSONResponse, sanitize_for_json, strip_surrogates
from app_core.tool_discovery import get_registry, discover_tools, should_reload as should_reload_tools, get_last_errors

from .static_mount import mount_static_and_assets
from .tools_routes import ExecuteRequest, head_tools, get_tools, post_debug, post_execute

logger = logging.getLogger(__name__)

MCP_HOST = os.getenv('MCP_HOST', '127.0.0.1')
MCP_PORT = int(os.getenv('MCP_PORT', '8000'))
EXECUTE_TIMEOUT_SEC = int(os.getenv('EXECUTE_TIMEOUT_SEC', '180'))
RELOAD_ENV = os.getenv('RELOAD', '').strip() == '1'
AUTO_RELOAD_TOOLS = os.getenv('AUTO_RELOAD_TOOLS', '1').strip() == '1'


def create_app() -> FastAPI:
    app = FastAPI(title="MCP Server", description="Minimal MCP Server Implementation", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    # Mount static and assets
    project_root = find_project_root()
    mount_static_and_assets(app, project_root)

    # ----- Validation error handler -----
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"❌ Validation error: {exc.errors()}")
        body = await request.body()
        logger.error(f"❌ Request body: {body}")
        return SafeJSONResponse(
            content={"detail": "Validation error", "errors": exc.errors(), "body": body.decode() if body else "empty"},
            status_code=422,
        )

    # ----- Tools endpoints -----
    @app.options("/tools")
    async def tools_options():
        return Response(status_code=204)

    @app.head("/tools")
    async def tools_head(request: Request):
        return await head_tools(request)

    @app.get("/tools")
    async def tools_get(request: Request):
        return await get_tools(request, AUTO_RELOAD_TOOLS, RELOAD_ENV)

    @app.post("/debug")
    async def debug_endpoint(request: Request):
        return await post_debug(request)

    @app.post("/execute")
    async def execute_endpoint(request: ExecuteRequest):
        return await post_execute(request, AUTO_RELOAD_TOOLS, RELOAD_ENV, EXECUTE_TIMEOUT_SEC)

    # ----- Config (GENERIC) -----
    @app.get("/config")
    async def get_config():
        return SafeJSONResponse(content=get_all_env_vars())

    @app.post("/config")
    async def set_config(request: Request):
        try:
            body = await request.body()
            payload = json.loads(body)
            result = save_env_vars(payload)
            return SafeJSONResponse(content={"success": True, **result})
        except Exception as e:
            logger.exception("Failed to save config")
            raise HTTPException(status_code=500, detail=str(e))

    # ----- UI -----
    @app.get("/control", response_class=HTMLResponse)
    async def control_dashboard(request: Request):
        try:
            from ui_html import CONTROL_HTML
            return HTMLResponse(content=CONTROL_HTML)
        except Exception as e:
            logger.exception("Failed to import CONTROL_HTML; serving fallback control page")
            fallback = """
            <!doctype html>
            <html><head><meta charset='utf-8'><title>Control Panel</title>
            <style>body{font-family:system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;padding:24px}</style>
            </head><body>
            <h1>Control Panel (fallback)</h1>
            <p>Le template Control n'a pas pu être chargé.<br>Erreur: %s</p>
            </body></html>
            """ % (str(e).replace('<','&lt;'))
            return HTMLResponse(content=fallback, status_code=200)

    @app.get("/logo")
    async def get_logo():
        project_root = find_project_root()
        logo_path = project_root / "assets" / "LOGO_DRAGONFLY_HD.jpg"
        if not logo_path.exists():
            raise HTTPException(status_code=404, detail="Logo not found")
        return FileResponse(logo_path, media_type="image/jpeg")

    # ----- Startup -----
    @app.on_event("startup")
    async def startup_event():
        logger.info("🚀 Starting MCP Server with Safe JSON handling...")
        load_env_file()
        discover_tools()
        logger.info(f"🔧 Server ready with {len(get_registry())} tools")
        logger.info(f"📁 Project root: {find_project_root()}")
        if AUTO_RELOAD_TOOLS:
            logger.info("🔄 Auto-reload enabled - New tools will be detected automatically")
        else:
            logger.info("📎 Auto-reload disabled - Use ?reload=1 or restart server for new tools")

    return app
