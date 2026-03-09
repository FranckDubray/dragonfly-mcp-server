"""Portal Custom Model Manager package."""
from __future__ import annotations
from typing import Dict, Any
import json
from pathlib import Path


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec."""
    spec_path = (
        Path(__file__).parent.parent.parent / "tool_specs" / "portal_model_custom.json"
    )
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)


__all__ = ["spec"]
