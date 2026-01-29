"""
Cost calculation and breakdown for LLM Agent.
"""
from typing import Dict, Any, List, Optional


class CostCalculator:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.iterations: List[Dict[str, Any]] = []
        self._cumulative: Dict[str, Any] = {}
    
    def add_iteration(self, iteration: int, usage: Optional[Dict[str, Any]]):
        if not self.enabled or not usage:
            return
        
        self.iterations.append({"iteration": iteration, "usage": usage})
        
        # Merge cumulatif (sum numeric fields)
        for k, v in usage.items():
            if isinstance(v, (int, float)) and "price" not in k.lower():
                self._cumulative[k] = self._cumulative.get(k, 0) + v
            elif k not in self._cumulative:
                self._cumulative[k] = v
    
    def cumulative_usage(self) -> Dict[str, Any]:
        return self._cumulative
    
    def breakdown(self) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        return {
            "total_iterations": len(self.iterations),
            "cumulative": self._cumulative,
            "per_iteration": self.iterations,
        }
