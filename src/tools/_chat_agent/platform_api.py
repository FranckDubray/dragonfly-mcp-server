"""Platform API wrapper for chat_agent.

Handles:
- Thread retrieval (GET /threads/{id})
- Chat completions with streaming (POST /chat/completions)
- Model validation (GET /models)
"""

from typing import Any, Dict, List, Optional
import requests
import logging
import json

LOG = logging.getLogger(__name__)


def get_thread_history(
    thread_id: str,
    token: str,
    api_base: str
) -> List[Dict[str, Any]]:
    """Retrieve thread history from Platform API.
    
    Args:
        thread_id: Thread ID to retrieve
        token: AI_PORTAL_TOKEN
        api_base: API base URL
    
    Returns:
        List of messages with id/parentId/level (converted from platform format)
    
    Raises:
        Exception if thread not found or API error
    """
    url = f"{api_base}/threads/{thread_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"Fetching thread: {url}")
        
        resp = requests.get(url, headers=headers, timeout=30)
        
        if resp.status_code == 404:
            raise ValueError(f"Thread '{thread_id}' not found")
        
        resp.raise_for_status()
        data = resp.json()
        
        # Extract assistant content
        raw_messages = data.get("assistantContentJson", [])
        if not raw_messages:
            LOG.warning(f"Thread {thread_id} has no messages")
            return []
        
        # Convert platform format to OpenAI messages with id/parentId/level
        from .thread_utils import platform_history_to_thread_messages
        messages = platform_history_to_thread_messages(raw_messages)
        
        LOG.info(f"Loaded {len(messages)} messages from thread {thread_id}")
        return messages
    
    except Exception as e:
        LOG.error(f"Failed to fetch thread history: {e}")
        raise


def call_llm_streaming(
    messages: List[Dict[str, Any]],
    model: str,
    tools: List[Dict[str, Any]],
    system_prompt: str,
    temperature: float,
    token: str,
    api_base: str,
    thread_id: Optional[str] = None,
    timeout: int = 300
) -> Dict[str, Any]:
    """Call LLM with streaming enabled - USING _call_llm streaming parser.
    
    Args:
        messages: Full message history (with id/parentId/level)
        model: Model name
        tools: MCP tools spec (OpenAI format)
        system_prompt: System prompt
        temperature: Sampling temperature
        token: AI_PORTAL_TOKEN
        api_base: API base URL
        thread_id: Optional thread ID (for continuation)
        timeout: Request timeout
    
    Returns:
        Dict with:
        - content: Final text response
        - tool_calls: List of tool_calls (if any)
        - finish_reason: "stop" or "tool_calls"
        - usage: Token usage dict
        - thread_id: Thread ID (new or existing)
    
    Raises:
        Exception if API call fails
    """
    # Use the PROVEN streaming implementation from _call_llm
    try:
        from .._call_llm.http_client import build_headers, post_stream
        from .._call_llm.streaming import process_tool_calls_stream
    except ImportError as e:
        raise ImportError(f"Failed to import _call_llm streaming: {e}")
    
    url = f"{api_base}/chat/completions"
    
    # IMPORTANT: Strip id/parentId/level from messages before sending to API
    # The Platform API expects standard OpenAI format without Threading fields
    clean_messages = []
    for msg in messages:
        clean_msg = {}
        
        # Copy only OpenAI-standard fields
        if "role" in msg:
            clean_msg["role"] = msg["role"]
        if "content" in msg:
            clean_msg["content"] = msg["content"]
        if "tool_calls" in msg:
            clean_msg["tool_calls"] = msg["tool_calls"]
        if "tool_call_id" in msg:
            clean_msg["tool_call_id"] = msg["tool_call_id"]
        if "name" in msg:
            clean_msg["name"] = msg["name"]
        
        clean_messages.append(clean_msg)
    
    payload = {
        "model": model,
        "messages": clean_messages,  # Use cleaned messages
        "promptSystem": system_prompt,
        "temperature": temperature,
        "stream": True,
        "save": True,
    }
    
    if tools:
        payload["tools"] = tools
    
    if thread_id:
        payload["threadId"] = thread_id
    
    try:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"Calling LLM: model={model}, messages={len(clean_messages)}, tools={len(tools)}")
        
        headers = build_headers(token)
        resp = post_stream(url, headers, payload, timeout)
        
        # Use the working streaming parser
        result = process_tool_calls_stream(resp)
        
        return result
    
    except Exception as e:
        LOG.error(f"LLM call failed: {e}")
        raise


def fetch_mcp_tools(tool_names: List[str], mcp_url: str) -> List[Dict[str, Any]]:
    """Fetch MCP tool specifications.
    
    Args:
        tool_names: List of tool names to fetch
        mcp_url: MCP server URL (e.g., http://127.0.0.1:8000)
    
    Returns:
        List of OpenAI-format tool specs
    
    Raises:
        Exception if MCP server unreachable or tools not found
    """
    url = f"{mcp_url}/tools"
    
    try:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"Fetching MCP tools from: {url}")
        
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        all_tools = resp.json()
        
        # Filter requested tools
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
                    LOG.warning(f"Failed to parse spec for tool: {item_name}")
                    continue
                
                func_spec = spec.get("function") if isinstance(spec, dict) else None
                if not isinstance(func_spec, dict):
                    continue
                
                tools_spec.append({"type": "function", "function": func_spec})
                found_names.add(item_name)
        
        # Check for missing tools
        missing = set(tool_names) - found_names
        if missing:
            raise ValueError(f"Tools not found in MCP: {list(missing)}")
        
        LOG.info(f"Fetched {len(tools_spec)} MCP tools")
        return tools_spec
    
    except Exception as e:
        LOG.error(f"Failed to fetch MCP tools: {e}")
        raise
