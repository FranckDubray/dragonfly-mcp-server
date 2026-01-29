from __future__ import annotations
"""
Core LLM Agent orchestrator with multi-turn loop.

The LLM can call tools in sequence, using previous results
to decide next calls. Stops naturally when finish_reason="stop".
"""
from typing import Any, Dict, List, Optional
import os
import logging

from .loop import execute_single_iteration
from .prompts import DEFAULT_AGENT_PROMPT
from .debug_builder import DebugBuilder
from .cost_calculator import CostCalculator
from .timeout_manager import TimeoutManager

LOG = logging.getLogger(__name__)


def execute_agent(
    message: str,
    model: str,
    tool_names: List[str],
    max_iterations: int = 20,
    agent_prompt: Optional[str] = None,
    temperature: float = 0.5,
    max_tokens: Optional[int] = None,
    timeout_seconds: int = 300,
    parallel_execution: bool = True,
    early_stop_on_error: bool = False,
    debug: bool = False,
    include_cost_breakdown: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """
    Main LLM Agent orchestrator with multi-turn loop.
    
    The LLM can call multiple tools in sequence, using previous results
    to decide next calls. Stops naturally when finish_reason != "tool_calls".
    
    Args:
        message: User question/instruction
        model: LLM model name
        tool_names: List of available MCP tools
        max_iterations: Safety limit (default: 20)
        agent_prompt: Custom system prompt (optional)
        temperature: Sampling temperature (default: 0.5)
        max_tokens: Max tokens for final response
        timeout_seconds: Global timeout (default: 300s)
        parallel_execution: Execute independent tools in parallel (default: True)
        early_stop_on_error: Stop on first tool error (default: False)
        debug: Enable detailed debug tracking (default: False)
        include_cost_breakdown: Include cost analysis (default: True)
    
    Returns:
        {
            "success": True/False,
            "content": "...",
            "iterations": N,
            "usage": {...},
            "cost_breakdown": {...},
            "debug": {...}
        }
    """
    
    # Validation
    token = os.getenv("AI_PORTAL_TOKEN")
    if not token:
        return {"error": "AI_PORTAL_TOKEN required"}
    if not message or not message.strip():
        return {"error": "message required"}
    if not tool_names:
        return {"error": "tool_names required (at least 1 tool)"}
    
    # Configuration
    endpoint = os.getenv("LLM_ENDPOINT", "https://ai.dragonflygroup.fr/api/v1/chat/completions")
    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000")
    prompt_system = agent_prompt or DEFAULT_AGENT_PROMPT
    
    # Initialization
    messages = [{"role": "user", "content": [{"type": "text", "text": message}]}]
    iteration = 0
    debug_builder = DebugBuilder(enabled=debug)
    cost_calc = CostCalculator(enabled=include_cost_breakdown)
    timeout_mgr = TimeoutManager(timeout_seconds)
    
    if LOG.isEnabledFor(logging.INFO):
        LOG.info(f"Agent start: model={model}, tools={len(tool_names)}, max_iter={max_iterations}, timeout={timeout_seconds}s")
    
    # Global metadata
    debug_builder.set_meta({
        "model": model,
        "endpoint": endpoint,
        "mcp_url": mcp_url,
        "tool_names": tool_names,
        "max_iterations": max_iterations,
        "timeout_seconds": timeout_seconds,
        "parallel_execution": parallel_execution,
    })
    
    # ========== MULTI-TURN LOOP ==========
    while iteration < max_iterations:
        # Check global timeout
        if timeout_mgr.is_expired():
            err = timeout_mgr.build_timeout_error(iteration)
            debug_builder.finalize(err.get("usage_cumulative", {}), iteration)
            return {**err, "debug": debug_builder.get()} if debug else err
        
        iteration += 1
        if LOG.isEnabledFor(logging.INFO):
            LOG.info(f"Agent iteration {iteration}/{max_iterations} start")
        
        try:
            # Execute one iteration
            iter_result = execute_single_iteration(
                messages=messages,
                model=model,
                tool_names=tool_names,
                prompt_system=prompt_system,
                temperature=temperature,
                endpoint=endpoint,
                mcp_url=mcp_url,
                token=token,
                parallel_execution=parallel_execution,
                early_stop_on_error=early_stop_on_error,
                timeout_remaining=timeout_mgr.remaining(),
            )
            
            # Record in debug and cost
            debug_builder.add_iteration(iteration, iter_result)
            cost_calc.add_iteration(iteration, iter_result.get("usage"))
            
            # Check critical error
            if iter_result.get("error"):
                if early_stop_on_error or "timeout" in iter_result["error"].lower():
                    debug_builder.finalize(cost_calc.cumulative_usage(), iteration)
                    return {
                        "error": iter_result["error"],
                        "usage": cost_calc.cumulative_usage(),
                        "iterations": iteration,
                        "cost_breakdown": cost_calc.breakdown() if include_cost_breakdown else None,
                        "debug": debug_builder.get() if debug else None,
                    }
            
            # Check finish_reason
            finish_reason = iter_result.get("finish_reason")
            
            if finish_reason == "tool_calls":
                # ✅ LLM wants to call tools → continue
                # Results already added to messages by execute_single_iteration
                if LOG.isEnabledFor(logging.INFO):
                    LOG.info(f"Agent iteration {iteration}: {len(iter_result.get('tool_calls', []))} tools executed, continuing...")
                continue
            
            elif finish_reason == "stop":
                # ✅ LLM finished → final response
                if LOG.isEnabledFor(logging.INFO):
                    LOG.info(f"Agent completed in {iteration} iterations (finish_reason=stop)")
                
                debug_builder.finalize(cost_calc.cumulative_usage(), iteration)
                
                return {
                    "success": True,
                    "content": iter_result.get("content", ""),
                    "finish_reason": "stop",
                    "iterations": iteration,
                    "usage": cost_calc.cumulative_usage(),
                    "cost_breakdown": cost_calc.breakdown() if include_cost_breakdown else None,
                    "debug": debug_builder.get() if debug else None,
                }
            
            else:
                # ⚠️ Unexpected finish_reason (length, error, etc.)
                if LOG.isEnabledFor(logging.WARNING):
                    LOG.warning(f"Agent unexpected finish_reason: {finish_reason}")
                
                debug_builder.finalize(cost_calc.cumulative_usage(), iteration)
                
                return {
                    "success": False,
                    "error": f"Unexpected finish_reason: {finish_reason}",
                    "content": iter_result.get("content", ""),
                    "finish_reason": finish_reason,
                    "iterations": iteration,
                    "usage": cost_calc.cumulative_usage(),
                    "cost_breakdown": cost_calc.breakdown() if include_cost_breakdown else None,
                    "debug": debug_builder.get() if debug else None,
                }
        
        except Exception as e:
            if LOG.isEnabledFor(logging.ERROR):
                LOG.error(f"Agent iteration {iteration} failed: {e}", exc_info=True)
            
            debug_builder.finalize(cost_calc.cumulative_usage(), iteration)
            
            return {
                "error": f"Agent execution failed at iteration {iteration}: {e}",
                "iterations": iteration,
                "usage": cost_calc.cumulative_usage(),
                "cost_breakdown": cost_calc.breakdown() if include_cost_breakdown else None,
                "debug": debug_builder.get() if debug else None,
            }
    
    # ⚠️ Max iterations reached (safety)
    if LOG.isEnabledFor(logging.WARNING):
        LOG.warning(f"Agent reached max iterations ({max_iterations})")
    
    debug_builder.finalize(cost_calc.cumulative_usage(), iteration)
    
    return {
        "error": f"Max iterations reached ({max_iterations}). Agent did not finish naturally.",
        "iterations": iteration,
        "usage": cost_calc.cumulative_usage(),
        "cost_breakdown": cost_calc.breakdown() if include_cost_breakdown else None,
        "debug": debug_builder.get() if debug else None,
        "hint": "Increase max_iterations or simplify the task.",
    }
