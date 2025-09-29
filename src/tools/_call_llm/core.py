"""
Core LLM execution logic (STREAM-ONLY for both calls) with rich debug.
- If tools provided:
  - 1st call (STREAM): if tool_calls → execute MCP tools, then 2nd call (STREAM) for final text.
  - If no tool_calls but text streamed → return that text directly.
- promptSystem: ONLY via payload.promptSystem (system messages are stripped from messages).
- Debug: when LLM_DEBUG or LLM_RETURN_DEBUG truthy, returns a `debug` object (no secrets),
  summarizing payloads, streaming outcomes, tool_calls and tool executions.
- STRICT: no non-stream fallbacks (never stream=False).
"""
from typing import Any, Dict, List, Optional
import os
import json
import logging
import requests

from .streaming import process_streaming_chunks, process_tool_calls_stream

LOG = logging.getLogger(__name__)

# -------------------- helpers (debug + safety) --------------------

def _env_truthy(name: str) -> bool:
    v = os.getenv(name, "").strip().lower()
    return v in ("1", "true", "yes", "on", "debug")


def _trim_str(s: Any, limit: int = 2000) -> Any:
    try:
        if isinstance(s, str) and len(s) > limit:
            return s[:limit] + f"... (+{len(s) - limit} bytes)"
    except Exception:
        pass
    return s


def _trim_val(x: Any, limit: int = 2000) -> Any:
    try:
        if isinstance(x, dict):
            return {k: _trim_val(v, limit) for k, v in x.items()}
        if isinstance(x, list):
            return [_trim_val(v, limit) for v in x]
        if isinstance(x, str):
            return _trim_str(x, limit)
    except Exception:
        return x
    return x


def _payload_summary(payload: Dict[str, Any], tool_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "model": payload.get("model"),
        "has_promptSystem": "promptSystem" in payload and bool(payload.get("promptSystem")),
        "messages_count": len(payload.get("messages") or []),
        "stream": bool(payload.get("stream")),
    }
    if tool_data:
        names = list(tool_data.get("found_tools") or [])
        out.update({
            "tools_count": len(tool_data.get("tools") or []),
            "tool_names": names,
            "tool_choice": payload.get("tool_choice"),
            "parallel_tool_calls": payload.get("parallel_tool_calls"),
        })
    # Do not include Authorization nor the full tools specs/messages here to avoid noise
    return out


