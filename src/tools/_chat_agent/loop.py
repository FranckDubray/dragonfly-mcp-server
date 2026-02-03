"""Agent loop logic for chat_agent.

Handles the multi-turn iteration:
1. Call LLM with current messages
2. If tool_calls → execute tools → add results → loop
3. If stop → return final response
"""

from __future__ import annotations

import time
import json
import logging
import random
import string
from typing import Any, Dict, List, Optional

from .platform_api import call_llm_streaming
from .executor import execute_tools
from .thread_utils import estimate_tokens

LOG = logging.getLogger(__name__)


def _gen_call_id() -> str:
    """Generate unique call ID."""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"call_{int(time.time()*1000)}_{suffix}"


def _normalize_tool_calls(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure each tool_call has id + type + function{name,arguments(str)}."""
    norm: List[Dict[str, Any]] = []
    for tc in tool_calls or []:
        tc = dict(tc) if isinstance(tc, dict) else {}

        if not tc.get("id"):
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
    
    Returns:
        Dict with:
        - success: bool
        - response: Final text response
        - thread_id: Thread ID
        - iterations: Number of iterations
        - operations: List of operations (tool calls)
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
                timeout=remaining_timeout
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
        
        # Normalize tool_calls (ensure id, type, function)
        tool_calls = _normalize_tool_calls(tool_calls)
        
        # If no tool_calls → final response
        if not tool_calls:
            # Track with ThreadChain for debugging
            thread_chain.new_assistant_text(content)
            
            operations.append({
                "iteration": iteration,
                "tool_calls": []
            })
            
            return {
                "success": True,
                "response": content,
                "thread_id": returned_thread_id,
                "iterations": iteration,
                "operations": operations,
                "usage": cumulative_usage
            }
        
        # Tool calls present → execute
        # 1. Add assistant tool_calls message (OpenAI format, NO id/parentId/level)
        messages.append({
            "role": "assistant",
            "tool_calls": tool_calls,
        })
        
        # Track with ThreadChain for debugging
        thread_chain.new_assistant_tool_calls(tool_calls)
        
        # 2. Execute tools
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
        
        # 3. Add tool result messages (OpenAI format, NO id/parentId/level)
        for tc, result in zip(tool_calls, tool_results):
            # Extract actual result (handle nested structure)
            tool_content = json.dumps(result.get("result", result), ensure_ascii=False)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id"),
                "content": tool_content,
            })
            
            # Track with ThreadChain for debugging
            thread_chain.new_tool_result(tc.get("id"), tool_content)
        
        # 4. Record operation
        op = {
            "iteration": iteration,
            "tool_calls": _format_tool_calls_for_operations(tool_calls, tool_results)
        }
        operations.append(op)
        
        # Loop continues
    
    # Max iterations reached
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
    
    for tc, result in zip(tool_calls, tool_results):
        fn = tc.get("function", {})
        
        item = {
            "name": fn.get("name"),
            "arguments": fn.get("arguments"),
            "result": result
        }
        
        formatted.append(item)
    
    return formatted
