
"""
chat_agent — Conversational agent with Platform Threading API persistence.

Bootstrap file. Implementation in _chat_agent/.
"""

import json
import os
import sys
import importlib
from typing import Any, Dict

# FORCE RELOAD of implementation modules to ensure updates are applied
# (Temporary fix for development/testing without full server restart)
try:
    if 'src.tools._chat_agent.model_validator' in sys.modules:
        import src.tools._chat_agent.model_validator as mv
        importlib.reload(mv)
    if 'src.tools._chat_agent.platform_api' in sys.modules:
        import src.tools._chat_agent.platform_api as pa
        importlib.reload(pa)
    if 'src.tools._chat_agent.agent' in sys.modules:
        import src.tools._chat_agent.agent as ag
        importlib.reload(ag)
except Exception:
    pass

# We import dynamically inside run() to ensure we get the reloaded function
# from ._chat_agent import execute_chat_agent


def run(**params) -> Any:
    """Execute chat agent (MCP entry point).
    
    Args:
        **params: All parameters from spec (message, model, tools, thread_id, output_mode, etc.)
    
    Returns:
        Result dict formatted according to output_mode
    """
    try:
        # Import directly from agent module to bypass __init__ cache
        from src.tools._chat_agent.agent import execute_chat_agent
        return execute_chat_agent(**params)
    except Exception as e:
        return {
            "error": f"chat_agent failed: {e}",
            "hint": "Check AI_PORTAL_TOKEN and parameters"
        }


def spec() -> Dict[str, Any]:
    """Load spec from canonical JSON file."""
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(
        os.path.join(here, '..', 'tool_specs', 'chat_agent.json')
    )
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
