from __future__ import annotations
"""
LLM Orchestrator (stream-only):
- 1st call with tools (stream): collects tool_calls (supports OpenAI + provider-specific + legacy), executes MCP tools.
- 2nd call without tools (stream): returns final text only.
- promptSystem passed separately from messages.
- Debug returned ONLY if LLM_RETURN_DEBUG=1 or params.debug=True.
"""
from typing import Any, Dict, List, Optional
import os
import json
import copy
import logging

from .payloads import (
    strip_system_to_promptSystem,
    build_initial_payload,
    summarize_payload,
)
from .http_client import build_headers, post_stream
from .streaming import process_tool_calls_stream, process_streaming_chunks
from .tools_exec import (
    fetch_and_prepare_tools,
    execute_mcp_tool,
    build_assistant_tool_message,
    append_tool_results_to_messages,
)
from .debug_utils import env_truthy, make_debug_container, attach_stream_debug, trim_val
from .usage_utils import merge_usage

LOG = logging.getLogger(__name__)


def execute_call_llm(
    messages: List[Dict[str, Any]],
    model: str = "gpt-5",
    max_tokens: Optional[int] = None,
    tool_names: Optional[List[str]] = None,
    assistantId: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs,
) -> Dict[str, Any]:
    # Debug returned ONLY if explicitly requested
    debug_enabled = env_truthy("LLM_RETURN_DEBUG") or bool(kwargs.get("debug"))
    debug = make_debug_container(tool_names) if debug_enabled else {}

    token = os.getenv("AI_PORTAL_TOKEN")
    if not token:
        if LOG.isEnabledFor(logging.ERROR):
            LOG.error("Missing AI_PORTAL_TOKEN")
        return {"error": "AI_PORTAL_TOKEN required", **({"debug": debug} if debug_enabled else {})}
    if not messages:
        if LOG.isEnabledFor(logging.ERROR):
            LOG.error("Missing messages parameter")
        return {"error": "messages required", **({"debug": debug} if debug_enabled else {})}

    # Strip system messages to promptSystem unless provided explicitly
    messages, prompt_system = strip_system_to_promptSystem(messages, kwargs.get("promptSystem"))

    endpoint = os.getenv("LLM_ENDPOINT", "https://dev-ai.dragonflygroup.fr/api/v1/chat/completions")
    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000")
    timeout_sec = int(os.getenv("LLM_REQUEST_TIMEOUT_SEC", "180"))

    if LOG.isEnabledFor(logging.INFO):
        LOG.info(f"LLM call: model={model}, messages_count={len(messages)}, tool_names={tool_names}")

    payload = build_initial_payload(model, messages, prompt_system, max_tokens, assistant_id=assistantId, temperature=temperature)

    # Prepare tools if requested
    tool_data: Dict[str, Any] = {"tools": [], "name_to_reg": {}, "found_tools": []}
    if tool_names:
        try:
            tool_data = fetch_and_prepare_tools(tool_names, mcp_url)
            if tool_data.get("tools"):
                payload["tools"] = tool_data["tools"]
                if debug_enabled:
                    debug["tools"]["prepared"] = list(tool_data.get("found_tools") or [])
        except Exception as e:
            if LOG.isEnabledFor(logging.ERROR):
                LOG.error(f"Failed to get MCP tools: {e}")
            return {"error": f"Failed to get MCP tools: {e}", **({"debug": debug} if debug_enabled else {})}

    headers = build_headers(token)

    # Cumulative usage across phases and nested calls
    usage_cumulative: Dict[str, Any] = {}
    usage_breakdown: List[Dict[str, Any]] = [] if debug_enabled else None

    # 1) First call (stream, with tools)
    payload["stream"] = True
    if debug_enabled:
        debug["meta"] = {"endpoint": endpoint, "MCP_URL": mcp_url, "model": model, "max_tokens": max_tokens, "assistantId": assistantId, "temperature": temperature}
        debug["first"]["payload"] = summarize_payload(payload, tool_data)
        debug["first"]["payload_full"] = copy.deepcopy(payload)

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

    if debug_enabled:
        first_stream = {
            "tool_calls_count": len(tool_calls),
            "text_len": len(streamed_text),
            "finish_reason": tc_data.get("finish_reason"),
            "usage": first_usage,
            "media_count": len(media),
        }
        if media:
            first_stream["media_preview"] = [{k: v for k, v in m.items() if k in ("kind", "mime_type", "url") } for m in media][:5]
        attach_stream_debug(first_stream, tc_data)
        debug["first"]["stream"] = first_stream

    # If no tool_calls but text or media arrived, return the text/media
    if not tool_calls:
        if streamed_text or media:
            if LOG.isEnabledFor(logging.INFO):
                LOG.info(f"LLM phase 1 complete: no tool_calls, text_len={len(streamed_text)}, media_count={len(media)}")
            out = {
                "success": True,
                "content": streamed_text,
                "media": media if media else None,
                "finish_reason": tc_data.get("finish_reason", "stop"),
                "usage": usage_cumulative if usage_cumulative else first_usage,
            }
            # remove None field for cleanliness
            if out.get("media") is None:
                del out["media"]
            if debug_enabled:
                debug["usage_cumulative"] = usage_cumulative
                if usage_breakdown:
                    debug["usage_breakdown"] = usage_breakdown
                out["debug"] = debug
            return out
        if LOG.isEnabledFor(logging.WARNING):
            LOG.warning("LLM phase 1: no tool_calls, no text, and no media")
        return {"error": "No tool_calls, no text, and no media in streaming response", **({"debug": debug} if debug_enabled else {})}

    if LOG.isEnabledFor(logging.INFO):
        LOG.info(f"LLM phase 1 complete: {len(tool_calls)} tool_calls detected")

    # Build assistant tool_calls message and execute MCP tools
    assistant_msg = build_assistant_tool_message(tool_calls)

    payload["messages"].append(assistant_msg)

    exec_results = []
    for tc in tool_calls:
        fname = (tc.get("function") or {}).get("name")
        args_str = (tc.get("function") or {}).get("arguments", "{}")
        try:
            args = json.loads(args_str)
        except Exception:
            args = {}
        result, mcp_dbg = execute_mcp_tool(fname, args, tool_data.get("name_to_reg") or {}, mcp_url, debug_enabled)
        # Merge usage from child tool (recursively if this is a nested call_llm)
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

    if debug_enabled:
        debug["tools"]["executions"] = exec_results

    # 2) Second call (stream, without tools) to produce final text
    if "tools" in payload:
        del payload["tools"]
    final_payload = json.loads(json.dumps(payload))
    final_payload["stream"] = True

    if debug_enabled:
        debug["second"]["payload"] = summarize_payload(final_payload, None)
        debug["second"]["payload_full"] = copy.deepcopy(final_payload)

    if LOG.isEnabledFor(logging.INFO):
        LOG.info(f"LLM phase 2: streaming without tools (messages_count={len(final_payload['messages'])})")

    resp2 = post_stream(endpoint, headers, final_payload, timeout_sec)
    final_result = process_streaming_chunks(resp2)

    # Aggregate usage from second stream
    final_usage = final_result.get("usage")
    merge_usage(usage_cumulative, final_usage)
    if debug_enabled and final_usage:
        usage_breakdown.append({"stage": "second_stream_without_tools", "usage": final_usage})

    if LOG.isEnabledFor(logging.INFO):
        LOG.info(f"LLM phase 2 complete: content_len={len(final_result.get('content') or '')}")

    if debug_enabled:
        second_stream = {
            "finish_reason": final_result.get("finish_reason"),
            "text_len": len(final_result.get("content") or ""),
            "usage": final_usage,
            "media_count": len(final_result.get("media") or []),
        }
        attach_stream_debug(second_stream, final_result, keys=("sse_stats", "raw_preview", "response_headers", "raw"))
        debug["second"]["stream"] = second_stream
        debug["usage_cumulative"] = usage_cumulative
        if usage_breakdown:
            debug["usage_breakdown"] = usage_breakdown

    out = {
        "success": True,
        "content": final_result.get("content", ""),
        "media": final_result.get("media") or (media if media else None),
        "finish_reason": final_result.get("finish_reason", "stop"),
        "usage": usage_cumulative if usage_cumulative else final_usage,
    }
    if out.get("media") is None:
        del out["media"]
    if debug_enabled:
        out["debug"] = debug
    return out
