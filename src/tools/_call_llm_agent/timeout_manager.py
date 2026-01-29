"""
Timeout management for LLM Agent workflow.
"""
import time
from typing import Dict, Any


class TimeoutManager:
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        self.start_time = time.time()
    
    def remaining(self) -> int:
        elapsed = time.time() - self.start_time
        remaining = max(10, int(self.timeout_seconds - elapsed))
        return remaining
    
    def is_expired(self) -> bool:
        return time.time() - self.start_time >= self.timeout_seconds
    
    def build_timeout_error(self, iteration: int) -> Dict[str, Any]:
        elapsed = time.time() - self.start_time
        return {
            "error": f"Global timeout reached ({self.timeout_seconds}s) at iteration {iteration}",
            "elapsed_seconds": round(elapsed, 2),
            "iterations": iteration,
            "usage_cumulative": {},
        }
