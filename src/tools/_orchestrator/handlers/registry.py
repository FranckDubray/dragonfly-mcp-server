# Handler registry (kind → handler instance)

from typing import Dict
from .base import AbstractHandler

class HandlerRegistry:
    """Registry mapping handler kinds to instances"""
    
    def __init__(self):
        self._handlers: Dict[str, AbstractHandler] = {}
    
    def register(self, handler: AbstractHandler) -> None:
        """Register a handler (raises if duplicate kind)"""
        if handler.kind in self._handlers:
            raise ValueError(f"Handler kind '{handler.kind}' already registered")
        self._handlers[handler.kind] = handler
    
    def get(self, kind: str) -> AbstractHandler:
        """Get handler by kind (raises KeyError if not found)"""
        if kind not in self._handlers:
            raise KeyError(f"Unknown handler kind: {kind}")
        return self._handlers[kind]
    
    def has(self, kind: str) -> bool:
        """Check if handler kind is registered"""
        return kind in self._handlers
    
    def list_kinds(self) -> list:
        """List all registered handler kinds"""
        return list(self._handlers.keys())

# Global registry instance
_registry = HandlerRegistry()

def get_registry() -> HandlerRegistry:
    """Get the global handler registry"""
    return _registry
