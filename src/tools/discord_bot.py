"""
Bootstrap for discord_bot tool.
Delegates to _discord_bot.operations module.
"""
from typing import Any, Dict
import os
import json

def run(**params) -> Any:
    try:
        from ._discord_bot.operations import run_operation
    except Exception:
        from src.tools._discord_bot.operations import run_operation
    return run_operation(**params)

def spec() -> Dict[str, Any]:
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'discord_bot.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
