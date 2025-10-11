"""
Thin facade for the 'discord_webhook' tool.
- spec() loads canonical JSON spec (source of truth)
- run(**params) delegates to _discord_webhook.ops_handlers.run_operation
"""
from __future__ import annotations
from typing import Any, Dict
import os, json

try:
    from ._discord_webhook.ops_handlers import run_operation  # type: ignore
except Exception:
    from src.tools._discord_webhook.ops_handlers import run_operation  # type: ignore


def run(**params) -> Any:
    return run_operation(**params)


def spec() -> Dict[str, Any]:
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'discord_webhook.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
