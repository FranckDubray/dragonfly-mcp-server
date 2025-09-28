"""
Core LLM execution logic (restored and fixed)
"""
from typing import Any, Dict, List, Optional
import os
import json
import requests
import logging

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
        # Simple streaming mode (no tools)
        if not tool_names:
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug("=== STREAMING MODE ===")
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
        
        # Tools mode - first call
        else:
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug("=== TOOLS MODE (NEW FORMAT) ===")
                LOG.debug(f"→ POST {endpoint} (JSON for tool_calls)")
            resp = requests.post(endpoint, headers=headers, json=payload, verify=False)
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug(f"← HTTP {resp.status_code}")
                LOG.debug(f"🔍 RAW LLM RESPONSE: {resp.text[:1000]}...")
            resp.raise_for_status()
            data = resp.json()
            if "response" in data and "choices" not in data:
                if LOG.isEnabledFor(logging.DEBUG):
                    LOG.debug("← Detected wrapped response, unwrapping...")
                data = data["response"]

            choice = (data.get("choices") or [{}])[0]
            message = choice.get("message", {})
            tool_calls = message.get("tool_calls")
            function_call = message.get("function_call")

            # Append assistant message
            payload["messages"].append(message)

            if tool_calls:
                return handle_tool_calls(tool_calls, tool_data["name_to_reg"], mcp_url, payload, endpoint, headers)
            elif function_call:
                return handle_function_call(function_call, tool_data["name_to_reg"], mcp_url, payload, endpoint, headers)
            else:
                # No tool calls, direct answer
                return {
                    "success": True,
                    "content": message.get("content", ""),
                    "finish_reason": choice.get("finish_reason", "stop"),
                    "usage": data.get("usage")
                }
    except Exception as e:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.exception("LLM call failed")
        return {"error": str(e)}


def fetch_and_prepare_tools(tool_names, mcp_url):
    """Fetch tools from MCP server and prepare OpenAI format"""
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"Fetching tools from MCP: {mcp_url}/tools")
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


def process_streaming_chunks(response):
    """Process streaming response and return content - FIXED streaming"""
    content = ""
    finish_reason = None
    usage = None
    chunk_count = 0
    # Keep logs minimal (no per-chunk spam)
    for line in response.iter_lines():
        if not line:
            continue
        line = line.decode('utf-8').strip()
        # SSE prefix
        if line.startswith('data: '):
            data_str = line[6:]
            if data_str == '[DONE]':
                break
            try:
                chunk = json.loads(data_str)
                if "response" in chunk and "choices" not in chunk:
                    chunk = chunk["response"]
                chunk_count += 1
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    if delta.get("content"):
                        content += delta["content"]
                    if choices[0].get("finish_reason"):
                        finish_reason = choices[0]["finish_reason"]
                if chunk.get("usage"):
                    usage = chunk["usage"]
            except Exception:
                continue
    return {"content": content, "finish_reason": finish_reason or "stop", "usage": usage}


def handle_tool_calls(tool_calls, name_to_reg, mcp_url, payload, endpoint, headers):
    """Handle tool_calls (NEW OpenAI format)"""
    # Execute each tool call
    for tool_call in tool_calls:
        tc_id = tool_call.get("id")
        function_data = tool_call.get("function", {})
        fname = function_data.get("name")
        args_str = function_data.get("arguments", "{}")
        try:
            args = json.loads(args_str)
        except Exception:
            args = {}
        # Execute MCP tool
        result = execute_mcp_tool(fname, args, name_to_reg, mcp_url)
        # Add tool response to conversation (NEW FORMAT)
        payload["messages"].append({
            "role": "tool",
            "tool_call_id": tc_id,
            "content": json.dumps(result)
        })
    # Force final text answer (no more tool calls)
    payload["tool_choice"] = "none"
    return final_llm_call(payload, endpoint, headers)


def handle_function_call(function_call, name_to_reg, mcp_url, payload, endpoint, headers):
    """Handle function_call (LEGACY OpenAI format)"""
    fname = function_call.get("name")
    args_str = function_call.get("arguments", "{}")
    try:
        args = json.loads(args_str)
    except Exception:
        args = {}
    result = execute_mcp_tool(fname, args, name_to_reg, mcp_url)
    payload["messages"] .append({
        "role": "function",
        "name": fname,
        "content": json.dumps(result)
    })
    payload["tool_choice"] = "none"  # force final text answer
    return final_llm_call(payload, endpoint, headers)


def execute_mcp_tool(fname, args, name_to_reg, mcp_url):
    """Execute a single MCP tool"""
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


def final_llm_call(payload, endpoint, headers):
    """Make final LLM call with streaming after tool execution"""
    # Clone payload and enforce text answer; REMOVE tools for the second call
    final_payload = json.loads(json.dumps(payload))
    final_payload["tool_choice"] = "none"
    # Remove tools/functions on second call so model only writes text
    if "tools" in final_payload:
        del final_payload["tools"]
    if "functions" in final_payload:
        del final_payload["functions"]
    # Add a strict instruction to return only the final number (helps avoid verbose answers)
    final_payload["messages"].append({
        "role": "system",
        "content": "Réponds uniquement avec le résultat final (le nombre brut), sans texte, sans explication, sans formatage." 
    })
    final_payload["stream"] = True
    resp = requests.post(endpoint, headers=headers, json=final_payload, stream=True, verify=False)
    resp.raise_for_status()
    result = process_streaming_chunks(resp)
    content = result.get("content") or ""
    # Fallback non-stream if content empty
    if not content.strip():
        final_payload2 = json.loads(json.dumps(payload))
        final_payload2["tool_choice"] = "none"
        if "tools" in final_payload2:
            del final_payload2["tools"]
        if "functions" in final_payload2:
            del final_payload2["functions"]
        # Add the same strict instruction
        final_payload2["messages"].append({
            "role": "system",
            "content": "Réponds uniquement avec le résultat final (le nombre brut), sans texte, sans explication, sans formatage."
        })
        if "stream" in final_payload2:
            del final_payload2["stream"]
        resp2 = requests.post(endpoint, headers=headers, json=final_payload2, verify=False)
        resp2.raise_for_status()
        data2 = resp2.json()
        if "response" in data2 and "choices" not in data2:
            data2 = data2["response"]
        choice2 = (data2.get("choices") or [{}])[0]
        message2 = choice2.get("message", {})
        content = message2.get("content", "")
        finish_reason = choice2.get("finish_reason", "stop")
        usage = data2.get("usage")
        return {"success": True, "content": content, "finish_reason": finish_reason, "usage": usage}
    return {
        "success": True,
        "content": content,
        "finish_reason": result.get("finish_reason", "stop"),
        "usage": result.get("usage")
    }
