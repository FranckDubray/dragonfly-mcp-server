





















# Crash logger: logs complete context snapshots on errors
# Critical for debugging production issues

import sqlite3
import json
import traceback
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Use centralized time and sanitation
from ..utils import utcnow_str
from ..engine.debug_utils import sanitize_details_for_log

def _sanitize_context(ctx: Dict[str, Any], max_size: int = 100000) -> str:
    """
    Sanitize and serialize context (mask PII, limit size).
    """
    try:
        clean = sanitize_details_for_log(ctx, max_bytes=max_size)
        json_str = json.dumps(clean, separators=(',', ':'), ensure_ascii=False, default=str)
        if len(json_str) > max_size:
            return json_str[:max_size] + f"\n... (truncated, original size: {len(json_str)} bytes)"
        return json_str
    except Exception as e:
        return json.dumps({"error": f"Failed to serialize context: {str(e)[:200]}"})

# ... rest unchanged ...
