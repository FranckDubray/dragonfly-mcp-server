from __future__ import annotations
import os
import sys
import json
import asyncio
import logging
from hashlib import sha1
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from config import load_env_file, save_env_vars, mask_secret, ENV_FILE, find_project_root

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

class ConfigUpdate(BaseModel):
    GITHUB_TOKEN: Optional[str] = None
    AI_PORTAL_TOKEN: Optional[str] = None
    LLM_ENDPOINT: Optional[str] = None
    # New: allow editing timeouts from /control
    EXECUTE_TIMEOUT_SEC: Optional[str] = None
    LLM_REQUEST_TIMEOUT_SEC: Optional[str] = None
    SCRIPT_TIMEOUT_SEC: Optional[str] = None

# ----------------- App factory -----------------

def create_app() -> FastAPI:
    app = FastAPI(title="MCP Server", description="Minimal MCP Server Implementation", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS"],
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
        logger.info(f"🔧 Executing tool: {tool_name} with params: {params}")
        if tool_name not in registry:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        tool = registry[tool_name]
        func = tool['func']
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(loop.run_in_executor(None, lambda: func(**params)), timeout=EXECUTE_TIMEOUT_SEC)
            return SafeJSONResponse(content={"result": result})
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Tool execution timed out")
        except TypeError as e:
            if "unexpected keyword argument" in str(e) or "missing" in str(e):
                raise HTTPException(status_code=400, detail=f"Invalid parameters: {e}")
            raise HTTPException(status_code=500, detail=f"Execution error: {e}")
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return SafeJSONResponse(
                content={
                    "error": "Execution error",
                    "detail": strip_surrogates(str(e)),
                    "tool": tool_name,
                },
                status_code=500,
            )

    # ----- Config -----
    @app.get("/config")
    async def get_config():
        gh = os.getenv('GITHUB_TOKEN')
        ai = os.getenv('AI_PORTAL_TOKEN')
        llm_ep = os.getenv('LLM_ENDPOINT', '')
        return SafeJSONResponse(
            content={
                "GITHUB_TOKEN": {"present": bool(gh), "masked": mask_secret(gh)},
                "AI_PORTAL_TOKEN": {"present": bool(ai), "masked": mask_secret(ai)},
                "LLM_ENDPOINT": llm_ep,
                # New: expose timeouts
                "EXECUTE_TIMEOUT_SEC": os.getenv('EXECUTE_TIMEOUT_SEC', ''),
                "LLM_REQUEST_TIMEOUT_SEC": os.getenv('LLM_REQUEST_TIMEOUT_SEC', ''),
                "SCRIPT_TIMEOUT_SEC": os.getenv('SCRIPT_TIMEOUT_SEC', ''),
                "env_file": str(ENV_FILE),
            }
        )

    @app.post("/config")
    async def set_config(update: ConfigUpdate):
        try:
            payload = update.dict()
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
