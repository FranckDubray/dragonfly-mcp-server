"""
Import 3D model operation (voxelized → blocks → compressed /fill)
"""
import logging
import time
from collections import defaultdict
from ..voxel import load_3d_model, voxelize_model, map_voxels_to_blocks
from ..utils import CommandBuilder, chunk_blocks
from ._model_import.orientation import decide_orientation, orient_coord, apply_orientation
from ._model_import.fit import fit_scale_from_bounds
from ._model_import.placement import compute_oriented_bounds, compute_anchor_mappings, build_clear_area_commands
from ._model_import.compress import rle_fill_commands

logger = logging.getLogger(__name__)

def import_3d_model_op(params: dict, rcon, context: dict) -> dict:
    model_path = params.get('model_path')
    if not model_path:
        return {"success": False, "error": "model_path required"}

    scale = float(params.get('scale', 1.0) or 1.0)
    voxel_res = float(params.get('voxel_resolution', 1.0) or 1.0)
    mapping = params.get('material_mapping', 'auto')
    orient = params.get('orient', 'auto')  # auto | y_up | z_up_to_y
    anchor = params.get('anchor', 'bottom')  # bottom | center | top
    anchor_xz = params.get('anchor_xz', 'center')  # center | min
    densify = bool(params.get('densify', False))
    clear_area = bool(params.get('clear_area', False))
    target_height = params.get('target_height')

    try:
        start_time = time.time()
        # 1) Load
        logger.info(f"Loading 3D model: {model_path}")
        try:
            mesh = load_3d_model(model_path)
        except ImportError as e:
            return {"success": False, "error": str(e), "model_path": model_path, "hint": "Install trimesh: pip install trimesh[easy]"}
        except FileNotFoundError as e:
            return {"success": False, "error": str(e), "model_path": model_path}

        # Fit-to-height (optional)
        scale, _ = fit_scale_from_bounds(mesh, orient, target_height, scale)

        # 2) Voxelize
        logger.info(f"Voxelizing model (resolution={voxel_res}, scale={scale})")
        voxel_grid = voxelize_model(mesh, resolution=voxel_res, scale=scale)
        if not voxel_grid:
            return {"success": False, "error": "Voxelization produced empty grid", "model_path": model_path}

        # 3) Map to blocks
        logger.info(f"Mapping voxels to Minecraft blocks (mode={mapping})")
        block_map = map_voxels_to_blocks(voxel_grid, mapping)

        # 4) Base position
        base_pos = None
        if params.get('position'):
            pos = params['position']
            base_pos = {'x': int(pos.get('x', 0)), 'y': int(pos.get('y', 64)), 'z': int(pos.get('z', 0))}
        elif params.get('relative_to_player', True):
            rp = context.get('resolved_position', {'x': 0, 'y': 64, 'z': 0})
            base_pos = {'x': int(rp['x']), 'y': int(rp['y']), 'z': int(rp['z'])}
        if not base_pos:
            base_pos = {'x': 0, 'y': 64, 'z': 0}

        # 5) Orientation
        use_z_up = decide_orientation(block_map, orient)
        oriented = apply_orientation(block_map, use_z_up)

        # 6) Densify (optional & single)
        if mapping == 'single' and densify:
            by_column = defaultdict(list)
            for (x, y, z) in oriented.keys():
                by_column[(x, z)].append(y)
            for (x, z), ys in by_column.items():
                y_min, y_max = min(ys), max(ys)
                blk = next((oriented[(x, y, z)] for y in ys for (xx, yy, zz) in [(x, y, z)] if (x, y, z) in oriented), 'stone')
                for y in range(y_min, y_max + 1):
                    oriented[(x, y, z)] = blk

        # 7) Anchoring & world mapping
        bounds = compute_oriented_bounds(oriented)
        y_base, y_diff, x_world, z_world, world_bounds = compute_anchor_mappings(base_pos, anchor, anchor_xz, bounds)

        # 8) Clear area if requested
        commands = []
        if clear_area:
            logger.info("Clearing world-aligned bounding box with air before build")
            commands += build_clear_area_commands(world_bounds, CommandBuilder, chunk_blocks)

        # 9) Build /fill commands per layer (bottom-up)
        by_yz = defaultdict(list)  # (wy,wz)->[(wx, block)]
        for (x, y, z), blk in oriented.items():
            wx = x_world(x)
            wy = y_base + y_diff(y)
            wz = z_world(z)
            by_yz[(wy, wz)].append((wx, blk))

        commands += rle_fill_commands(by_yz, CommandBuilder)

        # Cap & execute
        MAX_CMDS = 50000
        if len(commands) > MAX_CMDS:
            logger.warning(f"Command cap reached ({len(commands)}), truncating to {MAX_CMDS}")
            commands = commands[:MAX_CMDS]

        delay = int(params.get('delay_ms', 50) or 50)
        logger.info(f"Placing {len(commands)} /fill commands (delay={delay}ms) bottom-up")
        results = rcon.execute_batch(commands, delay_ms=delay)
        executed = sum(1 for r in results if r['success'])
        failed = len(commands) - executed
        elapsed = (time.time() - start_time) * 1000

        warnings = []
        if failed > 0:
            warnings.append(f"{failed} fill commands failed")

        return {
            "success": executed > 0,
            "model_path": model_path,
            "voxels_count": len(voxel_grid),
            "blocks_mapped": len(oriented),
            "fill_commands": len(commands),
            "executed_count": executed,
            "failed_count": failed,
            "scale": scale,
            "voxel_resolution": voxel_res,
            "mapping_mode": mapping,
            "spawn_position": base_pos,
            "orientation": ("z_up_to_y" if use_z_up else "y_up"),
            "anchor": anchor,
            "anchor_xz": anchor_xz,
            "time_ms": elapsed,
            "warnings": warnings
        }

    except Exception as e:
        logger.error(f"Import 3D model failed: {e}", exc_info=True)
        return {"success": False, "error": str(e), "error_type": type(e).__name__, "model_path": model_path}
