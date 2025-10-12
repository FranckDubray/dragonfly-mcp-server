"""
MCP tools integration utilities (legacy module) - kept for backward compatibility
Now superseded by tools_exec.py but retained to avoid import errors.
Exports the same API as tools_exec: fetch_and_prepare_tools, execute_mcp_tool
"""
from __future__ import annotations
from typing import Any, Dict, Tuple
import json
import requests
import logging
import os

LOG = logging.getLogger(__name__)
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
    return {"tools": tools, "name_to_reg": name_to_reg, "found_tools": found_tools}


def execute_mcp_tool(fname: str, args: Dict[str, Any], name_to_reg: Dict[str, str], mcp_url: str, dbg: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    reg_name = name_to_reg.get(fname, fname)
    mcp_payload = {"tool_reg": reg_name, "params": args}
    mcp_url_exec = f"{mcp_url}/execute"
    mcp_debug: Dict[str, Any] = {"url": mcp_url_exec, "request_json": mcp_payload} if dbg else {}
    try:
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
                return result, mcp_debug
            except Exception as e:
                return {"error": "Invalid MCP JSON response"}, mcp_debug
        else:
            if dbg:
                try:
                    mcp_debug["response_text"] = mcp_resp.text
                except Exception:
                    pass
            return {"error": f"MCP error {mcp_resp.status_code}"}, mcp_debug
    except Exception as e:
        if dbg:
            mcp_debug["exception"] = str(e)
        return {"error": f"MCP call failed: {e}"}, mcp_debug