def execute_call_llm(
    messages: List[Dict[str, Any]],
    model: str = "gpt-5",
    max_tokens: Optional[int] = None,
    tool_names: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    debug_enabled = _env_truthy("LLM_RETURN_DEBUG") or _env_truthy("LLM_DEBUG") or bool(kwargs.get("debug"))
    debug: Dict[str, Any] = {
        "first": {},
        "tools": {"requested": tool_names or [], "prepared": [], "executions": []},
        "second": {},
        "meta": {},
    } if debug_enabled else {}

    token = os.getenv("AI_PORTAL_TOKEN")
    if not token:
        return {"error": "AI_PORTAL_TOKEN required", **({"debug": debug} if debug_enabled else {})}
    if not messages:
        return {"error": "messages required", **({"debug": debug} if debug_enabled else {})}

    # Strip system messages → promptSystem
    prompt_system = kwargs.get("promptSystem")
    if not prompt_system:
        new_messages: List[Dict[str, Any]] = []
        for m in messages:
            if m.get("role") == "system" and prompt_system is None:
                prompt_system = m.get("content", "")
            else:
                new_messages.append(m)
        messages = new_messages

    endpoint = os.getenv("LLM_ENDPOINT", "https://dev-ai.dragonflygroup.fr/api/v1/chat/completions")
    timeout_sec = int(os.getenv("LLM_REQUEST_TIMEOUT_SEC", "180"))
    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000")

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 1,
    }
    if prompt_system:
        payload["promptSystem"] = prompt_system
    if max_tokens:
        payload["max_tokens"] = max_tokens

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Prepare tools if requested
    tool_data: Dict[str, Any] = {"tools": [], "name_to_reg": {}, "found_tools": []}
    if tool_names:
        try:
            td = fetch_and_prepare_tools(tool_names, mcp_url)
            tool_data = td
            if tool_data.get("tools"):
                payload["tools"] = tool_data["tools"]
                if debug_enabled:
                    debug["tools"]["prepared"] = list(tool_data.get("found_tools") or [])
        except Exception as e:
            return {"error": f"Failed to get MCP tools: {e}", **({"debug": debug} if debug_enabled else {})}

    # 1) FIRST CALL (STREAM-ONLY)
    try:
        payload["stream"] = True
        if debug_enabled:
            debug["meta"] = {
                "endpoint": endpoint,
                "MCP_URL": mcp_url,
                "model": model,
                "max_tokens": max_tokens,
            }
            debug["first"]["payload"] = _payload_summary(payload, tool_data)

        resp = requests.post(endpoint, headers=headers, json=payload, stream=True, timeout=timeout_sec, verify=False)
        resp.raise_for_status()

        # Reconstruct tool_calls (and capture any streamed text)
        tc_data = process_tool_calls_stream(resp)
        tool_calls = tc_data.get("tool_calls") or []
        streamed_text = (tc_data.get("text") or "").strip()
        if debug_enabled:
            debug["first"]["stream"] = {
                "tool_calls_count": len(tool_calls),
                "text_len": len(streamed_text),
                "finish_reason": tc_data.get("finish_reason"),
                "usage": tc_data.get("usage"),
            }

        # If no tool_calls were returned but some text was streamed, return that text directly
        if not tool_calls:
            if streamed_text:
                result: Dict[str, Any] = {
                    "success": True,
                    "content": streamed_text,
                    "finish_reason": tc_data.get("finish_reason", "stop"),
                    "usage": tc_data.get("usage"),
                }
                if debug_enabled:
                    result["debug"] = debug
                return result
            # Otherwise, nothing usable was received
            return {"error": "No tool_calls and no text returned in streaming response", **({"debug": debug} if debug_enabled else {})}

        # Append assistant message built from streaming tool_calls (OpenAI format)
        assistant_msg: Dict[str, Any] = {"role": "assistant", "tool_calls": []}
        for tc in tool_calls:
            assistant_msg["tool_calls"].append({
                "id": tc.get("id"),
                "type": "function",
                "function": {
                    "name": (tc.get("function") or {}).get("name"),
                    "arguments": (tc.get("function") or {}).get("arguments", ""),
                },
            })
        payload["messages"].append(assistant_msg)

        # Execute each tool call via MCP
        for tc in tool_calls:
            fname = (tc.get("function") or {}).get("name")
            args_str = (tc.get("function") or {}).get("arguments", "{}")
            try:
                args = json.loads(args_str)
            except Exception:
                args = {}
            result = execute_mcp_tool(fname, args, tool_data.get("name_to_reg") or {}, mcp_url)
            # Debug capture (trimmed)
            if debug_enabled:
                debug["tools"]["executions"].append({
                    "name": fname,
                    "args": _trim_val(args, 500),
                    "result_excerpt": _trim_val(result, 1000),
                })
            payload["messages"].append({
                "role": "tool",
                "tool_call_id": tc.get("id"),
                "content": json.dumps(result),
            })

        # 2) SECOND CALL (STREAM-ONLY, no tools)
        if "tools" in payload:
            del payload["tools"]
        final_payload = json.loads(json.dumps(payload))  # deep copy
        final_payload["stream"] = True
        if debug_enabled:
            debug["second"]["payload"] = _payload_summary(final_payload)

        resp2 = requests.post(endpoint, headers=headers, json=final_payload, stream=True, timeout=timeout_sec, verify=False)
        resp2.raise_for_status()
        final_result = process_streaming_chunks(resp2)
        if debug_enabled:
            debug["second"]["stream"] = {
                "finish_reason": final_result.get("finish_reason"),
                "text_len": len(final_result.get("content") or ""),
                "usage": final_result.get("usage"),
            }
        out: Dict[str, Any] = {
            "success": True,
            "content": final_result.get("content", ""),
            "finish_reason": final_result.get("finish_reason", "stop"),
            "usage": final_result.get("usage"),
        }
        if debug_enabled:
            out["debug"] = debug
        return out

    except Exception as e:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.exception("LLM call failed (stream-only)")
        return {"error": str(e), **({"debug": debug} if debug_enabled else {})}


# -------------------- tool discovery + MCP exec --------------------

def fetch_and_prepare_tools(tool_names, mcp_url):
    """Fetch tools from MCP server and prepare OpenAI format"""
    import requests
    resp = requests.get(f"{mcp_url}/tools", timeout=10)
    resp.raise_for_status()
    all_tools = resp.json()

    tools = []
    name_to_reg: Dict[str, str] = {}
    found_tools = []
    for item in all_tools:
        item_name = item.get("name")
        if item_name in tool_names:
            spec_str = item.get("json")
            reg_name = item.get("regName", item_name)
            if spec_str:
                try:
                    spec = json.loads(spec_str)
                    if "function" in spec:
                        func_spec = spec["function"]
                        tools.append({"type": "function", "function": func_spec})
                        fname = func_spec.get("name")
                        if fname:
                            name_to_reg[fname] = reg_name
                            found_tools.append(fname)
                except Exception:
                    continue
    return {"tools": tools, "name_to_reg": name_to_reg, "found_tools": found_tools}


def execute_mcp_tool(fname, args, name_to_reg, mcp_url):
    """Execute a single MCP tool"""
    import requests
    reg_name = name_to_reg.get(fname, fname)
    mcp_payload = {"tool_reg": reg_name, "params": args}
    try:
        mcp_resp = requests.post(
            f"{mcp_url}/execute",
            json=mcp_payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if mcp_resp.status_code == 200:
            mcp_data = mcp_resp.json()
            return mcp_data.get("result", {})
        else:
            return {"error": f"MCP error {mcp_resp.status_code}: {mcp_resp.text}"}
    except Exception as e:
        return {"error": f"MCP call failed: {e}"}
