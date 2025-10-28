
"""API routing for office_to_pdf operations (minimal outputs, logging)."""
from typing import Dict, Any
import logging
from .core import handle_convert, handle_get_info

LOG = logging.getLogger(__name__)


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to appropriate handler.

    Returns dict with either result or {"error": "..."}.
    """
    op = (operation or '').strip().lower()
    try:
        if op == 'convert':
            return handle_convert(**params)
        if op == 'get_info':
            return handle_get_info(**params)
        return {"error": f"Unknown operation '{operation}'. Valid operations: convert, get_info"}
    except Exception as e:  # pragma: no cover - minimal surface
        LOG.error(f"office_to_pdf operation failed: {e}")
        # Minimal error, no verbose metadata
        return {"error": f"Unexpected error: {str(e)}"}

 