"""
Palette management for image rendering: selectable sets and distance metrics.
"""
from typing import Dict, Tuple
import math

from ..voxel.block_mapper import BLOCK_COLOR_PALETTE as BASE_PALETTE

Palette = Dict[str, Tuple[int, int, int]]


def get_palette(mode: str = "both") -> Palette:
    """Return a palette by mode: 'wool' | 'concrete' | 'both'.
    Defaults to 'both' (wool + concrete + neutrals).
    """
    mode = (mode or "both").lower()
    if mode == "wool":
        return {k: v for k, v in BASE_PALETTE.items() if k.endswith("_wool")}
    if mode == "concrete":
        return {k: v for k, v in BASE_PALETTE.items() if k.endswith("_concrete")}
    return dict(BASE_PALETTE)


def distance_rgb(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    ar, ag, ab = a
    br, bg, bb = b
    return math.sqrt((ar - br) ** 2 + (ag - bg) ** 2 + (ab - bb) ** 2)

# Fast integer variant (squared distance), better for speed

def distance_rgb2(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> int:
    ar, ag, ab = a
    br, bg, bb = b
    dr = ar - br
    dg = ag - bg
    db = ab - bb
    return dr * dr + dg * dg + db * db

# Placeholder for future CIEDE2000 metric

def distance_ciede2000(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    # TODO: implement real CIEDE2000 if needed
    return distance_rgb(a, b)
