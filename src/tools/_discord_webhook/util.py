from __future__ import annotations
import hashlib
import os
import re
from typing import Tuple

API_BASE = "https://discord.com/api/v10"

def get_discord_webhook_url() -> str:
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        raise ValueError("DISCORD_WEBHOOK_URL missing")
    return url.strip()

def parse_webhook(url: str) -> Tuple[str, str]:
    m = re.search(r"webhooks/(\d+)/(\S+)", url)
    if not m:
        raise ValueError("Invalid Discord webhook URL")
    webhook_id, token = m.group(1), m.group(2)
    return webhook_id, token

def webhook_hash(webhook_id: str, token: str) -> str:
    return hashlib.sha256(f"{webhook_id}:{token}".encode("utf-8")).hexdigest()
