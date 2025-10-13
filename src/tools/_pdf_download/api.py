"""API layer for pdf_download tool - input parsing and routing with safe error handling."""
from __future__ import annotations
from typing import Dict, Any
import logging

from .core import handle_download

logger = logging.getLogger(__name__)


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to appropriate handler with global try/except.

    Args:
        operation: Operation to perform (currently: 'download')
        **params: Operation parameters

    Returns:
        Operation result (dict)
    """
    try:
        op = (operation or '').strip().lower()
        if op == "download":
            return handle_download(
                url=params.get("url"),
                filename=params.get("filename"),
                overwrite=bool(params.get("overwrite", False)),
                timeout=int(params.get("timeout", 60)),
            )
        logger.warning("pdf_download: unknown operation=%s", op)
        return {"success": False, "error": f"Unknown operation: {op}"}
    except ValueError as e:
        logger.warning("pdf_download: validation error: %s", e)
        return {"success": False, "error": f"Validation error: {str(e)}"}
    except Exception as e:
        logger.exception("pdf_download: unexpected error")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
