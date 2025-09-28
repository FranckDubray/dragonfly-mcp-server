"""
Core LLM execution logic (restored and fixed)
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
        LOG.debug("=== CALL_LLM START ===")
        LOG.debug(f"messages: {len(messages) if messages else 'None'}")
        LOG.debug(f"model: {model}")
        LOG.debug(f"max_tokens: {max_tokens}")
        LOG.debug(f"tool_names: {tool_names}")
        
    token = os.getenv("AI_PORTAL_TOKEN")
    if not token:
        return {"error": "AI_PORTAL_TOKEN required"}
    
    if not messages:
        return {"error": "messages required"}

    endpoint = os.getenv("LLM_ENDPOINT", "https://dev-ai.dragonflygroup.fr/api/v1/chat/completions")
    
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 1,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Tools requested
    if tool_names:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug("=== MCP TOOLS MODE ===")
            LOG.debug(f"Requested tools: {tool_names}")
        try:
            mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000")
            tool_data = fetch_and_prepare_tools(tool_names, mcp_url)
            if not tool_data["tools"]:
                if LOG.isEnabledFor(logging.DEBUG):
                    LOG.debug("No matching tools found - falling back to simple LLM call")
                tool_names = None
            else:
                payload["tools"] = tool_data["tools"]
                # ENFORCE tool usage
                found = tool_data.get("found_tools", [])
                if len(found) == 1:
                    payload["tool_choice"] = {"type": "function", "function": {"name": found[0]}}
                else:
                    payload["tool_choice"] = "required"
                if LOG.isEnabledFor(logging.DEBUG):
                    LOG.debug(f"Added {len(tool_data['tools'])} tools to LLM payload (NEW FORMAT)")
                    LOG.debug(f"🔍 PAYLOAD TO LLM API: {json.dumps(payload, indent=2)}")
        except Exception as e:
            return {"error": f"Failed to get MCP tools: {e}"}

    try:
        # Simple mode (no tools) OR tools mode for final answer
        if not tool_names:
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug("=== STREAMING MODE (FINAL/TEXT) ===")
                LOG.debug(f"→ POST {endpoint}")
                LOG.debug(f"🔍 SIMPLE PAYLOAD TO LLM API: {json.dumps(payload, indent=2)}")
            payload["stream"] = True
            resp = requests.post(endpoint, headers=headers, json=payload, stream=True, verify=False)
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug(f"← HTTP {resp.status_code}")
            resp.raise_for_status()
            result = process_streaming_chunks(resp)
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug(f"🔍 ASSEMBLED CHUNKS RESULT: {json.dumps(result, indent=2)}")
            return {
                "success": True,
                "content": result["content"],
                "finish_reason": result["finish_reason"],
                "usage": result["usage"]
            }
        
        # Tools mode - first call (STREAM)
        else:
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug("=== TOOLS MODE (STREAM) ===")
                LOG.debug(f"→ POST {endpoint} (SSE for tool_calls)")
            payload["stream"] = True
            resp = requests.post(endpoint, headers=headers, json=payload, stream=True, verify=False)
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug(f"← HTTP {resp.status_code}")
            resp.raise_for_status()

            # Reconstruct tool_calls from stream
            tc_data = process_tool_calls_stream(resp)
            tool_calls = tc_data.get("tool_calls") or []

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

            # Force final text answer (no more tool calls) - STREAM
            payload["tool_choice"] = "none"
            if "tools" in payload: del payload["tools"]
            if "functions" in payload: del payload["functions"]
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug("=== FINAL CALL (STREAM) ===")
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
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"Fetching tools from MCP: {mcp_url}/tools")
    import requests
    resp = requests.get(f"{mcp_url}/tools", timeout=10)
    resp.raise_for_status()
    all_tools = resp.json()
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"MCP returned {len(all_tools)} total tools")

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
                except Exception as e:
                    if LOG.isEnabledFor(logging.DEBUG):
                        LOG.debug(f"Failed to parse spec for tool {item_name}: {e}")
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"Found {len(found_tools)} matching tools: {found_tools}")
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
