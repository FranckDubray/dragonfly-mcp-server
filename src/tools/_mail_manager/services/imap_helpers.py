from importlib import import_module

FALLBACK_SPAM_NAMES = [
    'Spam', 'Junk', 'Junk Mail', 'Courrier indésirable'
]


def resolve_spam_folder(profile: str) -> str | None:
    """Use the IMAP tool to discover the spam folder once per mailbox.
    Strategy: prefer SPECIAL-USE flag \Junk if available, else fallback names.
    Returns the IMAP folder name or None if not found.
    """
    imap_tool = import_module('src.tools.imap')

    # Try a list_folders op if available in the tool (with flags data)
    try:
        res = imap_tool.run(operation='list_folders', profile=profile, limit=500)
        items = res.get('items') or []
        # Prefer SPECIAL-USE Junk
        for it in items:
            flags = {f.lower() for f in (it.get('flags') or [])}
            if '\\junk' in flags:  # RFC 6154 special-use
                return it.get('name') or it.get('path')
        # Fallback common names
        names = { (it.get('name') or it.get('path') or '').strip() for it in items }
        for candidate in FALLBACK_SPAM_NAMES:
            if candidate in names:
                return candidate
    except Exception:
        pass

    # Last-resort heuristic for Gmail
    try:
        # Gmail typical
        return '[Gmail]/Spam'
    except Exception:
        return None
