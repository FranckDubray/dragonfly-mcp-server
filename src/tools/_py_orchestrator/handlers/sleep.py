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
        Sleep for specified duration (cooperative).
        
        Supports either 'seconds' (float) or 'ms' (milliseconds) inputs.
        
        Args:
            seconds: Sleep duration (int or float seconds)
            ms: Sleep duration in milliseconds (int or float)
        
        Returns:
            {"slept": actual_seconds} (may be less if canceled)
        """
        seconds = kwargs.get('seconds')
        ms = kwargs.get('ms')
        # Prefer explicit milliseconds if provided
        if seconds is None and ms is not None:
            try:
                seconds = float(ms) / 1000.0
            except Exception:
                seconds = None
        if seconds is None:
            seconds = 1
        try:
            seconds = float(seconds)
        except Exception:
            seconds = 1.0
        
        tick = 0.5  # Check cancel every 0.5s
        remaining = max(0.0, seconds)
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
