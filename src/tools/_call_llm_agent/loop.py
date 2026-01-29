from __future__ import annotations
"""
Single iteration logic for LLM Agent.
"""
from typing import Any, Dict, List
import json
import logging
import sys

from .executor import execute_tools_parallel, execute_tools_sequential

# Import from parent _call_llm package
try:
    from ..call_llm import build_headers, post_stream, process_tool_calls_stream
    from ..call_llm import fetch_and_prepare_tools, build_assistant_tool_message
except ImportError:
    sys.path.insert(0, ".")
    from src.tools._call_llm.http_client import build_headers, post_stream
    from src.tools._call_llm.streaming import process_tool_calls_stream
    from src.tools._call_llm.tools_exec import fetch_and_prepare_tools, build_assistant_tool_message

LOG = logging.getLogger(__name__)


def execute_single_iteration(
    messages: List[Dict[str, Any]],
    model: str,
    tool_names: List[str],
    prompt_system: str,
    temperature: float,
    endpoint: str,
    mcp_url: str,
    token: str,
    parallel_execution: bool,
    early_stop_on_error: bool,
    timeout_remaining: int,
) -> Dict[str, Any]:
    """
    Execute a single iteration of the agent:
    1. Call LLM with tools
    2. If tool_calls → execute (parallel or sequential)
    3. Add results to messages
    4. Return finish_reason + usage
    """
    
    # Prepare MCP tools
    try:
        tool_data = fetch_and_prepare_tools(tool_names, mcp_url)
        tools_spec = tool_data.get("tools", [])
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"Prepared {len(tools_spec)} tools: {tool_data.get('found_tools', [])}")
    except Exception as e:
        if LOG.isEnabledFor(logging.ERROR):
            LOG.error(f"Failed to fetch MCP tools: {e}")
        return {"error": f"Failed to fetch MCP tools: {e}", "finish_reason": "error"}
    
    # Build LLM payload
    payload = {
        "model": model,
        "messages": messages,
        "promptSystem": prompt_system,
        "temperature": temperature,
        "tools": tools_spec,
        "stream": True,
    }
    
    headers = build_headers(token)
    
    # Call LLM with streaming
    try:
        resp = post_stream(endpoint, headers, payload, timeout_remaining)
        tc_data = process_tool_calls_stream(resp)
    except Exception as e:
        if LOG.isEnabledFor(logging.ERROR):
            LOG.error(f"LLM call failed: {e}")
        return {"error": f"LLM call failed: {e}", "finish_reason": "error"}
    
    tool_calls = tc_data.get("tool_calls") or []
    finish_reason = tc_data.get("finish_reason", "stop")
    usage = tc_data.get("usage")
    streamed_text = tc_data.get("text", "")
    
    # If no tool_calls → direct text response
    # FIX: Force finish_reason to "stop" if no tool_calls (prevents infinite loop)
    if not tool_calls:
        actual_finish = "stop" if streamed_text else finish_reason
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"No tool_calls, finish_reason={finish_reason}→{actual_finish}, text_len={len(streamed_text)}")
        return {
            "finish_reason": actual_finish,
            "content": streamed_text,
            "usage": usage,
            "tool_calls": [],
        }
    
    # ========== TOOL EXECUTION ==========
    
    if LOG.isEnabledFor(logging.INFO):
        LOG.info(f"Executing {len(tool_calls)} tools (parallel={parallel_execution})")
    
    # Build assistant message with tool_calls
    assistant_msg = build_assistant_tool_message(tool_calls)
    messages.append(assistant_msg)
    
    # Execute tools (parallel or sequential)
    if parallel_execution and len(tool_calls) > 1:
        exec_results = execute_tools_parallel(
            tool_calls,
            tool_data.get("name_to_reg", {}),
            mcp_url,
            early_stop_on_error,
        )
    else:
        exec_results = execute_tools_sequential(
            tool_calls,
            tool_data.get("name_to_reg", {}),
            mcp_url,
            early_stop_on_error,
        )
    
    # Add tool results to messages
    for tc, result in zip(tool_calls, exec_results):
        messages.append({
            "role": "tool",
            "tool_call_id": tc.get("id"),
            "content": json.dumps(result.get("result", result)),
        })
    
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"Tools executed, results added to messages (messages_count={len(messages)})")
    
    return {
        "finish_reason": "tool_calls",
        "tool_calls": tool_calls,
        "tool_results": exec_results,
        "usage": usage,
    }
