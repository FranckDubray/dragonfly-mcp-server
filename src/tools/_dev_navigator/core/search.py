from typing import Any, Dict

def run(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "operation": "search",
        "data": [],
        "returned_count": 0,
        "total_count": 0,
        "truncated": False,
        "stats": {}
    }
