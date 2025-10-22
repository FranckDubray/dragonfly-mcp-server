"""
API for render_image operation (split version, <7KB files)
"""
import logging
import os
import time
from typing import Dict, Tuple, List

from .paths import get_images_base_dir, normalize_image_path, resolve_candidates
from .palette_quant import select_palette, quantize_image
from .placer import resolve_base_position, compute_world_coords, blocks_to_commands

logger = logging.getLogger(__name__)


def _open_image_with_alpha(path: str):
    from PIL import Image
    im = Image.open(path)
    # If image has alpha, flatten onto white to avoid unintended transparency holes
    if im.mode in ("RGBA", "LA") or ("transparency" in im.info):
        base = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im_rgba = im.convert("RGBA")
        base.paste(im_rgba, (0, 0), im_rgba)
        return base.convert("RGB")
    return im.convert("RGB")


def render_image_op(params: dict, rcon, context: dict) -> dict:
    image_path = params.get('image_path')
    if not image_path:
        return {"success": False, "error": "image_path required"}

    mode = params.get('mode', 'wall')
    if mode not in ('wall', 'floor'):
        return {"success": False, "error": "mode must be 'wall' or 'floor'"}

    target_width = int(params.get('target_width', 64) or 64)
    if target_width < 1 or target_width > 512:
        return {"success": False, "error": "target_width must be 1-512"}

    try:
        from PIL import Image  # noqa: F401 (import check)
    except Exception:
        return {"success": False, "error": "Pillow not installed", "hint": "pip install pillow>=10"}

    try:
        start_ts = time.time()
        base_dir, rel, original = normalize_image_path(image_path)
        candidates = resolve_candidates(base_dir, rel, original)
        actual_path = next((c for c in candidates if os.path.exists(c)), None)
        if not actual_path:
            return {
                "success": False,
                "error": "Image not found",
                "searched_paths": candidates,
                "note": "Place the file under docs/images at your project root or current working directory.",
            }

        im = _open_image_with_alpha(actual_path)
        w0, h0 = im.size
        if w0 <= 0 or h0 <= 0:
            return {"success": False, "error": "Invalid image dimensions"}
        if w0 != target_width:
            from PIL import Image as _Image
            new_h = max(1, int(round(h0 * (target_width / float(w0)))))
            im = im.resize((target_width, new_h), _Image.NEAREST)
        w, h = im.size

        # Positioning
        base_x, base_y, base_z = resolve_base_position(params, context)
        anchor = params.get('anchor', 'bottom')
        anchor_xz = params.get('anchor_xz', 'center')
        start_x, start_y, fixed_z, start_z = compute_world_coords(
            mode, w, h, base_x, base_y, base_z, anchor, anchor_xz
        )

        # Quantization -> blocks per pixel
        palette, palette_mode = select_palette(params)
        block_rows = quantize_image(im, palette, params)

        # Safety: never place 'air' from quantization; replace with safe fallback
        fallback_blk = 'white_concrete' if 'white_concrete' in palette else 'white_wool'
        unique_blocks = set()
        for y in range(len(block_rows)):
            row = block_rows[y]
            for x in range(len(row)):
                blk = row[x]
                if not blk or blk == 'air':
                    row[x] = fallback_blk
                unique_blocks.add(row[x])

        # Assemble per (wy,wz)
        by_yz: Dict[Tuple[int, int], List[Tuple[int, str]]] = {}
        for y in range(h):
            if mode == 'wall':
                wy, wz = (start_y + (h - 1 - y), fixed_z)
            else:
                wy, wz = (start_y, (start_z if start_z is not None else base_z) + y)
            row_items = [(start_x + x, block_rows[y][x]) for x in range(w)]
            by_yz.setdefault((wy, wz), []).extend(row_items)

        # Commands
        commands = blocks_to_commands(
            by_yz,
            bool(params.get('clear_area', False)),
            mode,
            start_x,
            start_y,
            w,
            h,
            base_z,
            fixed_z,
            start_z,
        )

        # Safety cap
        MAX_CMDS = 50000
        if len(commands) > MAX_CMDS:
            commands = commands[:MAX_CMDS]

        delay = int(params.get('delay_ms', 50) or 50)
        logger.info(f"Rendering image {actual_path} as {mode}: {w}x{h} -> {len(commands)} fill commands")
        results = rcon.execute_batch(commands, delay_ms=delay)
        executed = sum(1 for r in results if r['success'])
        failed = len(commands) - executed

        elapsed = (time.time() - start_ts) * 1000
        warnings = []
        if failed > 0:
            warnings.append(f"{failed} commands failed")

        return {
            "success": executed > 0,
            "mode": mode,
            "image_path": image_path,
            "resolved_path": actual_path,
            "width": w,
            "height": h,
            "palette": palette_mode,
            "distance": (params.get('distance') or 'rgb').lower(),
            "dither": bool(params.get('dither', False)),
            "image_mapping": params.get('image_mapping', 'color'),
            "unique_blocks_used": sorted(unique_blocks),
            "fill_commands": len(commands),
            "executed_count": executed,
            "failed_count": failed,
            "spawn_position": {"x": base_x, "y": base_y, "z": base_z},
            "time_ms": elapsed,
            "warnings": warnings,
        }

    except Exception as e:
        logger.error(f"Render image failed: {e}", exc_info=True)
        return {"success": False, "error": str(e), "error_type": type(e).__name__, "image_path": image_path}
