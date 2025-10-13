from typing import Any, Dict

def run(p: Dict[str, Any]) -> Dict[str, Any]:
    # Compact summary only; no heavy lists to respect 20KB policy
    return {
        "operation": "overview",
        "data": {
            "languages": [],
            "key_files": [],
            "endpoints_summary": {},
            "tests_summary": {},
            "representative_outlines": []
        },
        "returned_count": 0,
        "total_count": 0,
        "truncated": False,
        "stats": {}
    }
