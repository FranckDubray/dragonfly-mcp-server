from __future__ import annotations
from typing import Any, Dict

try:
    from .operations import run_operation  # type: ignore
except Exception:
    from src.tools._discord_webhook.operations import run_operation  # type: ignore
