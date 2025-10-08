"""
IMAP utilities: query building, error handling, normalization
"""
from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime


def build_imap_search_query(query: Dict[str, Any]) -> str:
    """
    Build IMAP search criteria string from structured query.
    
    Examples:
    - {"from": "alice@example.com"} → 'FROM "alice@example.com"'
    - {"unseen": True, "since": "2025-10-01"} → 'UNSEEN SINCE 01-Oct-2025'
    """
    if not query:
        return "ALL"
    
    parts = []
    
    # Text criteria
    if "from" in query:
        parts.append(f'FROM "{query["from"]}"')
    if "to" in query:
        parts.append(f'TO "{query["to"]}"')
    if "subject" in query:
        parts.append(f'SUBJECT "{query["subject"]}"')
    if "text" in query:
        parts.append(f'TEXT "{query["text"]}"')
    
    # Date criteria (IMAP format: DD-MMM-YYYY)
    if "since" in query:
        date_str = format_imap_date(query["since"])
        parts.append(f'SINCE {date_str}')
    if "before" in query:
        date_str = format_imap_date(query["before"])
        parts.append(f'BEFORE {date_str}')
    
    # Flag criteria
    if query.get("unseen"):
        parts.append("UNSEEN")
    if query.get("seen"):
        parts.append("SEEN")
    if query.get("flagged"):
        parts.append("FLAGGED")
    
    return " ".join(parts) if parts else "ALL"


def format_imap_date(date_input: str) -> str:
    """
    Convert date string (YYYY-MM-DD) to IMAP format (DD-MMM-YYYY).
    Example: "2025-10-08" → "08-Oct-2025"
    """
    try:
        dt = datetime.strptime(date_input, "%Y-%m-%d")
        return dt.strftime("%d-%b-%Y")
    except Exception:
        # Fallback: try parsing as-is
        return date_input


def parse_message_ids(data: bytes) -> List[str]:
    """Parse IMAP search response to extract message UIDs"""
    if not data or data == b'':
        return []
    # data is like b'1 2 3 4' or b''
    ids = data.decode('utf-8').strip().split()
    return ids


def normalize_email_address(addr: str) -> str:
    """Extract clean email from 'Name <email>' format"""
    if '<' in addr and '>' in addr:
        start = addr.index('<') + 1
        end = addr.index('>')
        return addr[start:end].strip()
    return addr.strip()


def safe_decode(data: bytes | str, encoding: str = 'utf-8') -> str:
    """Safely decode bytes to string with fallback"""
    if isinstance(data, str):
        return data
    try:
        return data.decode(encoding)
    except UnicodeDecodeError:
        return data.decode('utf-8', errors='replace')
    except Exception:
        return str(data)


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text with ellipsis if too long"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "..."
