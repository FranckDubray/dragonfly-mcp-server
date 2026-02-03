"""SSE stream processing for chat_agent (independent from _call_llm).

Extracts:
- Text content
- Tool calls
- Finish reason
- Thread ID
- Usage
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

LOG = logging.getLogger(__name__)


def process_sse_stream(response) -> Dict[str, Any]:
    """Process SSE stream from Platform API.
    
    Args:
        response: requests.Response object (stream=True)
    
    Returns:
        Dict with:
        - content: Accumulated text
        - tool_calls: List of tool_calls (if any)
        - finish_reason: "stop" or "tool_calls"
        - usage: Token usage dict
        - thread_id: Thread ID from stream
    """
    content = ""
    finish_reason = None
    thread_id = None
    usage = None
    tool_calls_fragments: Dict[int, Dict[str, Any]] = {}
    
    for line_bytes in response.iter_lines():
        if not line_bytes:
            continue
        
        line = line_bytes.decode('utf-8').strip()
        
        # Extract data from SSE line
        data_str = _extract_data_str(line)
        if data_str is None:
            continue
        
        if data_str == '[DONE]':
            break
        
        try:
            chunk = json.loads(data_str)
        except Exception:
            continue
        
        # Extract thread_id (may appear in any chunk)
        if not thread_id and chunk.get("thread_id"):
            thread_id = chunk.get("thread_id")
        
        # Extract usage (usually in last chunk)
        if chunk.get("usage"):
            usage = chunk.get("usage")
        
        # Extract choices
        choices = chunk.get("choices")
        if not isinstance(choices, list) or not choices:
            continue
        
        choice = choices[0]
        if not isinstance(choice, dict):
            continue
        
        # Finish reason
        if choice.get("finish_reason"):
            finish_reason = choice.get("finish_reason")
        
        # Delta content
        delta = choice.get("delta")
        if not isinstance(delta, dict):
            continue
        
        # Text content
        delta_content = delta.get("content")
        if delta_content:
            content += delta_content
        
        # Tool calls (streaming format)
        delta_tool_calls = delta.get("tool_calls")
        if isinstance(delta_tool_calls, list):
            for tc_delta in delta_tool_calls:
                if not isinstance(tc_delta, dict):
                    continue
                
                idx = tc_delta.get("index")
                if idx is None:
                    continue
                
                # Initialize fragment if new
                if idx not in tool_calls_fragments:
                    tool_calls_fragments[idx] = {
                        "id": "",
                        "type": "function",
                        "function": {
                            "name": "",
                            "arguments": ""
                        }
                    }
                
                # Accumulate fields
                if tc_delta.get("id"):
                    tool_calls_fragments[idx]["id"] = tc_delta.get("id")
                
                if tc_delta.get("type"):
                    tool_calls_fragments[idx]["type"] = tc_delta.get("type")
                
                fn_delta = tc_delta.get("function")
                if isinstance(fn_delta, dict):
                    if fn_delta.get("name"):
                        tool_calls_fragments[idx]["function"]["name"] += fn_delta.get("name", "")
                    
                    if fn_delta.get("arguments"):
                        tool_calls_fragments[idx]["function"]["arguments"] += fn_delta.get("arguments", "")
    
    # Reconstruct tool_calls list
    tool_calls: List[Dict[str, Any]] = []
    if tool_calls_fragments:
        for idx in sorted(tool_calls_fragments.keys()):
            tool_calls.append(tool_calls_fragments[idx])
    
    # Normalize finish_reason
    if not finish_reason:
        finish_reason = "tool_calls" if tool_calls else "stop"
    
    return {
        "content": content,
        "tool_calls": tool_calls,
        "finish_reason": finish_reason,
        "usage": usage,
        "thread_id": thread_id,
    }


def _extract_data_str(line: str) -> str:
    """Extract data string from SSE line.
    
    Args:
        line: SSE line (e.g., "data: {...}")
    
    Returns:
        Data string or None if not a data line
    """
    if not line.startswith("data:"):
        return None
    
    return line[5:].strip()
