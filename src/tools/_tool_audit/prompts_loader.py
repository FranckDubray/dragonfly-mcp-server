from __future__ import annotations
import os
from typing import Tuple

BASE_DIR = os.path.dirname(__file__)
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")


def load_system_and_cdc(profile: str) -> Tuple[str, str]:
    system_path = os.path.join(PROMPTS_DIR, "system", "audit_system.md")
    if profile == "fuser":
        system_path = os.path.join(PROMPTS_DIR, "system", "fuser_system.md")
    with open(system_path, "r", encoding="utf-8") as f:
        system = f.read()

    cdc_file = {
        "perf": "perf.md",
        "quality": "quality.md",
        "maintain": "maintain.md",
        "invariants": "invariants.md",
        "combined": "combined.md",
        "fuser": "fuse.md",
    }.get(profile, "quality.md")
    cdc_path = os.path.join(PROMPTS_DIR, "cdc", cdc_file)
    with open(cdc_path, "r", encoding="utf-8") as f:
        cdc = f.read()
    return system, cdc
