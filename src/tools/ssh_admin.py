"""
Bootstrap for ssh_admin tool.
- spec() loads canonical JSON spec (source of truth)
- run(**params) delegates to _ssh_admin.operations
"""
from __future__ import annotations
from typing import Any, Dict
import os
import json

def run(**params) -> Any:
    try:
        from ._ssh_admin.operations import run_operation
    except Exception:
        from src.tools._ssh_admin.operations import run_operation
    return run_operation(**params)

def spec() -> Dict[str, Any]:
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'ssh_admin.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
