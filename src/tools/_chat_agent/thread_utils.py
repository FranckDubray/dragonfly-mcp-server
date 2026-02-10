"""Utilities for converting Platform thread format to OpenAI messages.

v3: Fixed to properly extract functionOutput from Platform storage.
Platform stores tool results in TWO places:
1. tool_calls[].function.functionOutput (in assistant message)
2. role=tool messages with content array

We prioritize functionOutput since it's in the same message structure.
"""

from __future__ import annotations

from typing import Any, Dict, List

ROOT_PARENT_ID = "000170695000"


def platform_history_to_thread_messages(raw_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert platform assistantContentJson to OpenAI messages.
    
    v3 strategy: Chronological sort, extract functionOutput properly.
    
    Platform stores messages with:
    - role=user: User messages with content array
    - role=assistant: AI responses, may have tool_calls with functionOutput
    - role=tool: Tool results with content array and tool_call_id
    
    Args:
        raw_messages: List from platform's assistantContentJson
    
    Returns:
        List of OpenAI-format messages (chronological order)
    """
    if not raw_messages:
        return []
    
    # Sort by timestamp (chronological)
    sorted_msgs = sorted(raw_messages, key=lambda m: m.get("timestamp", 0) or 0)
    
    out: List[Dict[str, Any]] = []
    
    for m in sorted_msgs:
        role = m.get("role", "")
        
        # --- USER MESSAGE ---
        if role == "user":
            text = _extract_text_content(m)
            if text:
                out.append({
                    "role": "user",
                    "content": [{"type": "text", "text": text}],
                })
            continue
        
        # --- ASSISTANT MESSAGE ---
        if role == "assistant":
            tool_calls_raw = m.get("tool_calls") or []
            text = _extract_text_content(m)
            
            # Has tool_calls?
            if tool_calls_raw:
                _append_assistant_with_tools(out, tool_calls_raw)
                continue
            
            # Plain text response
            if text:
                out.append({
                    "role": "assistant",
                    "content": [{"type": "text", "text": text}],
                })
            continue
        
        # --- TOOL MESSAGE ---
        if role == "tool":
            tool_call_id = m.get("tool_call_id") or m.get("id")
            text = _extract_text_content(m)
            
            if tool_call_id and text:
                out.append({
                    "role": "tool",
                    "content": [{"type": "text", "text": text}],
                    "tool_call_id": tool_call_id,
                })
            continue
        
        # --- LEGACY FORMAT (sender field) ---
        sender = m.get("sender", "")
        
        if sender == "user":
            text = (m.get("text") or "").strip()
            if text:
                out.append({
                    "role": "user",
                    "content": [{"type": "text", "text": text}],
                })
            continue
        
        if sender == "ai":
            tool_calls_raw = m.get("toolCalls") or []
            text = (m.get("text") or "").strip()
            
            if tool_calls_raw:
                _append_assistant_with_tools(out, tool_calls_raw)
                continue
            
            if text:
                out.append({
                    "role": "assistant",
                    "content": [{"type": "text", "text": text}],
                })
            continue
    
    return out


def _extract_text_content(m: Dict[str, Any]) -> str:
    """Extract text from message content (handles array and string formats)."""
    content = m.get("content")
    
    # Array format: [{"type": "text", "text": "..."}]
    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                texts.append(part.get("text", ""))
        return " ".join(texts).strip()
    
    # String format
    if isinstance(content, str):
        return content.strip()
    
    # Legacy: direct text field
    text = m.get("text")
    if isinstance(text, str):
        return text.strip()
    
    return ""


def _append_assistant_with_tools(
    out: List[Dict[str, Any]],
    tool_calls_raw: List[Dict[str, Any]]
) -> None:
    """Append assistant message with tool_calls AND corresponding tool results.
    
    Extracts functionOutput from each tool_call to build the tool result messages.
    """
    openai_tool_calls = []
    tool_results = []
    
    for tc in tool_calls_raw:
        if not tc:
            continue
        
        tc_id = tc.get("id") or f"call_unknown_{id(tc)}"
        tc_type = tc.get("type", "function")
        func = tc.get("function", {})
        
        openai_tool_calls.append({
            "id": tc_id,
            "type": tc_type,
            "function": {
                "name": func.get("name", ""),
                "arguments": func.get("arguments", "{}"),
            }
        })
        
        # Extract functionOutput (the actual tool result!)
        func_output = func.get("functionOutput")
        
        if func_output is not None and str(func_output) not in ("None", "null", ""):
            result_content = str(func_output)
        else:
            # Fallback: Platform didn't store the result
            result_content = json.dumps({
                "note": "Tool result not available in thread history",
                "tool": func.get("name", "unknown"),
                "arguments_preview": str(func.get("arguments", ""))[:200]
            })
        
        tool_results.append({
            "tool_call_id": tc_id,
            "content": result_content
        })
    
    if not openai_tool_calls:
        return
    
    # Add assistant message with tool_calls
    out.append({
        "role": "assistant",
        "content": [],  # Empty when tool_calls present
        "tool_calls": openai_tool_calls,
    })
    
    # Add tool result messages
    for tr in tool_results:
        out.append({
            "role": "tool",
            "content": [{"type": "text", "text": tr["content"]}],
            "tool_call_id": tr["tool_call_id"],
        })


def estimate_tokens(messages: List[Dict[str, Any]]) -> int:
    """Rough estimation of token count for messages.
    
    Formula: (total_chars / 4) + (message_count * 10)
    Conservative estimate (4 chars/token typical for English).
    
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
                    # Include functionOutput in estimation
                    total_chars += len(str(fn.get("functionOutput", "")))
        
        # Tool results
        if m.get("role") == "tool":
            content = m.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        total_chars += len(part.get("text", ""))
            elif isinstance(content, str):
                total_chars += len(content)
    
    estimated = (total_chars // 4) + (len(messages) * 10)
    return estimated


# Required import for json.dumps in fallback
import json
