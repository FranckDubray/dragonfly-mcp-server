from typing import Any, Dict

from ..services.errors import make_error


def run(p: Dict[str, Any]) -> Dict[str, Any]:
    # Skeleton: return empty sections with pagination hints.
    sections = {}
    for name in ("overview", "tree", "endpoints", "tests"):
        sections[name] = {
            "returned_count": 0,
            "total_count": 0,
            "truncated": False,
            "data": []
        }
    return {
        "operation": "compose",
        "sections": sections,
        "returned_count": 0,
        "total_count": 0,
        "truncated": False,
        "stats": {}
    }
