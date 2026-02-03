"""Tool execution for chat_agent (parallel and sequential).

Adapted from _call_llm_agent/executor.py for independence.
"""

from __future__ import annotations

import json
import asyncio
import logging
import requests
from typing import Any, Dict, List

LOG = logging.getLogger(__name__)


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
        List of results (one per tool_call)
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
        
        result = _execute_single_tool(fname, args, mcp_url)
        results.append(result)
    
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
            results = loop.run_until_complete(execute_all())
        except RuntimeError:
            # No running loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(execute_all())
            loop.close()
    
    except Exception as e:
        LOG.error(f"Parallel execution failed: {e}, falling back to sequential")
        return _execute_sequential(tool_calls, mcp_url)
    
    # Convert exceptions to error dicts
    final_results = []
    for res in results:
        if isinstance(res, Exception):
            final_results.append({"error": str(res)})
        else:
            final_results.append(res)
    
    return final_results


def _execute_single_tool(tool_name: str, args: Dict[str, Any], mcp_url: str) -> Dict[str, Any]:
    """Execute a single MCP tool.
    
    Returns:
        Result dict or error dict
    """
    url = f"{mcp_url}/execute"
    payload = {
        "tool": tool_name,
        "params": args
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()
    
    except requests.exceptions.Timeout:
        return {"error": f"Tool '{tool_name}' timeout after 60s"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"Tool '{tool_name}' HTTP error: {e}"}
    except Exception as e:
        return {"error": f"Tool '{tool_name}' execution failed: {e}"}
