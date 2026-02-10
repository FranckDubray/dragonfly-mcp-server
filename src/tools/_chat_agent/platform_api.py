"""Platform API wrapper for chat_agent.

Handles:
- Chat completions with streaming (POST /chat/completions)
- Thread history loading (GET /threads/{id})
- MCP tools fetching
"""

from typing import Any, Dict, List, Optional
import requests
import logging
import json
import time
import random
import string

LOG = logging.getLogger(__name__)

ROOT_PARENT_ID = "000170695000"


def _gen_msg_id() -> str:
    """Generate unique message ID (Platform format)."""
    ts = int(time.time() * 1000)
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{ts}-{suffix}"


def load_thread_history(
    thread_id: str,
    token: str,
    api_base: str,
    timeout: int = 30
) -> Dict[str, Any]:
    """Load thread history from Platform API.
    
    Args:
        thread_id: Thread ID to load (format: thread_stream_XXX)
        token: Bearer token
        api_base: API base URL (e.g., https://ai.dragonflygroup.fr/api/v1)
        timeout: Request timeout
    
    Returns:
        Dict with:
        - success: bool
        - messages: List of messages in Platform format (if success)
        - error: Error message (if failed)
    """
    # Correct endpoint: /api/v1/threads/{id}
    url = f"{api_base}/threads/{thread_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        LOG.info(f"Loading thread history from: {url}")
        
        resp = requests.get(url, headers=headers, timeout=timeout)
        
        if resp.status_code == 404:
            return {
                "success": False,
                "error": f"Thread not found: {thread_id}",
                "hint": "Verify the thread_id or create a new thread"
            }
        
        resp.raise_for_status()
        data = resp.json()
        
        # Extract assistantContentJson (the message history)
        assistant_content = data.get("assistantContentJson", [])
        
        if not isinstance(assistant_content, list):
            LOG.warning(f"Thread {thread_id} has invalid assistantContentJson format")
            assistant_content = []
        
        LOG.info(f"✅ Loaded {len(assistant_content)} messages from thread {thread_id}")
        
        return {
            "success": True,
            "messages": assistant_content,
            "thread_data": data  # Full thread data for debugging
        }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": f"Timeout loading thread {thread_id} (>{timeout}s)"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Failed to load thread history: {e}"
        }
    except Exception as e:
        LOG.exception("Unexpected error loading thread history")
        return {
            "success": False,
            "error": f"Unexpected error: {e}"
        }


def call_llm_streaming(
    messages: List[Dict[str, Any]],
    model: str,
    tools: List[Dict[str, Any]],
    system_prompt: str,
    temperature: float,
    token: str,
    api_base: str,
    thread_id: Optional[str] = None,
    timeout: int = 300,
    save: bool = True
) -> Dict[str, Any]:
    """Call LLM with streaming enabled.
    
    Messages MUST include id/parentId/level for Platform to store them properly.
    """
    try:
        from .._call_llm.http_client import build_headers, post_stream
        from .._call_llm.streaming import process_tool_calls_stream
    except ImportError as e:
        raise ImportError(f"Failed to import _call_llm streaming: {e}")
    
    url = f"{api_base}/chat/completions"
    
    # Build messages with id/parentId/level for Platform storage
    clean_messages = []
    last_id = ROOT_PARENT_ID
    
    for msg in messages:
        clean_msg = {}
        
        # Role
        clean_msg["role"] = msg.get("role", "user")
        
        # Content: ensure array format
        content = msg.get("content")
        if isinstance(content, str):
            clean_msg["content"] = [{"type": "text", "text": content}]
        elif isinstance(content, list):
            clean_msg["content"] = content
        else:
            clean_msg["content"] = []
        
        # ID: use existing or generate new
        msg_id = msg.get("id") or _gen_msg_id()
        clean_msg["id"] = msg_id
        
        # ParentId: use existing or chain to previous message
        clean_msg["parentId"] = msg.get("parentId") or last_id
        
        # Level
        clean_msg["level"] = msg.get("level", 0)
        
        # Tool calls (assistant message)
        if "tool_calls" in msg:
            clean_msg["tool_calls"] = msg["tool_calls"]
        
        # Tool result reference
        if "tool_call_id" in msg:
            clean_msg["tool_call_id"] = msg["tool_call_id"]
        
        clean_messages.append(clean_msg)
        last_id = msg_id
    
    payload = {
        "model": model,
        "messages": clean_messages,
        "promptSystem": system_prompt,
        "temperature": temperature,
        "stream": True,
        "save": save,
    }
    
    if tools:
        payload["tools"] = tools
    
    if thread_id:
        payload["threadId"] = thread_id
    
    try:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"Calling LLM: model={model}, messages={len(clean_messages)}, tools={len(tools)}, save={save}")
        
        headers = build_headers(token)
        resp = post_stream(url, headers, payload, timeout)
        result = process_tool_calls_stream(resp)
        
        return result
    
    except Exception as e:
        LOG.error(f"LLM call failed: {e}")
        raise


def fetch_mcp_tools(tool_names: List[str], mcp_url: str) -> List[Dict[str, Any]]:
    """Fetch MCP tool specifications."""
    url = f"{mcp_url}/tools"
    
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        all_tools = resp.json()
        
        tools_spec: List[Dict[str, Any]] = []
        found_names: set = set()
        
        for item in all_tools or []:
            if not isinstance(item, dict):
                continue
            
            item_name = item.get("name")
            if item_name in tool_names:
                spec_str = item.get("json")
                if not spec_str:
                    continue
                
                try:
                    spec = json.loads(spec_str)
                except Exception:
                    continue
                
                func_spec = spec.get("function") if isinstance(spec, dict) else None
                if not isinstance(func_spec, dict):
                    continue
                
                tools_spec.append({"type": "function", "function": func_spec})
                found_names.add(item_name)
        
        missing = set(tool_names) - found_names
        if missing:
            raise ValueError(f"Tools not found in MCP: {list(missing)}")
        
        return tools_spec
    
    except Exception as e:
        LOG.error(f"Failed to fetch MCP tools: {e}")
        raise
