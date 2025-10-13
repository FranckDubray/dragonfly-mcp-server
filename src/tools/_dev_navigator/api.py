"""
Dev Navigator API (no side-effects at import)
- Pagination-first, hard payload cap enforced in core
- Offline deterministic by default; release index read-only when available
"""
from typing import Any, Dict

from .validators.envelope import validate_envelope
from .core.router import route_operation


def execute(**params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        clean = validate_envelope(params)
        result = route_operation(clean)
        return result
    except Exception as e:  # Final safeguard; core and validators should raise controlled errors
        # Minimal error envelope to respect outputs compactness
        return {
            "operation": params.get("operation", "unknown"),
            "errors": [{
                "code": "internal_error",
                "message": str(e),
                "scope": "tool",
                "recoverable": False
            }],
            "returned_count": 0,
            "total_count": 0,
            "truncated": False
        }
