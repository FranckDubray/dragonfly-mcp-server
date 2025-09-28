from __future__ import annotations
import os
import sys
import json
import asyncio
import logging
import importlib
import pkgutil
import time
import math
from hashlib import sha1
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from config import load_env_file, save_env_vars, mask_secret, ENV_FILE, find_project_root

logger = logging.getLogger(__name__)

MCP_HOST = os.getenv('MCP_HOST', '127.0.0.1')
MCP_PORT = int(os.getenv('MCP_PORT', '8000'))
EXECUTE_TIMEOUT_SEC = int(os.getenv('EXECUTE_TIMEOUT_SEC', '30'))
RELOAD_ENV = os.getenv('RELOAD', '').strip() == '1'
AUTO_RELOAD_TOOLS = os.getenv('AUTO_RELOAD_TOOLS', '1').strip() == '1'

# Big integers handling
BIGINT_AS_STRING = os.getenv('BIGINT_AS_STRING', '1').strip().lower() in ('1','true','yes','on')
BIGINT_STR_THRESHOLD = int(os.getenv('BIGINT_STR_THRESHOLD', '1000'))  # stringify ints when digits > threshold
# Lift Python 3.11+ safety cap for int->str to support very large factorials
try:
    if hasattr(sys, 'set_int_max_str_digits'):
        val = os.getenv('PY_INT_MAX_STR_DIGITS', '0').strip()  # 0 = unlimited
        sys.set_int_max_str_digits(0 if val == '' else int(val))
        logger.info(f"int->str max digits set to {val or 'unlimited'}")
except Exception as e:
    logger.warning(f"Could not set int max str digits: {e}")

registry: Dict[str, Dict[str, Any]] = {}
_tool_id_counter = 10000
_last_scan_time = 0
_tools_dir_mtime = 0
_tools_file_set: Set[str] = set()

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

