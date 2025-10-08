"""
IMAP provider presets (Gmail, Outlook, Yahoo, iCloud, Infomaniak, custom)
"""
from __future__ import annotations
from typing import Dict, Any

IMAP_PRESETS: Dict[str, Dict[str, Any]] = {
    "gmail": {
        "server": "imap.gmail.com",
        "port": 993,
        "ssl": True,
        "special_folders": {
            "inbox": "INBOX",
            "sent": "[Gmail]/Sent Mail",
            "trash": "[Gmail]/Trash",
            "spam": "[Gmail]/Spam",
            "all": "[Gmail]/All Mail",
            "drafts": "[Gmail]/Drafts",
            "important": "[Gmail]/Important",
            "starred": "[Gmail]/Starred"
        },
        "notes": "App Password required if 2FA enabled. Enable IMAP: Settings → Forwarding/IMAP → Enable IMAP"
    },
    "outlook": {
        "server": "outlook.office365.com",
        "port": 993,
        "ssl": True,
        "special_folders": {
            "inbox": "INBOX",
            "sent": "Sent",
            "trash": "Deleted",
            "spam": "Junk",
            "drafts": "Drafts"
        },
        "notes": "Works with Hotmail, Live.com, Office365. Password or App Password."
    },
    "yahoo": {
        "server": "imap.mail.yahoo.com",
        "port": 993,
        "ssl": True,
        "special_folders": {
            "inbox": "INBOX",
            "sent": "Sent",
            "trash": "Trash",
            "spam": "Bulk Mail",
            "drafts": "Draft"
        },
        "notes": "App Password mandatory. Generate at: Account Security → Generate app password"
    },
    "icloud": {
        "server": "imap.mail.me.com",
        "port": 993,
        "ssl": True,
        "special_folders": {
            "inbox": "INBOX",
            "sent": "Sent Messages",
            "trash": "Deleted Messages",
            "spam": "Junk",
            "drafts": "Drafts"
        },
        "notes": "App-specific password required. Generate at: Apple ID → Security → App-Specific Passwords"
    },
    "infomaniak": {
        "server": "mail.infomaniak.com",
        "port": 993,
        "ssl": True,
        "special_folders": {
            "inbox": "INBOX",
            "sent": "Sent",
            "trash": "Trash",
            "spam": "Junk",
            "drafts": "Drafts"
        },
        "notes": "Swiss cloud provider. Use your full email address and password (or App Password if available)."
    },
    "custom": {
        "server": None,  # User must provide
        "port": 993,
        "ssl": True,
        "special_folders": {
            "inbox": "INBOX",
            "sent": "Sent",
            "trash": "Trash",
            "spam": "Junk",
            "drafts": "Drafts"
        },
        "notes": "Provide imap_server, imap_port, use_ssl manually"
    }
}


def get_preset(provider: str) -> Dict[str, Any]:
    """Get preset config for a provider"""
    provider = (provider or "").lower()
    if provider not in IMAP_PRESETS:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(IMAP_PRESETS.keys())}")
    return IMAP_PRESETS[provider].copy()


def normalize_folder_name(provider: str, folder_alias: str) -> str:
    """
    Normalize folder alias (inbox, sent, trash...) to provider-specific name.
    If not an alias, return as-is (preserve case for exact folder names).
    """
    if not folder_alias:
        return "INBOX"
    
    preset = get_preset(provider)
    folder_lower = folder_alias.lower()
    special = preset.get("special_folders", {})
    
    # If it's a known alias, return the mapped folder name
    if folder_lower in special:
        return special[folder_lower]
    
    # Otherwise, return as-is (preserve case for exact folder names like "[Gmail]/Spam")
    return folder_alias
