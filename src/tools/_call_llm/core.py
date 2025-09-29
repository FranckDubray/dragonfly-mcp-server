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


def execute_call_llm(
    messages: List[Dict[str, Any]],
    model: str = "gpt-5",
    max_tokens: Optional[int] = None,
    tool_names: Optional[List[str]] = None,
    **kwargs,
) -> Dict[str, Any]:
    # Debug returned ONLY if explicitly requested
    debug_enabled = env_truthy("LLM_RETURN_DEBUG") or bool(kwargs.get("debug"))
    debug = make_debug_container(tool_names) if debug_enabled else {}

    token = os.getenv("AI_PORTAL_TOKEN")
    if not token:
        return {"error": "AI_PORTAL_TOKEN required", **({"debug": debug} if debug_enabled else {})}
    if not messages:
        return {"error": "messages required", **({"debug": debug} if debug_enabled else {})}

    # Strip system messages to promptSystem unless provided explicitly
    messages, prompt_system = strip_system_to_promptSystem(messages, kwargs.get("promptSystem"))

    endpoint = os.getenv("LLM_ENDPOINT", "https://dev-ai.dragonflygroup.fr/api/v1/chat/completions")
    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000")
    timeout_sec = int(os.getenv("LLM_REQUEST_TIMEOUT_SEC", "180"))

    payload = build_initial_payload(model, messages, prompt_system, max_tokens)

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
            return {"error": f"Failed to get MCP tools: {e}", **({"debug": debug} if debug_enabled else {})}

    headers = build_headers(token)

    # 1) First call (stream, with tools)
    payload["stream"] = True
    if debug_enabled:
        debug["meta"] = {"endpoint": endpoint, "MCP_URL": mcp_url, "model": model, "max_tokens": max_tokens}
        debug["first"]["payload"] = summarize_payload(payload, tool_data)
        debug["first"]["payload_full"] = copy.deepcopy(payload)

    resp = post_stream(endpoint, headers, payload, timeout_sec)
    tc_data = process_tool_calls_stream(resp)
    tool_calls = tc_data.get("tool_calls") or []
    streamed_text = (tc_data.get("text") or "").strip()

    if debug_enabled:
        first_stream = {
            "tool_calls_count": len(tool_calls),
            "text_len": len(streamed_text),
            "finish_reason": tc_data.get("finish_reason"),
            "usage": tc_data.get("usage"),
        }
        attach_stream_debug(first_stream, tc_data)
        debug["first"]["stream"] = first_stream

    # If no tool_calls but text arrived, return the text
    if not tool_calls:
        if streamed_text:
            out = {
                "success": True,
                "content": streamed_text,
                "finish_reason": tc_data.get("finish_reason", "stop"),
                "usage": tc_data.get("usage"),
            }
            if debug_enabled:
                out["debug"] = debug
            return out
        return {"error": "No tool_calls and no text returned in streaming response", **({"debug": debug} if debug_enabled else {})}

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

    resp2 = post_stream(endpoint, headers, final_payload, timeout_sec)
    final_result = process_streaming_chunks(resp2)

    if debug_enabled:
        second_stream = {
            "finish_reason": final_result.get("finish_reason"),
            "text_len": len(final_result.get("content") or ""),
            "usage": final_result.get("usage"),
        }
        attach_stream_debug(second_stream, final_result, keys=("sse_stats", "raw_preview", "response_headers", "raw"))
        debug["second"]["stream"] = second_stream

    out = {
        "success": True,
        "content": final_result.get("content", ""),
        "finish_reason": final_result.get("finish_reason", "stop"),
        "usage": final_result.get("usage"),
    }
    if debug_enabled:
        out["debug"] = debug
    return out
