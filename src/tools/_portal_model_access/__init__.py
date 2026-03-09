"""Portal Model Access — Manage model visibility per tenant/company."""
from __future__ import annotations
import json
import os


def spec():
    """Load canonical JSON spec."""
    here = os.path.dirname(__file__)
    path = os.path.abspath(
        os.path.join(here, "..", "..", "tool_specs", "portal_model_access.json")
    )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
