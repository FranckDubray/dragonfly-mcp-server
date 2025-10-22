"""
Placement and command generation for image rendering.
"""
from typing import Dict, Tuple, List

from ...utils import CommandBuilder
from .._model_import.compress import rle_fill_commands
from .._model_import.placement import build_clear_area_commands


def resolve_base_position(params: dict, context: dict) -> Tuple[int, int, int]:
    pos = params.get('position')
    if isinstance(pos, dict) and any(k in pos for k in ('x', 'y', 'z')):
        bx = int(round(float(pos.get('x', 0))))
        by = int(round(float(pos.get('y', 64))))
        bz = int(round(float(pos.get('z', 0))))
        return bx, by, bz
    base = context.get('resolved_position', {'x': 0, 'y': 64, 'z': 0})
    bx = int(round(float(base.get('x', 0))))
    by = int(round(float(base.get('y', 64))))
    bz = int(round(float(base.get('z', 0))))
    return bx, by, bz


def compute_world_coords(mode: str, w: int, h: int, base_x: int, base_y: int, base_z: int, anchor: str, anchor_xz: str):
    if anchor_xz == 'center':
        start_x = base_x - (w // 2)
    else:
        start_x = base_x

    if mode == 'wall':
        if anchor == 'bottom':
            min_y = base_y
        elif anchor == 'top':
            min_y = base_y - (h - 1)
        else:
            min_y = base_y - (h // 2)
        start_y = min_y
        fixed_z = base_z
        return start_x, start_y, fixed_z, None
    else:
        start_y = base_y
        if anchor_xz == 'center':
            start_z = base_z - (h // 2)
        else:
            start_z = base_z
        return start_x, start_y, None, start_z


def blocks_to_commands(by_yz: Dict[Tuple[int, int], List[Tuple[int, str]]], clear_area: bool, mode: str,
                       start_x: int, start_y: int, w: int, h: int, base_z: int, fixed_z: int | None, start_z: int | None) -> List[str]:
    commands: List[str] = []
    if clear_area:
        if mode == 'wall':
            min_x = start_x
            max_x = start_x + w - 1
            min_y = start_y
            max_y = start_y + h - 1
            min_z = max_z = fixed_z if fixed_z is not None else base_z
        else:
            min_x = start_x
            max_x = start_x + w - 1
            min_z = start_z if start_z is not None else base_z
            max_z = (start_z if start_z is not None else base_z) + h - 1
            min_y = max_y = start_y
        world_bounds = (min_x, max_x, min_z, max_z, min_y, max_y)
        commands += build_clear_area_commands(world_bounds, CommandBuilder, lambda a, b: [(a, b)])

    commands += rle_fill_commands(by_yz, CommandBuilder)
    return commands
