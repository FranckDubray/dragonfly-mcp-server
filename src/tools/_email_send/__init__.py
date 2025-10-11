"""Email SMTP send tool package."""

import json
from pathlib import Path


def spec():
    """Load and return the canonical JSON spec for email_send tool.
    
    Returns:
        Dict with OpenAI function calling spec
    """
    spec_path = Path(__file__).parent.parent.parent / "tool_specs" / "email_send.json"
    
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")
    
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)


__all__ = ["spec"]
