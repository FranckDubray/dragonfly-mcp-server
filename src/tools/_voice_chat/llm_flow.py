
"""LLM flow: call MCP /execute call_llm and log compact input/output.
- Includes compatibility fallback if the remote call_llm does not accept 'tool_names'.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import json
from .utils import mcp_base
from .logs import dbg
import requests


def _post_execute(payload: Dict[str, Any]) -> requests.Response:
    return requests.post(f"{mcp_base()}/execute", json=payload, timeout=120)


def call_llm(
    messages: List[Dict[str, str]],
    model: Optional[str],
    temperature: float,
    max_tokens: int,
    tool_names: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    send_messages = list(messages)
    if system_prompt and not (send_messages and send_messages[0].get("role") == "system"):
        send_messages = [{"role": "system", "content": system_prompt}] + send_messages
    payload = {
        "tool": "call_llm",
        "params": {
            "messages": send_messages,
            "model": model,
            "temperature": temperature,
            "max_tokens": int(max_tokens),
        },
    }
    if tool_names:
        payload["params"]["tool_names"] = tool_names
    dbg(
        "voice_chat_llm_call",
        model=model,
        max_tokens=int(max_tokens),
        messages_count=len(send_messages),
        tools=len(tool_names or []),
        has_system=bool(system_prompt),
    )
    try:
        r = _post_execute(payload)
        # Fallback: some servers may reject unknown param 'tool_names'
        if r.status_code == 400 and tool_names:
            txt = (r.text or "").lower()
            if "invalid" in txt and "param" in txt:
                dbg("voice_chat_llm_retry_no_tools")
                # Remove tool_names and retry once
                payload_retry = {
                    "tool": "call_llm",
                    "params": {
                        "messages": send_messages,
                        "model": model,
                        "temperature": temperature,
                        "max_tokens": int(max_tokens),
                    },
                }
                r = _post_execute(payload_retry)
        if r.status_code != 200:
            return {"error": f"call_llm failed {r.status_code}: {r.text[:200]}"}
        data = r.json()
        text = None
        if isinstance(data, dict):
            text = data.get("result") or data.get("text") or data.get("content")
            if isinstance(text, dict):
                text = text.get("text") or text.get("content")
        dbg("voice_chat_llm_result", preview=(text or "")[:160])
        return {"success": True, "assistant_text": text or ""}
    except Exception as e:
        return {"error": f"MCP /execute call_llm error: {e}"}
