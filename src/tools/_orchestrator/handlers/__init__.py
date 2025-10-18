# Handlers package: registry, base, implementations

from .base import AbstractHandler, HandlerError
from .registry import HandlerRegistry, get_registry
from .http_tool import HttpToolHandler
from .sleep import SleepHandler
from .transforms import (
    IncrementHandler,
    DecrementHandler,
    AddHandler,
    MultiplyHandler,
    SetValueHandler
)
from .transforms_domain import (
    SanitizeTextHandler,
    NormalizeLLMOutputHandler,
    JsonStringifyHandler,
    ExtractFieldHandler,
    FormatTemplateHandler,
    IdempotencyGuardHandler
)
from .mock_score import MockScoreProgressiveHandler

__all__ = [
    'AbstractHandler',
    'HandlerError',
    'HandlerRegistry',
    'get_registry',
    'HttpToolHandler',
    'SleepHandler',
    'IncrementHandler',
    'DecrementHandler',
    'AddHandler',
    'MultiplyHandler',
    'SetValueHandler',
    'SanitizeTextHandler',
    'NormalizeLLMOutputHandler',
    'JsonStringifyHandler',
    'ExtractFieldHandler',
    'FormatTemplateHandler',
    'IdempotencyGuardHandler',
    'MockScoreProgressiveHandler',
]

def bootstrap_handlers(cancel_flag_fn=None):
    """
    Register default handlers.
    
    Args:
        cancel_flag_fn: Callable for sleep handler cancel check
    """
    registry = get_registry()
    
    # Register http_tool handler (generic MCP client)
    if not registry.has('http_tool'):
        registry.register(HttpToolHandler())
    
    # Register sleep handler (if cancel_flag_fn provided)
    if cancel_flag_fn and not registry.has('sleep'):
        registry.register(SleepHandler(cancel_flag_fn))
    
    # Register transform handlers
    transforms = [
        IncrementHandler(),
        DecrementHandler(),
        AddHandler(),
        MultiplyHandler(),
        SetValueHandler(),
        MockScoreProgressiveHandler()
    ]
    for transform in transforms:
        if not registry.has(transform.kind):
            registry.register(transform)
    
    # Register domain transforms
    domain_transforms = [
        SanitizeTextHandler(),
        NormalizeLLMOutputHandler(),
        JsonStringifyHandler(),
        ExtractFieldHandler(),
        FormatTemplateHandler(),
        IdempotencyGuardHandler()
    ]
    for transform in domain_transforms:
        if not registry.has(transform.kind):
            registry.register(transform)
