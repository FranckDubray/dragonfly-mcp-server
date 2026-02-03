"""Output formatting for chat_agent based on output_mode."""

from typing import Any, Dict, List


def build_output(
    output_mode: str,
    success: bool,
    response: str,
    thread_id: str,
    iterations: int,
    operations: List[Dict[str, Any]],
    messages: List[Dict[str, Any]],
    usage: Dict[str, Any],
    error: str = None
) -> Dict[str, Any]:
    """Build output based on mode.
    
    Args:
        output_mode: "minimal", "intermediate", or "debug"
        success: Whether execution succeeded
        response: Final assistant response
        thread_id: Thread ID (new or existing)
        iterations: Number of iterations executed
        operations: List of operations (tool calls per iteration)
        messages: Full message history
        usage: Token usage dict
        error: Error message if failed
    
    Returns:
        Formatted output dict
    """
    if output_mode == "minimal":
        return _build_minimal(success, response, thread_id, operations, error)
    
    elif output_mode == "intermediate":
        return _build_intermediate(success, response, thread_id, operations, messages, error)
    
    else:  # debug
        return _build_debug(success, response, thread_id, iterations, operations, messages, usage, error)


def _build_minimal(
    success: bool,
    response: str,
    thread_id: str,
    operations: List[Dict[str, Any]],
    error: str = None
) -> Dict[str, Any]:
    """Minimal output for chatbot use.
    
    Returns:
        {success, response, tools_used, thread_id}
    """
    # Extract unique tool names
    tools_used = set()
    for op in operations:
        for tc in op.get("tool_calls", []):
            if tc.get("name"):
                tools_used.add(tc.get("name"))
    
    out = {
        "success": success,
        "response": response,
        "tools_used": sorted(list(tools_used)),
        "thread_id": thread_id  # AJOUT : Indispensable pour la continuité
    }
    
    if error:
        out["error"] = error
    
    return out


def _build_intermediate(
    success: bool,
    response: str,
    thread_id: str,
    operations: List[Dict[str, Any]],
    messages: List[Dict[str, Any]],
    error: str = None
) -> Dict[str, Any]:
    """Intermediate output for production use.
    
    Returns:
        {success, response, tools_used, thread_id, operations_summary, context_info}
    """
    # Extract unique tool names
    tools_used = set()
    for op in operations:
        for tc in op.get("tool_calls", []):
            if tc.get("name"):
                tools_used.add(tc.get("name"))
    
    # Build operations summary (without full args/results)
    ops_summary = []
    for op in operations:
        tool_names = [tc.get("name") for tc in op.get("tool_calls", [])]
        ops_summary.append({
            "iteration": op.get("iteration"),
            "tools": tool_names,
            "count": len(tool_names)
        })
    
    # Context info
    context_info = {
        "message_count": len(messages),
        "total_iterations": len(operations)
    }
    
    out = {
        "success": success,
        "response": response,
        "tools_used": sorted(list(tools_used)),
        "thread_id": thread_id,
        "operations_summary": ops_summary,
        "context_info": context_info
    }
    
    if error:
        out["error"] = error
    
    return out


def _build_debug(
    success: bool,
    response: str,
    thread_id: str,
    iterations: int,
    operations: List[Dict[str, Any]],
    messages: List[Dict[str, Any]],
    usage: Dict[str, Any],
    error: str = None
) -> Dict[str, Any]:
    """Full debug output.
    
    Returns:
        Full details including tool calls, usage, transcript snapshot
    """
    # Extract unique tool names
    tools_used = set()
    for op in operations:
        for tc in op.get("tool_calls", []):
            if tc.get("name"):
                tools_used.add(tc.get("name"))
    
    # Transcript snapshot (last 10 messages)
    transcript_snapshot = []
    for m in messages[-10:]:
        snapshot_msg = {
            "role": m.get("role"),
        }
        
        # Only include id/level if present (from ThreadChain tracking)
        if m.get("id"):
            snapshot_msg["id"] = m.get("id")
        if m.get("level") is not None:
            snapshot_msg["level"] = m.get("level")
        
        if m.get("content"):
            content = m.get("content")
            if isinstance(content, list) and content:
                snapshot_msg["content_preview"] = content[0].get("text", "")[:200]
            elif isinstance(content, str):
                snapshot_msg["content_preview"] = content[:200]
        
        if m.get("tool_calls"):
            snapshot_msg["tool_calls_count"] = len(m.get("tool_calls"))
        
        if m.get("tool_call_id"):
            snapshot_msg["tool_call_id"] = m.get("tool_call_id")
        
        transcript_snapshot.append(snapshot_msg)
    
    out = {
        "success": success,
        "response": response,
        "tools_used": sorted(list(tools_used)),
        "thread_id": thread_id,
        "iterations": iterations,
        "operations": operations,  # Full details
        "usage": usage,
        "context_info": {
            "message_count": len(messages),
            "total_iterations": len(operations)
        },
        "transcript_snapshot": transcript_snapshot
    }
    
    if error:
        out["error"] = error
    
    return out
