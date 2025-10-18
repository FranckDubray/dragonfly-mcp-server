# Abstract handler interface

from typing import Dict, Any
from abc import ABC, abstractmethod

class HandlerError(Exception):
    """Normalized handler error"""
    def __init__(self, message: str, code: str, category: str, retryable: bool, details: Dict = None):
        super().__init__(message)
        self.message = message[:400]  # Truncate to 400 chars
        self.code = code
        self.category = category  # "io" | "validation" | "permission" | "timeout"
        self.retryable = retryable
        self.details = details or {}

class AbstractHandler(ABC):
    """Base class for all handlers (io and transform)"""
    
    @property
    @abstractmethod
    def kind(self) -> str:
        """Handler kind (e.g., 'http_tool', 'sanitize_text')"""
        pass
    
    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute handler logic.
        
        Args:
            **kwargs: Resolved inputs (flat dict)
        
        Returns:
            Outputs dict (flat)
        
        Raises:
            HandlerError: On failure (with retryable flag)
        """
        pass
