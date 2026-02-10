"""Tool execution for chat_agent (parallel and sequential).

Adapted from _call_llm/tools_exec.py for consistency.
"""

from __future__ import annotations

import json
import asyncio
import logging
import requests
from typing import Any, Dict, List, Tuple

LOG = logging.getLogger(__name__)


def _trim_val(x: Any, limit: int = 2000) -> Any:
    """Trim large values for debug output."""
    try:
        if isinstance(x, dict):
            return {k: _trim_val(v, limit) for k, v in x.items()}
        if isinstance(x, list):
            if len(x) > 20:
                return [_trim_val(v, limit) for v in x[:20]] + [f"... +{len(x)-20} items"]
            return [_trim_val(v, limit) for v in x]
        if isinstance(x, str) and len(x) > limit:
            return x[:limit] + f"... (+{len(x)-limit} bytes)"
    except Exception:
        return x
    return x


def execute_tools(
    tool_calls: List[Dict[str, Any]],
    mcp_url: str,
    parallel: bool = True
) -> List[Dict[str, Any]]:
    """Execute tool calls (parallel or sequential).
    
    Args:
        tool_calls: OpenAI-format tool_calls
        mcp_url: MCP server URL
        parallel: Execute in parallel if True
    
    Returns:
        List of results with structure:
        {
            "result": <actual tool result>,
            "debug": {"url": ..., "status_code": ..., ...}
        }
    """
    if parallel and len(tool_calls) > 1:
        return _execute_parallel(tool_calls, mcp_url)
    else:
        return _execute_sequential(tool_calls, mcp_url)


def _execute_sequential(
    tool_calls: List[Dict[str, Any]],
    mcp_url: str
) -> List[Dict[str, Any]]:
    """Execute tools one by one."""
    results = []
    
    for tc in tool_calls:
        fname = tc.get("function", {}).get("name")
        args_str = tc.get("function", {}).get("arguments", "{}")
        
        try:
            args = json.loads(args_str)
        except Exception:
            args = {}
        
        result, debug_info = _execute_single_tool(fname, args, mcp_url)
        results.append({
            "result": result,
            "debug": debug_info
        })
    
    return results


def _execute_parallel(
    tool_calls: List[Dict[str, Any]],
    mcp_url: str
) -> List[Dict[str, Any]]:
    """Execute tools in parallel using asyncio."""
    
    async def execute_one(tc):
        fname = tc.get("function", {}).get("name")
        args_str = tc.get("function", {}).get("arguments", "{}")
        
        try:
            args = json.loads(args_str)
        except Exception:
            args = {}
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _execute_single_tool, fname, args, mcp_url)
    
    async def execute_all():
        tasks = [execute_one(tc) for tc in tool_calls]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    try:
        # Handle event loop
        try:
            loop = asyncio.get_running_loop()
            # Nested loop (Jupyter, etc.)
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                LOG.warning("nest_asyncio not available, falling back to sequential")
                return _execute_sequential(tool_calls, mcp_url)
            raw_results = loop.run_until_complete(execute_all())
        except RuntimeError:
            # No running loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            raw_results = loop.run_until_complete(execute_all())
            loop.close()
    
    except Exception as e:
        LOG.error(f"Parallel execution failed: {e}, falling back to sequential")
        return _execute_sequential(tool_calls, mcp_url)
    
    # Convert results to standard format
    final_results = []
    for res in raw_results:
        if isinstance(res, Exception):
            final_results.append({
                "result": {"error": str(res)},
                "debug": {"exception": str(res)}
            })
        elif isinstance(res, tuple) and len(res) == 2:
            # Normal return from _execute_single_tool
            result, debug_info = res
            final_results.append({
                "result": result,
                "debug": debug_info
            })
        else:
            # Unexpected format
            final_results.append({
                "result": res,
                "debug": {}
            })
    
    return final_results


def _execute_single_tool(
    tool_name: str, 
    args: Dict[str, Any], 
    mcp_url: str
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Execute a single MCP tool.
    
    Returns:
        Tuple of (result, debug_info)
        - result: The actual tool result (extracted from MCP response)
        - debug_info: Debug information about the call
    """
    url = f"{mcp_url}/execute"
    payload = {
        "tool": tool_name,
        "params": args
    }
    
    debug_info: Dict[str, Any] = {
        "url": url,
        "request": {"tool": tool_name, "params_keys": list(args.keys())}
    }
    
    try:
        if LOG.isEnabledFor(logging.INFO):
            LOG.info(f"Executing MCP tool: {tool_name}")
        
        resp = requests.post(url, json=payload, timeout=60)
        debug_info["status_code"] = resp.status_code
        
        if resp.status_code == 200:
            try:
                mcp_json = resp.json()
                # Extract "result" key from MCP response (standard format)
                result = mcp_json.get("result", mcp_json)
                debug_info["response_excerpt"] = _trim_val(result, 500)
                
                if LOG.isEnabledFor(logging.INFO):
                    LOG.info(f"MCP tool {tool_name} completed successfully")
                
                return result, debug_info
            except Exception as e:
                LOG.warning(f"MCP tool {tool_name} invalid JSON response: {e}")
                debug_info["parse_error"] = str(e)
                return {"error": "Invalid MCP JSON response"}, debug_info
        else:
            debug_info["response_text"] = resp.text[:500] if resp.text else None
            LOG.warning(f"MCP tool {tool_name} error: HTTP {resp.status_code}")
            return {"error": f"MCP error {resp.status_code}"}, debug_info
    
    except requests.exceptions.Timeout:
        debug_info["timeout"] = True
        return {"error": f"Tool '{tool_name}' timeout after 60s"}, debug_info
    except requests.exceptions.HTTPError as e:
        debug_info["http_error"] = str(e)
        return {"error": f"Tool '{tool_name}' HTTP error: {e}"}, debug_info
    except Exception as e:
        debug_info["exception"] = str(e)
        return {"error": f"Tool '{tool_name}' execution failed: {e}"}, debug_info
