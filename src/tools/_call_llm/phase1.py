from __future__ import annotations
"""
LLM Phase 1: streaming with tools enabled, collect tool_calls, execute MCP tools
"""
from typing import Any, Dict, List
import json
import logging
from .http_client import post_stream
from .streaming import process_tool_calls_stream
from .tools_exec import execute_mcp_tool, build_assistant_tool_message, append_tool_results_to_messages
from .debug_utils import attach_stream_debug, trim_val
from .usage_utils import merge_usage

LOG = logging.getLogger(__name__)


def execute_phase1(
    endpoint: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout_sec: int,
    tool_data: Dict[str, Any],
    mcp_url: str,
    debug_enabled: bool,
    usage_cumulative: Dict[str, Any],
    usage_breakdown: List[Dict[str, Any]] | None,
) -> Dict[str, Any]:
    """Phase 1: LLM call with tools, reconstruct tool_calls, execute MCP tools.
    Returns: {
        "tool_calls": [...],
        "text": "...",
        "media": [...],
        "finish_reason": "...",
        "messages": [...],  # updated with assistant + tool results
        "exec_results": [...],  # tool execution details
        "first_usage": {...},
        "debug_first_stream": {...} (if debug_enabled)
    }
    """
    if LOG.isEnabledFor(logging.INFO):
        LOG.info(f"LLM phase 1: streaming with tools (tools_count={len(payload.get('tools', []))})")

    resp = post_stream(endpoint, headers, payload, timeout_sec)
    tc_data = process_tool_calls_stream(resp)
    tool_calls = tc_data.get("tool_calls") or []
    streamed_text = (tc_data.get("text") or "").strip()
    media = tc_data.get("media") or []

    # Aggregate usage from first stream
    first_usage = tc_data.get("usage")
    merge_usage(usage_cumulative, first_usage)
    if debug_enabled and first_usage:
        usage_breakdown.append({"stage": "first_stream_with_tools", "usage": first_usage})

    debug_first_stream = None
    if debug_enabled:
        debug_first_stream = {
            "tool_calls_count": len(tool_calls),
            "text_len": len(streamed_text),
            "finish_reason": tc_data.get("finish_reason"),
            "usage": first_usage,
            "media_count": len(media),
        }
        if media:
            debug_first_stream["media_preview"] = [{k: v for k, v in m.items() if k in ("kind", "mime_type", "url")} for m in media][:5]
        attach_stream_debug(debug_first_stream, tc_data)

    # If no tool_calls, return early
    if not tool_calls:
        return {
            "tool_calls": [],
            "text": streamed_text,
            "media": media,
            "finish_reason": tc_data.get("finish_reason", "stop"),
            "messages": payload["messages"],
            "exec_results": [],
            "first_usage": first_usage,
            "debug_first_stream": debug_first_stream,
            "early_return": True,
        }

    if LOG.isEnabledFor(logging.INFO):
        LOG.info(f"LLM phase 1 complete: {len(tool_calls)} tool_calls detected")

    # Build assistant tool_calls message
    assistant_msg = build_assistant_tool_message(tool_calls)
    payload["messages"].append(assistant_msg)

    # Execute MCP tools
    exec_results = []
    for tc in tool_calls:
        fname = (tc.get("function") or {}).get("name")
        args_str = (tc.get("function") or {}).get("arguments", "{}")
        try:
            args = json.loads(args_str)
        except Exception:
            args = {}
        result, mcp_dbg = execute_mcp_tool(fname, args, tool_data.get("name_to_reg") or {}, mcp_url, debug_enabled)
        # Merge usage from child tool
        child_usage = None
        if isinstance(result, dict):
            child_usage = result.get("usage") or result.get("usage_cumulative")
        merge_usage(usage_cumulative, child_usage)
        if debug_enabled and child_usage:
            usage_breakdown.append({"stage": f"tool:{fname}", "usage": child_usage})
        exec_results.append({
            "name": fname,
            "args": args,
            "mcp": mcp_dbg if debug_enabled else {},
            "result_excerpt": trim_val(result, 2000),
        })

    append_tool_results_to_messages(payload["messages"], tool_calls, exec_results)

    return {
        "tool_calls": tool_calls,
        "text": streamed_text,
        "media": media,
        "finish_reason": tc_data.get("finish_reason", "tool_calls"),
        "messages": payload["messages"],
        "exec_results": exec_results,
        "first_usage": first_usage,
        "debug_first_stream": debug_first_stream,
        "early_return": False,
    }
