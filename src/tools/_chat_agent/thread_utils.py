"""Utilities for converting Platform thread format to OpenAI messages.

Handles reconstruction of tool_calls and tool messages from platform storage.
"""

from __future__ import annotations

from typing import Any, Dict, List

ROOT_PARENT_ID = "000170695000"


def platform_history_to_thread_messages(raw_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert platform assistantContentJson to OpenAI messages with id/parentId/level.
    
    Properly handles:
    - Messages with toolCalls stored in platform
    - Tool result messages (functionOutput)
    - Linear chain reconstruction from last AI message backwards
    
    Args:
        raw_messages: List from platform's assistantContentJson
    
    Returns:
        List of OpenAI-format messages with id/parentId/level
    """
    if not raw_messages:
        return []
    
    # Filter invalid messages
    filtered: List[Dict[str, Any]] = []
    for m in raw_messages:
        mid = str(m.get("id", ""))
        pid = str(m.get("parentId", ""))
        
        # Drop id==parentId (safety)
        if mid and pid and mid == pid:
            continue
        
        # Keep user messages
        if m.get("sender") == "user":
            filtered.append(m)
            continue
        
        # Keep AI messages if they have text OR toolCalls
        if m.get("sender") == "ai":
            has_text = bool((m.get("text") or "").strip())
            has_tools = bool(m.get("toolCalls"))
            if has_text or has_tools:
                filtered.append(m)
    
    raw_messages = filtered
    if not raw_messages:
        return []
    
    # Index by ID
    id_map: Dict[str, Dict[str, Any]] = {}
    for m in raw_messages:
        mid = str(m.get("id", ""))
        if mid:
            id_map[mid] = m
    
    # Find last AI message (leaf)
    def ts(x):
        return x.get("timestamp", 0) or 0
    
    ai_msgs = [m for m in raw_messages if m.get("sender") == "ai"]
    if ai_msgs:
        ai_msgs.sort(key=ts)
        leaf_id = str(ai_msgs[-1].get("id"))
    else:
        raw_messages.sort(key=ts)
        leaf_id = str(raw_messages[-1].get("id"))
    
    # Walk parents to build chain
    chain: List[Dict[str, Any]] = []
    seen: set[str] = set()
    cur = leaf_id
    
    while cur and cur not in seen:
        seen.add(cur)
        m = id_map.get(cur)
        if not m:
            break
        chain.append(m)
        
        pid = m.get("parentId")
        if pid is None:
            break
        pid_str = str(pid)
        if pid_str == ROOT_PARENT_ID:
            break
        if pid_str not in id_map:
            break
        cur = pid_str
    
    chain.reverse()
    
    # Build OpenAI messages
    out: List[Dict[str, Any]] = []
    level = 0
    
    for m in chain:
        role = "assistant" if m.get("sender") == "ai" else "user"
        
        msg = {
            "role": role,
            "id": m.get("id"),
            "parentId": m.get("parentId"),
            "level": level,
        }
        
        # Handle AI messages with toolCalls
        if role == "assistant" and m.get("toolCalls"):
            tool_calls_openai = []
            
            for tc in m.get("toolCalls", []):
                if not tc:
                    continue
                
                tc_id = tc.get("id")
                tc_type = tc.get("type", "function")
                tc_func = tc.get("function", {})
                
                tool_call = {
                    "id": tc_id,
                    "type": tc_type,
                    "function": {
                        "name": tc_func.get("name", ""),
                        "arguments": tc_func.get("arguments", "{}")
                    }
                }
                tool_calls_openai.append(tool_call)
                
                # Check for functionOutput → create tool result message
                func_output = tc_func.get("functionOutput")
                if func_output is not None:
                    level += 1
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": str(func_output),
                        "id": f"{m.get('id')}_tool_{tc_id}",
                        "parentId": m.get("id"),
                        "level": level,
                    }
                    out.append(tool_msg)
            
            msg["tool_calls"] = tool_calls_openai
            
            # If text is also present (final response hack), include it
            if m.get("text"):
                msg["content"] = [{"type": "text", "text": m.get("text")}]
        
        else:
            # Standard text content
            msg["content"] = [{"type": "text", "text": m.get("text", "")}]
        
        out.append(msg)
        level += 1
    
    return out


def estimate_tokens(messages: List[Dict[str, Any]]) -> int:
    """Rough estimation of token count for messages.
    
    Formula: (total_chars / 4) + (message_count * 10)
    This is a conservative estimate (4 chars/token is typical for English).
    
    Args:
        messages: List of messages
    
    Returns:
        Estimated token count
    """
    total_chars = 0
    
    for m in messages:
        # Content
        content = m.get("content")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    total_chars += len(part.get("text", ""))
        elif isinstance(content, str):
            total_chars += len(content)
        
        # Tool calls
        tool_calls = m.get("tool_calls")
        if isinstance(tool_calls, list):
            for tc in tool_calls:
                if isinstance(tc, dict):
                    fn = tc.get("function", {})
                    total_chars += len(fn.get("name", ""))
                    total_chars += len(fn.get("arguments", ""))
        
        # Tool results
        if m.get("role") == "tool":
            total_chars += len(m.get("content", ""))
    
    # Conservative estimate: 4 chars/token + overhead per message
    estimated = (total_chars // 4) + (len(messages) * 10)
    return estimated
