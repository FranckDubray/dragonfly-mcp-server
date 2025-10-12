from __future__ import annotations
from typing import Any, Dict, Tuple
import json
import requests
import os
import uuid
import logging

LOG = logging.getLogger(__name__)

# Use the server's global tool execution timeout for internal tool calls
# Falls back to 180s (same default as app_factory.EXECUTE_TIMEOUT_SEC)
EXECUTE_TIMEOUT_SEC = int(os.getenv("EXECUTE_TIMEOUT_SEC", "180"))

def fetch_and_prepare_tools(tool_names, mcp_url):
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
    if LOG.isEnabledFor(logging.INFO):
        LOG.info(f"MCP tools prepared: {len(found_tools)} tools ({', '.join(found_tools)})")
    return {"tools": tools, "name_to_reg": name_to_reg, "found_tools": found_tools}

def execute_mcp_tool(fname: str, args: Dict[str, Any], name_to_reg: Dict[str, str], mcp_url: str, dbg: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    reg_name = name_to_reg.get(fname, fname)
    mcp_payload = {"tool_reg": reg_name, "params": args}
    mcp_url_exec = f"{mcp_url}/execute"
    mcp_debug: Dict[str, Any] = {"url": mcp_url_exec, "request_json": mcp_payload} if dbg else {}
    try:
        if LOG.isEnabledFor(logging.INFO):
            LOG.info(f"Executing MCP tool: {fname} (reg: {reg_name})")
        mcp_resp = requests.post(
            mcp_url_exec,
            json=mcp_payload,
            headers={"Content-Type": "application/json"},
            timeout=EXECUTE_TIMEOUT_SEC,
        )
        if dbg:
            mcp_debug["status_code"] = mcp_resp.status_code
        if mcp_resp.status_code == 200:
            try:
                mcp_json = mcp_resp.json()
                if dbg:
                    mcp_debug["response_json"] = mcp_json
                result = mcp_json.get("result", {})
                if LOG.isEnabledFor(logging.INFO):
                    LOG.info(f"MCP tool {fname} completed successfully")
                return result, mcp_debug
            except Exception as e:
                if LOG.isEnabledFor(logging.WARNING):
                    LOG.warning(f"MCP tool {fname} invalid JSON response: {e}")
                return {"error": "Invalid MCP JSON response"}, mcp_debug
        else:
            if dbg:
                try:
                    mcp_debug["response_text"] = mcp_resp.text
                except Exception:
                    pass
            if LOG.isEnabledFor(logging.WARNING):
                LOG.warning(f"MCP tool {fname} error: HTTP {mcp_resp.status_code}")
            return {"error": f"MCP error {mcp_resp.status_code}"}, mcp_debug
    except Exception as e:
        if dbg:
            mcp_debug["exception"] = str(e)
        if LOG.isEnabledFor(logging.WARNING):
            LOG.warning(f"MCP tool {fname} call failed: {e}")
        return {"error": f"MCP call failed: {e}"}, mcp_debug

def build_assistant_tool_message(tool_calls):
    """Build assistant message with tool_calls. Generates fallback IDs if missing.
    IMPORTANT:
    - Don't include 'content' field when tool_calls is present (OpenAI best practice).
    - Modifies tool_calls IN-PLACE to add generated IDs (ensures consistency with tool results).
    """
    assistant_msg: Dict[str, Any] = {"role": "assistant", "tool_calls": []}
    for tc in tool_calls:
        tc_id = tc.get("id")
        if not tc_id:
            tc_id = f"call_{uuid.uuid4().hex[:16]}"
            tc["id"] = tc_id
            if LOG.isEnabledFor(logging.WARNING):
                LOG.warning(f"Tool call missing ID, generated fallback: {tc_id}")
        assistant_msg["tool_calls"].append({
            "id": tc_id,
            "type": "function",
            "function": {
                "name": (tc.get("function") or {}).get("name"),
                "arguments": (tc.get("function") or {}).get("arguments", ""),
            },
        })
    return assistant_msg

def append_tool_results_to_messages(messages, tool_calls, exec_results):
    for tc, ex in zip(tool_calls, exec_results):
        tc_id = tc.get("id")
        if not tc_id:
            tc_id = f"call_{uuid.uuid4().hex[:16]}"
            if LOG.isEnabledFor(logging.ERROR):
                LOG.error(f"Tool call still missing ID in append_tool_results, generating emergency fallback: {tc_id}")
        messages.append({
            "role": "tool",
            "tool_call_id": tc_id,
            "content": json.dumps(ex.get("result_excerpt", ex)),
        })
