# Mock transform for testing: simulates score that improves with retries

from .base import AbstractHandler

class MockScoreProgressiveHandler(AbstractHandler):
    """
    Mock handler that returns a score that improves with each retry.
    Used for testing retry loops.
    
    Formula: score = base + (retry_count * increment)
    Default: score = 4 + (retry_count * 1.5)
    
    Examples:
        retry_count=0 → score=4.0
        retry_count=1 → score=5.5
        retry_count=2 → score=7.0 ✅ (passes >= 7 threshold)
    """
    
    @property
    def kind(self) -> str:
        return "mock_score_progressive"
    
    def run(self, retry_count=0, base=4.0, increment=1.5, **kwargs) -> dict:
        """
        Args:
            retry_count: Current retry attempt (default: 0)
            base: Base score (default: 4.0)
            increment: Score increase per retry (default: 1.5)
        
        Returns:
            {"score": float, "retry_count": int, "message": str}
        """
        score = float(base) + (float(retry_count) * float(increment))
        
        return {
            "score": score,
            "retry_count": retry_count,
            "message": f"Attempt {retry_count + 1}: score={score:.1f}"
        }
