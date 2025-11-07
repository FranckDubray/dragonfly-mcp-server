
"""Portal helpers: base URL, headers, fetch last thread and full messages (official endpoints only).

- GET {base}/api/v1/user/threads?page=1&itemsPerPage=1
- GET {base}/api/v1/threads/{id}
  (returns a Thread object with assistantContentJson array)

Role mapping (assistantContentJson ONLY):
- sender == "ai" or "assistant" → role = "assistant"
- else → role = "user"
Content from 'text' field. Empty texts are ignored. Tool-call containers (text empty with toolCalls) are skipped.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import os
import requests
from .utils import portal_base_from_llm_endpoint, portal_headers


def get_last_thread_id(user_token: str) -> Dict[str, Any]:
    base = portal_base_from_llm_endpoint()
    url = f"{base}/api/v1/user/threads?page=1&itemsPerPage=1"
    r = requests.get(url, headers=portal_headers(user_token), timeout=15)
    if r.status_code != 200:
        return {
            "error": f"Portal error {r.status_code}",
            "debug": {
                "method": "GET",
                "url": url,
                "portal_base": base,
                "LLM_ENDPOINT": os.getenv("LLM_ENDPOINT"),
                "reason": r.reason,
                "response_preview": (r.text or "")[:300],
            },
        }
    data = r.json()
    threads = data.get("threads") or data.get("hydra:member") or []
    if not threads:
        return {
            "error": "No threads found",
            "debug": {
                "method": "GET",
                "url": url,
                "portal_base": base,
                "LLM_ENDPOINT": os.getenv("LLM_ENDPOINT"),
                "data_keys": list(data.keys()) if isinstance(data, dict) else str(type(data)),
            },
        }
    t0 = threads[0]
    return {"success": True, "thread_id": t0.get("id")}


def get_thread_page(user_token: str, thread_id: str, page_url: Optional[str] = None) -> Dict[str, Any]:
    base = portal_base_from_llm_endpoint()
    url = page_url or f"{base}/api/v1/threads/{thread_id}"
    r = requests.get(url, headers=portal_headers(user_token), timeout=15)
    if r.status_code != 200:
        return {
            "error": f"Portal error {r.status_code}",
            "debug": {
                "method": "GET",
                "url": url,
                "portal_base": base,
                "LLM_ENDPOINT": os.getenv("LLM_ENDPOINT"),
                "reason": r.reason,
                "response_preview": (r.text or "")[:300],
            },
        }
    return {"success": True, "data": r.json(), "url": url}


def _extract_system_prompt(root: Dict[str, Any]) -> Optional[str]:
    if not isinstance(root, dict):
        return None
    # Common top-level keys
    for k in ("systemPrompt", "promptSystem", "system", "assistantSystem", "assistantInstructions"):
        v = root.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    # Sometimes nested under assistant
    assistant = root.get("assistant") or {}
    if isinstance(assistant, dict):
        for k in ("systemPrompt", "promptSystem", "system", "instructions"):
            v = assistant.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


def build_messages_from_portal(user_token: str) -> Dict[str, Any]:
    t = get_last_thread_id(user_token)
    if "error" in t:
        return t
    thread_id = t["thread_id"]
    
    first = get_thread_page(user_token, thread_id)
    if "error" in first:
        return first
    root = first["data"]

    items = root.get("assistantContentJson")
    if not isinstance(items, list):
        return {
            "error": "assistantContentJson not found or invalid format",
            "debug": {
                "thread_id": thread_id,
                "root_keys": list(root.keys()) if isinstance(root, dict) else str(type(root)),
            }
        }

    # Sort by timestamp (asc)
    items_sorted = sorted(items, key=lambda m: m.get("timestamp", 0))
    
    mapped: List[Dict[str, str]] = []
    for item in items_sorted:
        sender = (item.get("sender") or "").strip().lower()
        role = "assistant" if sender in ("ai", "assistant") else "user"
        text = (item.get("text") or "").strip()
        if not text:
            continue
        mapped.append({"role": role, "content": text})

    sys_prompt = _extract_system_prompt(root)

    return {
        "success": True,
        "thread_id": thread_id,
        "total_items": len(mapped),
        "returned_count": len(mapped),
        "messages": mapped,
        "system_prompt": sys_prompt,
    }
