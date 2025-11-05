import json
import time
import asyncio
import logging
from hashlib import sha1
from typing import Dict, Any, Optional
from collections.abc import Iterator

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import find_project_root
from app_core.safe_json import SafeJSONResponse, sanitize_for_json, strip_surrogates
from app_core.tool_discovery import (
    get_registry,
    discover_tools,
    should_reload as should_reload_tools,
    get_last_errors,
)

logger = logging.getLogger(__name__)

AUTO_RELOAD_TOOLS = True
RELOAD_ENV = False
EXECUTE_TIMEOUT_SEC = 180

class ExecuteRequest(BaseModel):
    tool_reg: Optional[str] = None
    tool: Optional[str] = None
    params: Dict[str, Any]

    def get_tool_name(self) -> str:
        return self.tool_reg or self.tool or ''

async def head_tools(request: Request):
    registry = get_registry()
    if should_reload_tools(request, AUTO_RELOAD_TOOLS, RELOAD_ENV, len(registry)):
        discover_tools(); registry = get_registry()
    items = []
    for tool in registry.values():
        item = {k: v for k, v in tool.items() if k != 'func'}
        items.append(item)
    items.sort(key=lambda x: x.get("name", ""))
    payload = json.dumps(sanitize_for_json(items), separators=(",", ":"), ensure_ascii=False)
    etag = sha1(payload.encode("utf-8")).hexdigest()
    return Response(status_code=200, headers={"Cache-Control": "no-cache", "ETag": etag})

async def get_tools(request: Request, auto_reload: bool, reload_env: bool):
    registry = get_registry()
    reload_flag = request.query_params.get('reload') == '1'
    list_flag = request.query_params.get('list') == '1'

    if should_reload_tools(request, auto_reload, reload_env, len(registry)) or reload_flag:
        logger.info("🔄 Reloading tools (explicit or auto)")
        discover_tools(); registry = get_registry()
        if reload_flag and not list_flag:
            errors = get_last_errors()
            return SafeJSONResponse(content={
                "reloaded": True,
                "tool_count": len(registry),
                "errors": errors,
            })

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

async def post_debug(request: Request):
    try:
        body = await request.body()
        logger.info(f"🐞 Debug - Raw body: {body}")
        json_data = json.loads(body)
        logger.info(f"🐞 Debug - Parsed JSON: {json_data}")
        return SafeJSONResponse(content={"status": "ok", "received": json_data})
    except Exception as e:
        logger.error(f"🐞 Debug error: {e}")
        return SafeJSONResponse(content={"error": str(e)})

async def post_execute(request: ExecuteRequest, auto_reload: bool, reload_env: bool, execute_timeout: int):
    registry = get_registry()
    fake_req = Request(scope={"type": "http", "method": "POST", "query_string": b""})
    if auto_reload and should_reload_tools(fake_req, auto_reload, reload_env, len(registry)):
        logger.info("🔄 Auto-reloading tools before execution...")
        discover_tools(); registry = get_registry()
    if len(registry) == 0:
        discover_tools(); registry = get_registry()
    tool_name = request.get_tool_name()
    params = request.params

    if tool_name not in registry:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    tool = registry[tool_name]
    display_name = tool.get('displayName', tool_name)
    func = tool['func']

    logger.info(f"🔧 Executing '{display_name}' ({tool_name})")
    start_time = time.perf_counter()

    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(loop.run_in_executor(None, lambda: func(**params)), timeout=execute_timeout)
        duration = time.perf_counter() - start_time
        logger.info(f"✅ '{display_name}' completed in {duration:.3f}s")
        
        # 🆕 DÉTECTION DES GENERATORS : Stream SSE
        if isinstance(result, Iterator):
            logger.info(f"🌊 Streaming response detected for '{display_name}'")
            
            async def event_stream():
                try:
                    for chunk in result:
                        # ✅ FORMAT SSE STANDARD : {json}\n\n
                        chunk_json = json.dumps(sanitize_for_json(chunk), ensure_ascii=False)
                        yield f"data: {chunk_json}\n\n"
                except Exception as e:
                    error_chunk = {"chunk_type": "error", "error": {"message": str(e)[:200]}, "terminal": True}
                    yield f"{json.dumps(error_chunk)}\n\n"
            
            return StreamingResponse(
                event_stream(), 
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
                }
            )
        
        # Mode normal (non-streaming)
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
