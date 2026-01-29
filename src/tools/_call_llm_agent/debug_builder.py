"""
Debug builder for detailed LLM Agent execution tracking.
"""
from typing import Dict, Any, List


def _trim_val(x: Any, limit: int = 2000) -> Any:
    """Trim long values for debug output."""
    try:
        if isinstance(x, dict):
            return {k: _trim_val(v, limit) for k, v in x.items()}
        if isinstance(x, list):
            return [_trim_val(v, limit) for v in x]
        if isinstance(x, str) and len(x) > limit:
            return x[:limit] + f"... (+{len(x)-limit} chars)"
    except Exception:
        return x
    return x


class DebugBuilder:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.meta: Dict[str, Any] = {}
        self.iterations: List[Dict[str, Any]] = []
    
    def set_meta(self, meta: Dict[str, Any]):
        if self.enabled:
            self.meta = meta
    
    def add_iteration(self, iteration: int, iter_result: Dict[str, Any]):
        if not self.enabled:
            return
        
        # Extract key info
        debug_entry = {
            "iteration": iteration,
            "finish_reason": iter_result.get("finish_reason"),
            "tool_calls_count": len(iter_result.get("tool_calls", [])),
            "usage": iter_result.get("usage"),
        }
        
        # Tool calls details
        if iter_result.get("tool_calls"):
            tool_calls_debug = []
            for i, tc in enumerate(iter_result["tool_calls"]):
                fname = (tc.get("function") or {}).get("name")
                args = (tc.get("function") or {}).get("arguments", "{}")
                result = iter_result.get("tool_results", [])[i] if i < len(iter_result.get("tool_results", [])) else {}
                
                tool_calls_debug.append({
                    "name": fname,
                    "arguments": _trim_val(args, 500),
                    "result_preview": _trim_val(result, 1000),
                })
            
            debug_entry["tool_calls"] = tool_calls_debug
        
        # Content if present
        if iter_result.get("content"):
            debug_entry["content_length"] = len(iter_result["content"])
            debug_entry["content_preview"] = _trim_val(iter_result["content"], 500)
        
        self.iterations.append(debug_entry)
    
    def finalize(self, usage_cumulative: Dict[str, Any], total_iterations: int):
        if self.enabled:
            self.meta["total_iterations"] = total_iterations
            self.meta["usage_cumulative"] = usage_cumulative
    
    def get(self) -> Dict[str, Any]:
        if not self.enabled:
            return {}
        return {
            "meta": self.meta,
            "iterations": self.iterations,
        }
