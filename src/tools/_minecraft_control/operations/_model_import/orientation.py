"""
Orientation helpers for voxelized models.
"""
from typing import Dict, Tuple

def decide_orientation(block_map: Dict[Tuple[int,int,int], str], orient: str) -> bool:
    """Return True if we should map z-up to y-up (use_z_up), else False.
    orient: 'auto' | 'y_up' | 'z_up_to_y'
    """
    if orient == 'z_up_to_y':
        return True
    if orient == 'y_up':
        return False
    # auto: infer from spans (z >> y → likely z-up)
    try:
        import numpy as _np
        if not block_map:
            return False
        vs = _np.array(list(block_map.keys()), dtype=_np.int32)
        vy_span = int(vs[:, 1].max()) - int(vs[:, 1].min()) if vs.size else 0
        vz_span = int(vs[:, 2].max()) - int(vs[:, 2].min()) if vs.size else 0
        return vz_span > (vy_span * 1.25)
    except Exception:
        return False

def orient_coord(vx: int, vy: int, vz: int, use_z_up: bool) -> Tuple[int,int,int]:
    """Map z-up indices to y-up if needed."""
    return (int(vx), int(vz), int(vy)) if use_z_up else (int(vx), int(vy), int(vz))

def apply_orientation(block_map: Dict[Tuple[int,int,int], str], use_z_up: bool) -> Dict[Tuple[int,int,int], str]:
    """Return new dict with oriented voxel coordinates."""
    oriented: Dict[Tuple[int,int,int], str] = {}
    for (vx, vy, vz), blk in block_map.items():
        ox, oy, oz = orient_coord(vx, vy, vz, use_z_up)
        oriented[(ox, oy, oz)] = blk
    return oriented
