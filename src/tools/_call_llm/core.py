"""
Core LLM execution logic (stream-only for both calls) + promptSystem support
Behavior with tools:
- First streaming call:
  - If tool_calls appear → execute them, then do second streaming call for final text.
  - If NO tool_calls but some text was streamed → return that text directly (no second call).
"""
from typing import Any, Dict, List, Optional
import os
import json
import requests
import logging

from .streaming import process_streaming_chunks, process_tool_calls_stream

LOG = logging.getLogger(__name__)

def execute_call_llm(
    messages: List[Dict[str, Any]],
    model: str = "gpt-5",
    max_tokens: Optional[int] = None,
    tool_names: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug("=== CALL_LLM START (stream-only) ===")
        LOG.debug(f"messages: {len(messages) if messages else 'None'}")
        LOG.debug(f"model: {model}")
        LOG.debug(f"max_tokens: {max_tokens}")
        LOG.debug(f"tool_names: {tool_names}")
        
    token = os.getenv("AI_PORTAL_TOKEN")
    if not token:
        return {"error": "AI_PORTAL_TOKEN required"}
    
    if not messages:
        return {"error": "messages required"}

    # Extract promptSystem from kwargs or from system messages
    prompt_system = kwargs.get("promptSystem")
    if not prompt_system:
        new_messages: List[Dict[str, Any]] = []
        for m in messages:
            if (m.get("role") == "system") and (prompt_system is None):
                prompt_system = m.get("content", "")
            else:
                new_messages.append(m)
        messages = new_messages

    endpoint = os.getenv("LLM_ENDPOINT", "https://dev-ai.dragonflygroup.fr/api/v1/chat/completions")
    
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
        "Content-Type": "application/json"
    }

    # Tools requested
    tool_data: Dict[str, Any] = {"tools": [], "name_to_reg": {}, "found_tools": []}
    if tool_names:
        try:
            mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000")
            td = fetch_and_prepare_tools(tool_names, mcp_url)
            if not td["tools"]:
                return {"error": "No matching tools found for call_llm"}
            tool_data = td
            payload["tools"] = tool_data["tools"]
            # NOTE: No tool_choice / no parallel_tool_calls → let provider decide
        except Exception as e:
            return {"error": f"Failed to get MCP tools: {e}"}

    try:
        # Simple mode (no tools) OR tools mode for final answer
        if not tool_names:
            # FINAL ANSWER (TEXT) — STREAM-ONLY
            payload["stream"] = True
            resp = requests.post(endpoint, headers=headers, json=payload, stream=True, verify=False)
            resp.raise_for_status()
            result = process_streaming_chunks(resp)
            return {
                "success": True,
                "content": result.get("content", ""),
                "finish_reason": result.get("finish_reason", "stop"),
                "usage": result.get("usage")
            }
        
        # Tools mode - first call (STREAM-ONLY) for tool_calls
        else:
            payload["stream"] = True
            resp = requests.post(endpoint, headers=headers, json=payload, stream=True, verify=False)
            resp.raise_for_status()

            # Reconstruct tool_calls (and capture any streamed text)
            tc_data = process_tool_calls_stream(resp)
            tool_calls = tc_data.get("tool_calls") or []
            streamed_text = (tc_data.get("text") or "").strip()

            # If no tool_calls were returned but some text was streamed, return that text directly
            if not tool_calls:
                if streamed_text:
                    return {
                        "success": True,
                        "content": streamed_text,
                        "finish_reason": tc_data.get("finish_reason", "stop"),
                        "usage": tc_data.get("usage")
                    }
                # Otherwise, nothing usable was received
                return {"error": "No tool_calls and no text returned in streaming response"}

            # Append assistant message built from streaming tool_calls (OpenAI format)
            assistant_msg: Dict[str, Any] = {"role": "assistant", "tool_calls": []}
            for tc in tool_calls:
                assistant_msg["tool_calls"].append({
                    "id": tc.get("id"),
                    "type": "function",
                    "function": {"name": (tc.get("function") or {}).get("name"),
                                  "arguments": (tc.get("function") or {}).get("arguments", "")}
                })
            payload["messages"].append(assistant_msg)

            # Execute each tool call
            mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000")
            for tc in tool_calls:
                fname = (tc.get("function") or {}).get("name")
                args_str = (tc.get("function") or {}).get("arguments", "{}")
                try:
                    args = json.loads(args_str)
                except Exception:
                    args = {}
                result = execute_mcp_tool(fname, args, tool_data["name_to_reg"], mcp_url)
                payload["messages"].append({
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "content": json.dumps(result)
                })

            # Final text answer (no tools in second call) — STREAM-ONLY
            if "tools" in payload:
                del payload["tools"]
            final_payload = json.loads(json.dumps(payload))
            final_payload["stream"] = True
            resp2 = requests.post(endpoint, headers=headers, json=final_payload, stream=True, verify=False)
            resp2.raise_for_status()
            final_result = process_streaming_chunks(resp2)
            return {
                "success": True,
                "content": final_result.get("content", ""),
                "finish_reason": final_result.get("finish_reason", "stop"),
                "usage": final_result.get("usage")
            }
    except Exception as e:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.exception("LLM call failed")
        return {"error": str(e)}


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
            timeout=30
        )
        if mcp_resp.status_code == 200:
            mcp_data = mcp_resp.json()
            return mcp_data.get("result", {})
        else:
            return {"error": f"MCP error {mcp_resp.status_code}: {mcp_resp.text}"}
    except Exception as e:
        return {"error": f"MCP call failed: {e}"}
