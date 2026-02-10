"""Agent loop logic for chat_agent.

Handles the multi-turn iteration:
1. Call LLM with current messages
2. If tool_calls → execute tools → add results → loop
3. If stop → return final response

IMPORTANT: Platform save strategy v2 (FIXED)
- ALWAYS save=True to persist complete conversation including tool results
- Platform handles message deduplication via id/parentId/level
- No need for separate "save-only" calls (wasteful LLM invocations)
"""

from __future__ import annotations

import time
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from .platform_api import call_llm_streaming
from .executor import execute_tools, _trim_val
from .thread_utils import estimate_tokens

LOG = logging.getLogger(__name__)


def _gen_call_id() -> str:
    """Generate guaranteed unique call ID using UUID4."""
    return f"call_{uuid.uuid4().hex}"


def _normalize_tool_calls(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize tool_calls and ALWAYS generate new unique IDs.
    
    CRITICAL: We always replace IDs because:
    1. LLM may reuse the same call_id across iterations
    2. Platform indexes/overwrites by call_id
    3. Duplicate IDs cause data loss in thread history
    """
    norm: List[Dict[str, Any]] = []
    for tc in tool_calls or []:
        tc = dict(tc) if isinstance(tc, dict) else {}

        # ALWAYS generate new unique ID to avoid Platform collisions
        tc["id"] = _gen_call_id()
        
        if not tc.get("type"):
            tc["type"] = "function"

        fn = tc.get("function") if isinstance(tc.get("function"), dict) else None
        if not fn:
            # tolerate older shapes
            fname = tc.get("name")
            fargs = tc.get("arguments") or "{}"
            fn = {"name": fname, "arguments": fargs}

        args = fn.get("arguments")
        if args is None:
            args = "{}"
        if not isinstance(args, str):
            args = json.dumps(args)

        tc["function"] = {"name": fn.get("name"), "arguments": args}
        norm.append(tc)

    return norm


def execute_agent_loop(
    messages: List[Dict[str, Any]],
    thread_chain,  # ThreadChain instance
    model: str,
    tools_spec: List[Dict[str, Any]],
    system_prompt: str,
    temperature: float,
    token: str,
    api_base: str,
    mcp_url: str,
    thread_id: Optional[str],
    max_iterations: int,
    timeout: int,
    start_time: float,
    parallel_execution: bool,
    context_limit: int
) -> Dict[str, Any]:
    """Execute agent multi-turn loop.
    
    Platform save strategy v2 (FIXED):
    - ALWAYS save=True to persist complete conversation including tool results
    - Platform handles message deduplication via id/parentId/level
    - No separate "save-only" calls (eliminates wasteful LLM invocations)
    
    Returns:
        Dict with:
        - success: bool
        - response: Final text response
        - thread_id: Thread ID
        - iterations: Number of iterations
        - operations: List of operations (tool calls with results and debug)
        - usage: Token usage
        - error: Error message if failed
    """
    operations = []
    cumulative_usage = {}
    iteration = 0
    returned_thread_id = thread_id
    
    while iteration < max_iterations:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            return {
                "success": False,
                "error": f"Timeout reached ({timeout}s) at iteration {iteration + 1}",
                "thread_id": returned_thread_id,
                "iterations": iteration,
                "operations": operations,
                "usage": cumulative_usage
            }
        
        iteration += 1
        remaining_timeout = max(10, int(timeout - elapsed))
        
        # Check context size before each call (preventive)
        estimated = estimate_tokens(messages)
        if estimated > context_limit * 0.95:  # 95% threshold (emergency)
            return {
                "success": False,
                "error": "ContextTooLarge",
                "message": f"Context grew too large during execution (estimated: {estimated} tokens)",
                "hint": "Conversation exceeded model capacity. Start a new thread.",
                "thread_id": returned_thread_id,
                "iterations": iteration,
                "operations": operations,
                "usage": cumulative_usage
            }
        
        # Save strategy v2: Always save to persist tool results
        # The Platform handles message deduplication via id/parentId
        should_save = True
        
        # Call LLM
        try:
            llm_result = call_llm_streaming(
                messages=messages,
                model=model,
                tools=tools_spec,
                system_prompt=system_prompt,
                temperature=temperature,
                token=token,
                api_base=api_base,
                thread_id=returned_thread_id,
                timeout=remaining_timeout,
                save=should_save
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"LLM call failed at iteration {iteration}: {e}",
                "thread_id": returned_thread_id,
                "iterations": iteration,
                "operations": operations,
                "usage": cumulative_usage
            }
        
        # Update thread_id if returned (new thread created)
        if llm_result.get("thread_id") and not returned_thread_id:
            returned_thread_id = llm_result.get("thread_id")
            LOG.info(f"New thread created: {returned_thread_id}")
        
        # Merge usage
        if llm_result.get("usage"):
            _merge_usage(cumulative_usage, llm_result.get("usage"))
        
        finish_reason = llm_result.get("finish_reason")
        content = llm_result.get("text", "")
        tool_calls = llm_result.get("tool_calls", [])
        
        # Normalize tool_calls (ALWAYS generates new unique IDs)
        tool_calls = _normalize_tool_calls(tool_calls)
        
        # If no tool_calls → final response
        if not tool_calls:
            # Add final assistant message to history
            if content:
                messages.append({
                    "role": "assistant",
                    "content": [{"type": "text", "text": content}],
                })
            
            # Track with ThreadChain for debugging
            thread_chain.new_assistant_text(content)
            
            operations.append({
                "iteration": iteration,
                "tool_calls": []
            })
            
            # No need for separate save call - already saved in LLM call above
            
            return {
                "success": True,
                "response": content,
                "thread_id": returned_thread_id,
                "iterations": iteration,
                "operations": operations,
                "usage": cumulative_usage
            }
        
        # Tool calls present → execute
        try:
            tool_results = execute_tools(
                tool_calls=tool_calls,
                mcp_url=mcp_url,
                parallel=parallel_execution
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed at iteration {iteration}: {e}",
                "thread_id": returned_thread_id,
                "iterations": iteration,
                "operations": operations,
                "usage": cumulative_usage
            }
        
        # Build tool_calls with functionOutput for Platform storage
        tool_calls_with_output = []
        for tc, tool_res in zip(tool_calls, tool_results):
            actual_result = tool_res.get("result", tool_res)
            tool_content = json.dumps(actual_result, ensure_ascii=False)
            
            tool_calls_with_output.append({
                "id": tc.get("id"),
                "type": tc.get("type", "function"),
                "function": {
                    "name": tc.get("function", {}).get("name"),
                    "arguments": tc.get("function", {}).get("arguments", "{}"),
                    "functionOutput": tool_content
                }
            })
        
        # Add assistant message with tool_calls (including functionOutput)
        messages.append({
            "role": "assistant",
            "content": [],
            "tool_calls": tool_calls_with_output,
        })
        
        # Track with ThreadChain for debugging
        thread_chain.new_assistant_tool_calls(tool_calls)
        
        # Add tool result messages (Platform format)
        for tc, tool_res in zip(tool_calls, tool_results):
            actual_result = tool_res.get("result", tool_res)
            tool_content = json.dumps(actual_result, ensure_ascii=False)
            
            messages.append({
                "role": "tool",
                "content": [{"type": "text", "text": tool_content}],
                "tool_call_id": tc.get("id"),
            })
            
            thread_chain.new_tool_result(tc.get("id"), tool_content)
        
        # Record operation
        op = {
            "iteration": iteration,
            "tool_calls": _format_tool_calls_for_operations(tool_calls, tool_results)
        }
        operations.append(op)
    
    # Max iterations reached - already saved in last LLM call
    return {
        "success": False,
        "error": f"Max iterations ({max_iterations}) reached without natural completion",
        "hint": "Increase max_iterations or simplify the task",
        "thread_id": returned_thread_id,
        "iterations": iteration,
        "operations": operations,
        "usage": cumulative_usage
    }


def _merge_usage(cumulative: Dict[str, Any], new_usage: Dict[str, Any]) -> None:
    """Merge token usage into cumulative dict."""
    if not isinstance(new_usage, dict):
        return
    
    for key, value in new_usage.items():
        if isinstance(value, (int, float)):
            cumulative[key] = cumulative.get(key, 0) + value
        elif key not in cumulative:
            cumulative[key] = value


def _format_tool_calls_for_operations(
    tool_calls: List[Dict[str, Any]],
    tool_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Format tool_calls with results for operations list."""
    formatted = []
    
    for tc, tool_res in zip(tool_calls, tool_results):
        fn = tc.get("function", {})
        actual_result = tool_res.get("result", tool_res)
        debug_info = tool_res.get("debug", {})
        
        item = {
            "name": fn.get("name"),
            "arguments": fn.get("arguments"),
            "result_excerpt": _trim_val(actual_result, 2000),
            "mcp_debug": debug_info
        }
        formatted.append(item)
    
    return formatted