# Fonction de sérialisation JSON safe intégrée
def sanitize_for_json(obj: Any) -> Any:
    """Recursively sanitize an object to make it JSON-compliant, incl. huge ints."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, int):
        # Optionally return large integers as strings to avoid downstream parser limits
        try:
            if BIGINT_AS_STRING:
                s = str(obj)
                if len(s) > BIGINT_STR_THRESHOLD:
                    return s
        except Exception:
            # Fallback: return as-is; global int->str cap is lifted above
            pass
        return obj
    elif isinstance(obj, float):
        if math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        elif math.isnan(obj):
            return "NaN"
        else:
            return obj
    else:
        return obj

class SafeJSONResponse(JSONResponse):
    """JSONResponse qui gère automatiquement les valeurs infinies et gros entiers"""
    def render(self, content: Any) -> bytes:
        sanitized = sanitize_for_json(content)
        return json.dumps(
            sanitized,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

# ----------------- tools discovery -----------------

def get_tools_directory_info() -> Dict[str, Any]:
    try:
        import tools as tools_package
        tools_path = Path(tools_package.__path__[0])
        if not tools_path.exists():
            return {"mtime": 0, "file_set": set(), "file_count": 0}
        tool_files = set()
        max_mtime = tools_path.stat().st_mtime
        for item in tools_path.iterdir():
            if item.name.startswith('_'):
                continue
            if item.is_file() and item.suffix == '.py':
                tool_files.add(item.name)
                max_mtime = max(max_mtime, item.stat().st_mtime)
            elif item.is_dir():
                tool_files.add(f"{item.name}/")
                max_mtime = max(max_mtime, item.stat().st_mtime)
                for subfile in item.rglob('*.py'):
                    max_mtime = max(max_mtime, subfile.stat().st_mtime)
        return {"mtime": max_mtime, "file_set": tool_files, "file_count": len(tool_files), "directory_exists": True}
    except Exception as e:
        logger.warning(f"Could not get tools directory info: {e}")
        return {"mtime": 0, "file_set": set(), "file_count": 0, "directory_exists": False}


def discover_tools():
    global registry, _last_scan_time, _tools_dir_mtime, _tool_id_counter, _tools_file_set
    _last_scan_time = time.time()
    tools_info = get_tools_directory_info()
    _tools_dir_mtime = tools_info["mtime"]
    current_file_set = tools_info["file_set"]
    added_files = current_file_set - _tools_file_set
    removed_files = _tools_file_set - current_file_set
    _tools_file_set = current_file_set
    if added_files:
        logger.info(f"🆕 New tool files detected: {added_files}")
    if removed_files:
        logger.info(f"🗑️ Removed tool files detected: {removed_files}")
    old_count = len(registry)
    registry.clear()
    _tool_id_counter = 10000
    try:
        import tools as tools_package
        tools_path = tools_package.__path__
        modules = []
        for finder, name, ispkg in pkgutil.iter_modules(tools_path):
            if name.startswith('_') or name == '__init__':
                continue
            try:
                module_name = f'tools.{name}'
                logger.info(f"🔍 Discovering {'package' if ispkg else 'module'}: {name}")
                if module_name in sys.modules:
                    logger.info(f"♻️ Reloading existing {'package' if ispkg else 'module'}: {name}")
                    importlib.reload(sys.modules[module_name])
                    module = sys.modules[module_name]
                else:
                    logger.info(f"📥 Importing new {'package' if ispkg else 'module'}: {name}")
                    module = importlib.import_module(module_name)
                modules.append((name, module, ispkg))
            except Exception as e:
                logger.error(f"❌ Failed to import {'package' if ispkg else 'module'} {name}: {e}")
        logger.info(f"🔍 Found {len(modules)} potential tool modules/packages")
        for module_name, module, ispkg in modules:
            if hasattr(module, 'run') and hasattr(module, 'spec'):
                try:
                    spec = module.spec()
                    tool_name = spec['function']['name']
                    display_name = spec['function'].get('displayName', tool_name)
                    tool_id = _tool_id_counter; _tool_id_counter += 1
                    registry[tool_name] = {
                        "id": tool_id,
                        "name": tool_name,
                        "regName": tool_name,
                        "displayName": display_name,
                        "description": spec['function']['description'],
                        "json": json.dumps(spec, separators=(",", ":"), ensure_ascii=False),
                        "func": module.run
                    }
                    pkg_info = " (package)" if ispkg else ""
                    logger.info(f"✅ Registered tool: {tool_name} (ID: {tool_id}) (from {module_name}{pkg_info}) as '{display_name}'")
                except Exception as e:
                    logger.error(f"❌ Failed to register tool from {module_name}: {e}")
            else:
                missing = []
                if not hasattr(module, 'run'):
                    missing.append('run()')
                if not hasattr(module, 'spec'):
                    missing.append('spec()')
                logger.warning(f"⚠️ {'Package' if ispkg else 'Module'} {module_name} missing {', '.join(missing)} functions")
    except ImportError as e:
        logger.error(f"❌ Failed to import tools package: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error during tool discovery: {e}")
    new_count = len(registry)
    if new_count != old_count:
        logger.info(f"🔄 Tool count changed: {old_count} → {new_count}")
        if new_count > old_count: logger.info(f"🎉 {new_count - old_count} new tool(s) discovered!")
        elif new_count < old_count: logger.info(f"🧹 {old_count - new_count} tool(s) removed")
    logger.info(f"🔧 Tool discovery complete. Registered {new_count} tools: {list(registry.keys())}")


def should_reload(request: Request) -> bool:
    global _last_scan_time, _tools_dir_mtime, _tools_file_set
    if RELOAD_ENV or request.query_params.get('reload') == '1':
        logger.info("🔄 Force reload requested")
        return True
    if len(registry) == 0:
        logger.info("🔄 No tools registered, reloading")
        return True
    if AUTO_RELOAD_TOOLS:
        tools_info = get_tools_directory_info()
        current_mtime = tools_info["mtime"]
        current_file_set = tools_info["file_set"]
        if current_mtime > _tools_dir_mtime:
            logger.info(f"🔄 Tools directory modified (mtime: {_tools_dir_mtime} → {current_mtime})")
            return True
        if current_file_set != _tools_file_set:
            added = current_file_set - _tools_file_set
            removed = _tools_file_set - current_file_set
            if added:
                logger.info(f"🔄 New tools detected: {added}")
                return True
            if removed:
                logger.info(f"🔄 Tools removed: {removed}")
                return True
    return False

# ----------------- app factory -----------------

def create_app() -> FastAPI:
    app = FastAPI(title="MCP Server", description="Minimal MCP Server Implementation", version="1.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET","POST","OPTIONS"], allow_headers=["*"], allow_credentials=True)

    from fastapi.exceptions import RequestValidationError
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"❌ Validation error: {exc.errors()}")
        body = await request.body()
        logger.error(f"❌ Request body: {body}")
        return SafeJSONResponse(content={"detail":"Validation error","errors":exc.errors(),"body":body.decode() if body else "empty"}, status_code=422)

    @app.options("/tools")
    async def tools_options():
        return Response(status_code=204)

    @app.get("/tools")
    async def get_tools(request: Request):
        if should_reload(request):
            logger.info("🔄 Auto-reloading tools...")
            discover_tools()
        items = []
        for tool in registry.values():
            item = {k: v for k, v in tool.items() if k != 'func'}
            items.append(item)
        items.sort(key=lambda x: x.get("name", ""))
        payload = json.dumps(sanitize_for_json(items), separators=(",", ":"), ensure_ascii=False)
        etag = sha1(payload.encode("utf-8")).hexdigest()
        if request.headers.get("If-None-Match") == etag:
            return Response(status_code=304)
        return Response(content=payload, media_type="application/json", headers={"Cache-Control":"no-cache","ETag": etag})

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
            return SafeJSONResponse(content={"status":"ok","received":json_data})
        except Exception as e:
            logger.error(f"🐛 Debug error: {e}")
            return SafeJSONResponse(content={"error": str(e)})

    @app.post("/execute")
    async def execute_tool(request: ExecuteRequest):
        if AUTO_RELOAD_TOOLS and should_reload(Request(scope={"type":"http","method":"POST","query_string": b""})):
            logger.info("🔄 Auto-reloading tools before execution...")
            discover_tools()
        if len(registry) == 0:
            discover_tools()
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
            raise HTTPException(status_code=500, detail=f"Execution error: {e}")

    @app.get("/config")
    async def get_config():
        gh = os.getenv('GITHUB_TOKEN')
        ai = os.getenv('AI_PORTAL_TOKEN')
        llm_ep = os.getenv('LLM_ENDPOINT', '')
        return SafeJSONResponse(content={
            "GITHUB_TOKEN": {"present": bool(gh), "masked": mask_secret(gh)},
            "AI_PORTAL_TOKEN": {"present": bool(ai), "masked": mask_secret(ai)},
            "LLM_ENDPOINT": llm_ep,
            "env_file": str(ENV_FILE)
        })

    @app.post("/config")
    async def set_config(update: ConfigUpdate):
        try:
            payload = update.dict()
            result = save_env_vars(payload)
            return SafeJSONResponse(content={"success": True, **result})
        except Exception as e:
            logger.exception("Failed to save config")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/control", response_class=HTMLResponse)
    async def control_dashboard():
        from ui_html import CONTROL_HTML
        return HTMLResponse(content=CONTROL_HTML)

    @app.get("/control.js")
    async def control_js(request: Request):
        from ui_js import CONTROL_JS
        return Response(content=CONTROL_JS, media_type="application/javascript")

    @app.on_event("startup")
    async def startup_event():
        logger.info("🚀 Starting MCP Server with Safe JSON handling...")
        load_env_file()
        discover_tools()
        logger.info(f"🔧 Server ready with {len(registry)} tools")
        logger.info(f"📁 Project root: {find_project_root()}")
        if AUTO_RELOAD_TOOLS:
            logger.info("🔄 Auto-reload enabled - New tools will be detected automatically")
        else:
            logger.info("📌 Auto-reload disabled - Use ?reload=1 or restart server for new tools")

    return app
