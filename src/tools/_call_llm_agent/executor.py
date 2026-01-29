from __future__ import annotations
"""
Parallel and sequential execution of MCP tools.
"""
from typing import Any, Dict, List
import asyncio
import json
import logging
import sys

LOG = logging.getLogger(__name__)

# Import from parent _call_llm package
try:
    from ..call_llm import execute_mcp_tool
except ImportError:
    # Fallback: direct import from tools_exec
    sys.path.insert(0, ".")
    from src.tools._call_llm.tools_exec import execute_mcp_tool


def execute_tools_sequential(
    tool_calls: List[Dict[str, Any]],
    name_to_reg: Dict[str, str],
    mcp_url: str,
    early_stop_on_error: bool,
) -> List[Dict[str, Any]]:
    """Execute tools one by one (sequential)."""
    results = []
    for tc in tool_calls:
        fname = (tc.get("function") or {}).get("name")
        args_str = (tc.get("function") or {}).get("arguments", "{}")
        try:
            args = json.loads(args_str)
        except Exception:
            args = {}
        
        result, _ = execute_mcp_tool(fname, args, name_to_reg, mcp_url, dbg=False)
        
        if early_stop_on_error and result.get("error"):
            if LOG.isEnabledFor(logging.WARNING):
                LOG.warning(f"Tool {fname} failed: {result.get('error')}, stopping execution (early_stop_on_error=True)")
            results.append(result)
            break
        
        results.append(result)
    
    return results


def execute_tools_parallel(
    tool_calls: List[Dict[str, Any]],
    name_to_reg: Dict[str, str],
    mcp_url: str,
    early_stop_on_error: bool,
) -> List[Dict[str, Any]]:
    """Execute tools in parallel using asyncio.gather."""
    
    async def execute_one(tc):
        fname = (tc.get("function") or {}).get("name")
        args_str = (tc.get("function") or {}).get("arguments", "{}")
        try:
            args = json.loads(args_str)
        except Exception:
            args = {}
        
        # execute_mcp_tool is sync, wrap in executor
        loop = asyncio.get_event_loop()
        result, _ = await loop.run_in_executor(
            None,
            execute_mcp_tool,
            fname, args, name_to_reg, mcp_url, False
        )
        return result
    
    async def execute_all():
        tasks = [execute_one(tc) for tc in tool_calls]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    try:
        # Handle both running and non-running event loops
        try:
            loop = asyncio.get_running_loop()
            # Nested event loop detected (e.g., Jupyter)
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                if LOG.isEnabledFor(logging.WARNING):
                    LOG.warning("nest_asyncio not available, falling back to sequential execution")
                return execute_tools_sequential(tool_calls, name_to_reg, mcp_url, early_stop_on_error)
            results = loop.run_until_complete(execute_all())
        except RuntimeError:
            # No running loop, create new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(execute_all())
            loop.close()
    
    except Exception as e:
        if LOG.isEnabledFor(logging.ERROR):
            LOG.error(f"Parallel execution failed: {e}, falling back to sequential")
        return execute_tools_sequential(tool_calls, name_to_reg, mcp_url, early_stop_on_error)
    
    # Handle errors if early_stop enabled
    if early_stop_on_error:
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                results[i] = {"error": str(res)}
                return results[:i+1]
            if isinstance(res, dict) and res.get("error"):
                return results[:i+1]
    
    # Convert exceptions to error dicts
    final_results = []
    for res in results:
        if isinstance(res, Exception):
            final_results.append({"error": str(res)})
        else:
            final_results.append(res)
    
    return final_results
