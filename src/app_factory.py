







from __future__ import annotations
import os
import sys
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
    get_all_env_vars,  # NEW: generic env loader
    ENV_FILE, 
    find_project_root
)

# New split modules
from app_core.safe_json import SafeJSONResponse, sanitize_for_json, strip_surrogates
from app_core.tool_discovery import (
    get_registry,
    discover_tools,
    should_reload as should_reload_tools,
)

logger = logging.getLogger(__name__)

# ----------------- Env knobs -----------------
MCP_HOST = os.getenv('MCP_HOST', '127.0.0.1')
MCP_PORT = int(os.getenv('MCP_PORT', '8000'))
EXECUTE_TIMEOUT_SEC = int(os.getenv('EXECUTE_TIMEOUT_SEC', '180'))
RELOAD_ENV = os.getenv('RELOAD', '').strip() == '1'
AUTO_RELOAD_TOOLS = os.getenv('AUTO_RELOAD_TOOLS', '1').strip() == '1'

# ----------------- Pydantic models -----------------
class ExecuteRequest(BaseModel):
    tool_reg: Optional[str] = None
    tool: Optional[str] = None
    params: Dict[str, Any]

    def get_tool_name(self) -> str:
        return self.tool_reg or self.tool or ''

# ConfigUpdate is now completely generic (accepts any key/value)
class ConfigUpdate(BaseModel):
    class Config:
        extra = 'allow'  # Accept any extra fields dynamically

# ----------------- App factory -----------------

def create_app() -> FastAPI:
    app = FastAPI(title="MCP Server", description="Minimal MCP Server Implementation", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        allow_credentials=True,
    )

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

    # ----- Tools listing -----
    @app.options("/tools")
    async def tools_options():
        return Response(status_code=204)

    @app.head("/tools")
    async def tools_head(request: Request):
        """HEAD endpoint for ETag checking without payload (used by auto-reload)."""
        registry = get_registry()
        if should_reload_tools(request, AUTO_RELOAD_TOOLS, RELOAD_ENV, len(registry)):
            discover_tools()
            registry = get_registry()
        # Build minimal payload for ETag calculation
        items = []
        for tool in registry.values():
            item = {k: v for k, v in tool.items() if k != 'func'}
            items.append(item)
        items.sort(key=lambda x: x.get("name", ""))
        payload = json.dumps(sanitize_for_json(items), separators=(",", ":"), ensure_ascii=False)
        etag = sha1(payload.encode("utf-8")).hexdigest()
        return Response(status_code=200, headers={"Cache-Control": "no-cache", "ETag": etag})

    @app.get("/tools")
    async def get_tools(request: Request):
        registry = get_registry()
        if should_reload_tools(request, AUTO_RELOAD_TOOLS, RELOAD_ENV, len(registry)):
            logger.info("🔄 Auto-reloading tools...")
            discover_tools()
            registry = get_registry()
        # Build public items (without callables)
        items = []
        for tool in registry.values():
            item = {k: v for k, v in tool.items() if k != 'func'}
            items.append(item)
        items.sort(key=lambda x: x.get("name", ""))
        payload = json.dumps(sanitize_for_json(items), separators=(",", ":"), ensure_ascii=False)
        etag = sha1(payload.encode("utf-8")).hexdigest()
        if request.headers.get("If-None-Match") == etag:
            return Response(status_code=304)
        return Response(content=payload, media_type="application/json", headers={"Cache-Control": "no-cache", "ETag": etag})

    # ----- Execute -----
    @app.options("/execute")
    async def execute_options():
        return Response(status_code=204)

    @app.post("/debug")
    async def debug_execute(request: Request):
        try:
            body = await request.body()
            logger.info(f"🐛 Debug - Raw body: {body}")
            json_data = json.loads(body)
            logger.info(f"🐛 Debug - Parsed JSON: {json_data}")
            exec_req = ExecuteRequest(**json_data)
            logger.info(f"🐛 Debug - ExecuteRequest created: {exec_req}")
            return SafeJSONResponse(content={"status": "ok", "received": json_data})
        except Exception as e:
            logger.error(f"🐛 Debug error: {e}")
            return SafeJSONResponse(content={"error": str(e)})

    @app.post("/execute")
    async def execute_tool(request: ExecuteRequest):
        registry = get_registry()
        # Create a fake req for reload trigger in POST context
        fake_req = Request(scope={"type": "http", "method": "POST", "query_string": b""})
        if AUTO_RELOAD_TOOLS and should_reload_tools(fake_req, AUTO_RELOAD_TOOLS, RELOAD_ENV, len(registry)):
            logger.info("🔄 Auto-reloading tools before execution...")
            discover_tools()
            registry = get_registry()
        if len(registry) == 0:
            discover_tools()
            registry = get_registry()
        tool_name = request.get_tool_name()
        params = request.params
        
        if tool_name not in registry:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        tool = registry[tool_name]
        display_name = tool.get('displayName', tool_name)
        func = tool['func']
        
        # Log start with displayName
        logger.info(f"🔧 Executing '{display_name}' ({tool_name})")
        
        # Start timer
        start_time = time.perf_counter()
        
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(loop.run_in_executor(None, lambda: func(**params)), timeout=EXECUTE_TIMEOUT_SEC)
            
            # Calculate duration
            duration = time.perf_counter() - start_time
            
            # Log success with timing
            logger.info(f"✅ '{display_name}' completed in {duration:.3f}s")
            
            return SafeJSONResponse(content={"result": result})
        except asyncio.TimeoutError:
            duration = time.perf_counter() - start_time
            logger.error(f"⏱️ '{display_name}' timed out after {duration:.3f}s")
            raise HTTPException(status_code=504, detail="Tool execution timed out")
        except TypeError as e:
            duration = time.perf_counter() - start_time
            if "unexpected keyword argument" in str(e) or "missing" in str(e):
                logger.error(f"❌ '{display_name}' failed after {duration:.3f}s: Invalid parameters")
                raise HTTPException(status_code=400, detail=f"Invalid parameters: {e}")
            logger.error(f"❌ '{display_name}' failed after {duration:.3f}s: {e}")
            raise HTTPException(status_code=500, detail=f"Execution error: {e}")
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(f"❌ '{display_name}' failed after {duration:.3f}s: {e}")
            return SafeJSONResponse(
                content={
                    "error": "Execution error",
                    "detail": strip_surrogates(str(e)),
                    "tool": tool_name,
                },
                status_code=500,
            )

    # ----- Config (GENERIC) -----
    @app.get("/config")
    async def get_config():
        """Return all env vars from .env with metadata (generic)."""
        return SafeJSONResponse(content=get_all_env_vars())

    @app.post("/config")
    async def set_config(request: Request):
        """Save any env vars to .env (generic)."""
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
    async def control_dashboard():
        from ui_html import CONTROL_HTML
        return HTMLResponse(content=CONTROL_HTML)

    @app.get("/control.js")
    async def control_js(request: Request):
        from ui_js import CONTROL_JS
        return Response(content=CONTROL_JS, media_type="application/javascript")

    @app.get("/logo")
    async def get_logo():
        """Serve Dragonfly logo for control panel."""
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
            logger.info("📌 Auto-reload disabled - Use ?reload=1 or restart server for new tools")

    return app
