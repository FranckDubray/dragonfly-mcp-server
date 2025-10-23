"""
Fallback helpers for list_entities: short per-field queries and small utilities.
Kept <7KB for maintainability.
"""
from typing import List
import logging

from .fields import fallback_fill_fields_counted

logger = logging.getLogger(__name__)

__all__ = [
    'split_lines',
    'extract_value_from_line',
    'fallback_fetch_entities',
]


def split_lines(raw: str) -> List[str]:
    """Normalize server output to a clean list of non-empty lines."""
    return [ln.strip() for ln in (raw or '').replace('\r\n', '\n').split('\n') if ln.strip()]


def extract_value_from_line(line: str) -> str:
    """Extract the value part from a typical Paper/Bukkit output line like:
    "<name> has the following entity data: <VALUE>"
    If the phrase is absent, fall back to the substring after the last ':'.
    """
    if not line:
        return ''
    low = line.lower()
    key = 'entity data:'
    idx = low.rfind(key)
    if idx != -1:
        return line[idx + len(key):].strip()
    j = line.rfind(':')
    return line[j + 1:].strip() if j != -1 else line.strip()


def fallback_fetch_entities(rcon, selector: str, pos_ref: str, requested_fields: List[str]) -> List[dict]:
    """Use the counted per-field fallback that aligns lines by index and decodes values per-path.
    This is robust against SNBT truncation in full dumps.
    """
    try:
        return fallback_fill_fields_counted(rcon, selector, requested_fields, pos_ref)
    except Exception as e:
        logger.error(f"fallback_fetch_entities failed: {e}", exc_info=True)
        return []
