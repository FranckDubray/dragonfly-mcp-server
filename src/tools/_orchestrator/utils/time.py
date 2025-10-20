# Time utilities - Single source of truth for timestamp formatting

from datetime import datetime, timezone

def utcnow_str() -> str:
    """
    Return current UTC time as ISO8601 string with microseconds.
    
    Format: 'YYYY-MM-DD HH:MM:SS.mmmmmm'
    Example: '2025-10-20 13:45:23.123456'
    
    This is the canonical timestamp format used throughout the orchestrator.
    """
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
