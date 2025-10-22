"""
Palette selection and quantization helpers for image rendering.
"""
from typing import Dict, Tuple, List

from ...utils.palette import get_palette, distance_rgb2

Palette = Dict[str, Tuple[int, int, int]]


ALLOWED_MODES = {"wool", "concrete", "both"}

def select_palette(params: dict) -> Tuple[Palette, str]:
    """Return (palette_dict, mode_name).
    Priority:
      1) params.palette if provided and valid
      2) if 'wool_only' present: True->'wool', False->'both'
      3) default 'both'
    """
    mode = params.get('palette')
    if isinstance(mode, str):
        mode = mode.lower()
    if mode not in ALLOWED_MODES:
        if 'wool_only' in params:
            mode = 'wool' if bool(params.get('wool_only')) else 'both'
        else:
            mode = 'both'
    return get_palette(mode), mode


def choose_block_fast(rgb: Tuple[int, int, int], palette: Palette) -> str:
    best = None
    best_d = 10**12
    for blk, brgb in palette.items():
        d = distance_rgb2(rgb, brgb)
        if d < best_d:
            best_d = d
            best = blk
    return best or 'stone'


def quantize_image(im, palette: Palette, params: dict) -> List[List[str]]:
    """Return block names per pixel (rows) based on params.distance and params.dither.
    Falls back to fast RGB nearest if advanced path not available.
    """
    image_mapping = params.get('image_mapping', 'color')
    if image_mapping == 'single':
        w, h = im.size
        blk = params.get('block_type', 'white_wool')
        return [[blk for _ in range(w)] for _ in range(h)]

    distance = (params.get('distance') or 'rgb').lower()
    dither = bool(params.get('dither', False))

    use_advanced = dither or (distance == 'lab')
    if not use_advanced:
        # Fast path: per-pixel nearest in RGB
        px = im.load()
        w, h = im.size
        out: List[List[str]] = []
        for y in range(h):
            row: List[str] = []
            for x in range(w):
                row.append(choose_block_fast(px[x, y], palette))
            out.append(row)
        return out

    # Advanced path
    try:
        import numpy as np
        from ...utils.dither import quantize_blocks
    except Exception:
        # Fallback if numpy not available
        px = im.load()
        w, h = im.size
        out: List[List[str]] = []
        for y in range(h):
            row: List[str] = []
            for x in range(w):
                row.append(choose_block_fast(px[x, y], palette))
            out.append(row)
        return out

    im_np = np.array(im, dtype=np.uint8)
    return quantize_blocks(im_np, palette, distance=distance, dither=dither)
