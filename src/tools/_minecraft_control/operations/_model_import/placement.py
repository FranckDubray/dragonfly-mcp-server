"""
Placement & anchoring helpers for voxel import.
"""
from typing import Dict, Tuple, Callable

Bounds = Tuple[int, int, int, int, int, int]  # (min_x, min_y, min_z, max_x, max_y, max_z)


def compute_oriented_bounds(oriented: Dict[Tuple[int, int, int], str]) -> Bounds:
    """Compute integer bounds of oriented voxel keys."""
    min_x = min_y = min_z = 10 ** 9
    max_x = max_y = max_z = -10 ** 9
    for (x, y, z) in oriented.keys():
        if x < min_x: min_x = x
        if y < min_y: min_y = y
        if z < min_z: min_z = z
        if x > max_x: max_x = x
        if y > max_y: max_y = y
        if z > max_z: max_z = z
    return (min_x, min_y, min_z, max_x, max_y, max_z)


def compute_anchor_mappings(
    base_pos: Dict[str, int],
    anchor: str,
    anchor_xz: str,
    bounds: Bounds
) -> Tuple[int, Callable[[int], int], Callable[[int], int], Callable[[int], int], Tuple[int, int, int, int, int, int]]:
    """Return mappings for world placement.

    Returns:
      y_base, y_diff(oy)->int, x_world(ox)->int, z_world(oz)->int, world_bounds (minx,maxx,minz,maxz,miny,maxy)
    """
    min_x, min_y, min_z, max_x, max_y, max_z = bounds

    # Y anchor
    if anchor == 'bottom':
        y_base = base_pos['y']
        def y_diff(oy: int) -> int: return (oy - min_y)
    elif anchor == 'top':
        y_base = base_pos['y']
        def y_diff(oy: int) -> int: return (oy - max_y)
    else:  # center
        cy = int((min_y + max_y) / 2)
        y_base = base_pos['y']
        def y_diff(oy: int) -> int: return (oy - cy)

    # XZ anchor (100% integer, no rounding; bias-left for even sizes)
    width = (max_x - min_x + 1)
    depth = (max_z - min_z + 1)

    if anchor_xz == 'center':
        start_x = base_pos['x'] - (width // 2)
        start_z = base_pos['z'] - (depth // 2)
        def x_world(ox: int) -> int: return start_x + (ox - min_x)
        def z_world(oz: int) -> int: return start_z + (oz - min_z)
    else:  # min
        def x_world(ox: int) -> int: return base_pos['x'] + (ox - min_x)
        def z_world(oz: int) -> int: return base_pos['z'] + (oz - min_z)

    world_min_x = min(x_world(min_x), x_world(max_x))
    world_max_x = max(x_world(min_x), x_world(max_x))
    world_min_z = min(z_world(min_z), z_world(max_z))
    world_max_z = max(z_world(min_z), z_world(max_z))
    world_min_y = y_base + y_diff(min_y)
    world_max_y = y_base + y_diff(max_y)

    return y_base, y_diff, x_world, z_world, (world_min_x, world_max_x, world_min_z, world_max_z, world_min_y, world_max_y)


def build_clear_area_commands(
    world_bounds: Tuple[int, int, int, int, int, int],
    CommandBuilder,
    chunk_blocks
) -> list:
    """Build /fill air commands chunked to clear world-aligned bounding box."""
    (min_x, max_x, min_z, max_z, min_y, max_y) = world_bounds
    start_bb = {"x": min_x, "y": min_y, "z": min_z}
    end_bb   = {"x": max_x, "y": max_y, "z": max_z}
    commands = []
    for c_start, c_end in chunk_blocks(start_bb, end_bb):
        commands.append(CommandBuilder.fill(c_start['x'], c_start['y'], c_start['z'], c_end['x'], c_end['y'], c_end['z'], 'air'))
    return commands
