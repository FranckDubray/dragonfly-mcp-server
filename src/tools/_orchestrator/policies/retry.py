# Retry policy execution (node-level retry with exponential backoff)

import time
from typing import Dict, Any, Callable
from ..handlers import HandlerError

class RetryExhaustedError(Exception):
    """Raised when retry policy is exhausted"""
    def __init__(self, attempts: int, last_error: HandlerError):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Retry exhausted after {attempts} attempts: {last_error.message}")

def execute_with_retry(
    handler_fn: Callable[[], Dict[str, Any]],
    retry_policy: Dict,
    on_retry: Callable[[int, HandlerError], None] = None
) -> Dict[str, Any]:
    """
    Execute handler with retry policy.
    
    Args:
        handler_fn: Callable that executes handler (raises HandlerError on failure)
        retry_policy: Retry config ({"max": int, "delay_sec": float})
        on_retry: Optional callback called on each retry (attempt_num, error)
    
    Returns:
        Handler outputs (dict)
    
    Raises:
        RetryExhaustedError: If all retries exhausted
        HandlerError: If non-retryable error
    
    Example retry_policy:
        {"max": 2, "delay_sec": 1}
        → 3 total attempts (1 initial + 2 retries), with 1s/2s backoff
    """
    max_retries = retry_policy.get('max', 0)
    delay_sec = retry_policy.get('delay_sec', 0.5)
    
    attempts = 0
    max_attempts = max_retries + 1  # Total attempts = initial + retries
    
    while attempts < max_attempts:
        try:
            result = handler_fn()
            return result
        
        except HandlerError as e:
            attempts += 1
            
            # Non-retryable → fail immediately
            if not e.retryable:
                raise
            
            # Last attempt failed → exhausted
            if attempts >= max_attempts:
                raise RetryExhaustedError(attempts, e)
            
            # Retry: compute backoff delay
            if e.details.get('retry_after_sec'):
                # Use server-provided delay (e.g., from 429 Retry-After)
                sleep_sec = e.details['retry_after_sec']
            else:
                # Exponential backoff: delay_sec * 2^(attempt-1)
                sleep_sec = delay_sec * (2 ** (attempts - 1))
            
            # Call retry callback if provided
            if on_retry:
                on_retry(attempts, e)
            
            # Sleep before retry
            time.sleep(sleep_sec)
    
    # Unreachable (safety)
    raise RetryExhaustedError(attempts, HandlerError(
        message="Retry loop exhausted unexpectedly",
        code="RETRY_EXHAUSTED",
        category="io",
        retryable=False
    ))
