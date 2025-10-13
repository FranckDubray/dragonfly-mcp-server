"""API routing for office_to_pdf operations (minimal outputs, logging)."""
from typing import Dict, Any
import logging
from .core import handle_convert, handle_get_info

LOG = logging.getLogger(__name__)


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to appropriate handler.

    Raises exceptions on error (no verbose metadata here).
    """
    try:
        op = (operation or '').strip().lower()
        if op == 'convert':
            return handle_convert(**params)
        if op == 'get_info':
            return handle_get_info(**params)
        raise ValueError(f"Unknown operation '{operation}'. Valid operations: convert, get_info")
    except Exception as e:
        LOG.error(f"office_to_pdf operation failed: {e}")
        raise
