"""
Constants and lightweight accessors for astronomy tool
- Loads large static datasets (planet data, stars) from JSON files on demand
- Keeps Python files <7KB as per project policy
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

# Small, safe list kept inline
MOON_PHASES = [
    "New Moon",
    "Waxing Crescent",
    "First Quarter",
    "Waxing Gibbous",
    "Full Moon",
    "Waning Gibbous",
    "Last Quarter",
    "Waning Crescent",
]


def _data_dir() -> str:
    here = os.path.dirname(__file__)
    return os.path.join(here, "data")


@lru_cache(maxsize=1)
def get_planet_data() -> dict:
    """Load planet data JSON once (cached)."""
    path = os.path.join(_data_dir(), "planet_data.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_stars_catalog() -> dict:
    """Load stars catalog JSON once (cached)."""
    path = os.path.join(_data_dir(), "stars_catalog.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_star_entry(name: str) -> dict | None:
    """Get a star entry by lowercase key from catalog."""
    catalog = get_stars_catalog().get("bright_stars", {})
    return catalog.get(name.lower().strip())
