# Sleep handler (cooperative, checks cancel flag)

import time
from typing import Dict, Any, Callable
from .base import AbstractHandler

class SleepHandler(AbstractHandler):
    """Cooperative sleep handler (checks cancel flag on each tick)"""
    
    def __init__(self, cancel_flag_fn: Callable[[], bool]):
        """
        Args:
            cancel_flag_fn: Callable that returns True if canceled
        """
        self._cancel_flag_fn = cancel_flag_fn
    
    @property
    def kind(self) -> str:
        return "sleep"
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Sleep for specified seconds (cooperative).
        
        Args:
            seconds: Sleep duration (int or float)
        
        Returns:
            {"slept": actual_seconds} (may be less if canceled)
        """
        seconds = kwargs.get('seconds', 1)
        if not isinstance(seconds, (int, float)):
            seconds = float(seconds)
        
        tick = 0.5  # Check cancel every 0.5s
        remaining = seconds
        slept = 0.0
        
        while remaining > 0:
            if self._cancel_flag_fn():
                # Canceled early
                break
            
            sleep_duration = min(tick, remaining)
            time.sleep(sleep_duration)
            slept += sleep_duration
            remaining -= sleep_duration
        
        return {"slept": slept}
