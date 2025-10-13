from __future__ import annotations
import json, re
from typing import Any, Dict, Optional


def extract_first_json_block(raw: Any) -> Optional[Dict[str, Any]]:
    # raw may already be a dict from call_llm tool
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    # Find first {...} JSON block heuristically
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None
