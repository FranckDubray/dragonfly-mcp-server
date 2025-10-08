"""
Thin facade for the 'discord_webhook' tool.
- spec() delegates to _discord_webhook.spec_def.tool_spec
- run(**params) delegates to _discord_webhook.ops_handlers.run_operation
"""
from __future__ import annotations
from typing import Any, Dict

try:
    from ._discord_webhook.spec_def import tool_spec  # type: ignore
    from ._discord_webhook.ops_handlers import run_operation  # type: ignore
except Exception:
    from src.tools._discord_webhook.spec_def import tool_spec  # type: ignore
    from src.tools._discord_webhook.ops_handlers import run_operation  # type: ignore


def run(**params) -> Any:
    return run_operation(**params)


def spec() -> Dict[str, Any]:
    return tool_spec()
