"""
3D model voxelization (requires trimesh)
"""
import logging
import os
from ..config import MODELS_DIR, ALLOWED_MODEL_EXTENSIONS

logger = logging.getLogger(__name__)
# Silence verbose trimesh debug logs
logging.getLogger('trimesh').setLevel(logging.WARNING)

# --------------------------
# Project root / paths utils
# --------------------------

def _find_project_root(start: str) -> str:
    cur = os.path.abspath(start)
    for _ in range(8):
        if os.path.isfile(os.path.join(cur, 'pyproject.toml')) or os.path.isdir(os.path.join(cur, '.git')):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


def _get_models_base_dir() -> str:
    root = _find_project_root(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(root, 'docs', 'models'))

# --------------------------
# Normalization / loading
# --------------------------

def _normalize_model_path(model_path: str) -> tuple[str, str]:
    base_dir = _get_models_base_dir()
    p = (model_path or '').replace('\\', '/').strip()
    for prefix in ('src/docs/models/', 'docs/models/', './docs/models/', '/docs/models/'):
        if p.startswith(prefix):
            p = p[len(prefix):]
            break
    p = p.lstrip('/')
    rel = os.path.normpath(p)
    if rel.startswith('..') or os.path.isabs(rel):
        raise ValueError("model_path must be relative to docs/models/ (no traversal)")
    return base_dir, rel


def load_3d_model(model_path: str):
    try:
        import trimesh
        from trimesh import util as _trimesh_util
    except ImportError:
        raise ImportError("trimesh not installed. Install with: pip install trimesh[easy]")

    base_dir, rel = _normalize_model_path(model_path)
    full_path = os.path.join(base_dir, rel)

    ext = os.path.splitext(full_path)[1].lower()
    if ext not in ALLOWED_MODEL_EXTENSIONS:
        raise ValueError(f"Unsupported format: {ext}. Allowed: {ALLOWED_MODEL_EXTENSIONS}")

    if not os.path.exists(full_path):
        raise FileNotFoundError(
            f"Model file not found: {full_path}. Place files under {base_dir} and pass a relative path like 'file.fbx' or 'subdir/file.obj'."
        )

    logger.info(f"Loading 3D model: {rel} (from {base_dir})")

    try:
        mesh = trimesh.load(full_path)
        # If Scene → merge
        if hasattr(mesh, 'geometry') and not hasattr(mesh, 'vertices'):
            try:
                mesh = _trimesh_util.concatenate(tuple(mesh.geometry.values()))
            except Exception:
                pass
        # If list of meshes → merge or take first with vertices
        if isinstance(mesh, (list, tuple)):
            try:
                mesh = _trimesh_util.concatenate(tuple(m for m in mesh if hasattr(m, 'vertices')))
            except Exception:
                mesh = next((m for m in mesh if hasattr(m, 'vertices')), mesh)
        vcount = len(mesh.vertices) if hasattr(mesh, 'vertices') else 0
        fcount = len(mesh.faces) if hasattr(mesh, 'faces') else 0
        logger.info(f"Model loaded: vertices={vcount}, faces={fcount}")
        return mesh
    except Exception as e:
        raise ValueError(f"Failed to load model: {e}")

# --------------------------
# Color helpers (faces / textures / vertex colors)
# --------------------------

def _precompute_face_colors(mesh):
    """Return per-face RGB (uint8) from available visuals: priority vertex->face->texture->default.
    If texture present with UV, sample per-vertex texel and average per face.
    """
    try:
        import numpy as np
    except ImportError:
        return None

    n_faces = len(getattr(mesh, 'faces', []))
    if n_faces == 0:
        return None

    # Vertex colors → average per face
    try:
        if hasattr(mesh, 'visual') and hasattr(mesh.visual, 'vertex_colors') and mesh.visual.vertex_colors is not None:
            vc = mesh.visual.vertex_colors
            if getattr(vc, 'shape', [0])[0] >= len(mesh.vertices):
                cols = vc[:, :3].astype(np.float64)
                faces = mesh.faces.astype(np.int64)
                fa = cols[faces[:, 0]]
                fb = cols[faces[:, 1]]
                fc = cols[faces[:, 2]]
                face_cols = ((fa + fb + fc) / 3.0).astype(np.uint8)
                return face_cols
    except Exception:
        pass

    # Face colors directly
    try:
        if hasattr(mesh, 'visual') and hasattr(mesh.visual, 'face_colors') and mesh.visual.face_colors is not None:
            fc = mesh.visual.face_colors
            if getattr(fc, 'shape', [0])[0] >= n_faces:
                return fc[:, :3].astype(np.uint8)
    except Exception:
        pass

    # Texture (UV + image): sample texel at each vertex UV then average per face
    try:
        if hasattr(mesh, 'visual') and getattr(mesh.visual, 'material', None) is not None:
            material = mesh.visual.material
            image = getattr(material, 'image', None)
            uv = getattr(mesh.visual, 'uv', None)
            if image is not None and uv is not None:
                from PIL import Image
                import numpy as np
                if isinstance(image, Image.Image):
                    tex = image.convert('RGB')
                    tw, th = tex.size
                    uvf = np.clip(uv, 0.0, 1.0)
                    # Sample per-vertex UV
                    us = (uvf[:, 0] * (tw - 1)).astype(np.int64)
                    vs = ((1.0 - uvf[:, 1]) * (th - 1)).astype(np.int64)  # flip V
                    tex_np = np.array(tex, dtype=np.uint8)
                    vcols = tex_np[vs, us, :]
                    faces = mesh.faces.astype(np.int64)
                    fa = vcols[faces[:, 0]]
                    fb = vcols[faces[:, 1]]
                    fc = vcols[faces[:, 2]]
                    face_cols = ((fa + fb + fc) / 3.0).astype(np.uint8)
                    return face_cols
    except Exception:
        pass

    return None


# --------------------------
# Voxelization (fast path using trimesh.voxelized)
# --------------------------

def voxelize_model(mesh, resolution: float = 1.0, scale: float = 1.0) -> dict:
    """Voxelize 3D mesh quickly using trimesh.voxelized.

    Returns:
        Dict {(x, y, z): (r, g, b)} - voxel indices with colors
    """
    try:
        import numpy as np
        from trimesh.proximity import closest_point
    except ImportError:
        raise ImportError("numpy required for voxelization")

    if scale != 1.0:
        mesh.apply_scale(scale)

    # Precompute face colors once (may be None → fallback gray)
    face_cols = _precompute_face_colors(mesh)

    # Fast voxelizer
    try:
        vg = mesh.voxelized(pitch=resolution)
        pitch = getattr(vg, 'pitch', resolution)
        origin = getattr(vg, 'origin', None)
        idx = getattr(vg, 'sparse_indices', None)
        if idx is None:
            mat = vg.matrix.astype(bool)
            idx = np.argwhere(mat)
        voxel_dict: dict[tuple[int,int,int], tuple[int,int,int]] = {}

        # Build world points for all voxels
        if idx is not None and len(idx) > 0:
            if origin is not None:
                world_pts = origin + (idx + 0.5) * pitch
            else:
                bounds = mesh.bounds
                min_bound = bounds[0]
                world_pts = min_bound + (idx + 0.5) * resolution

            # If we have face colors, snap each point to nearest face and assign its color
            if face_cols is not None:
                pts, dist, fids = closest_point(mesh, world_pts)
                # Clamp face ids
                fids = np.clip(fids, 0, len(face_cols) - 1)
                colors = face_cols[fids]
                for (vx, vy, vz), col in zip(idx, colors):
                    voxel_dict[(int(vx), int(vy), int(vz))] = (int(col[0]), int(col[1]), int(col[2]))
            else:
                # Fallback grayscale
                for i in idx:
                    vx, vy, vz = int(i[0]), int(i[1]), int(i[2])
                    voxel_dict[(vx, vy, vz)] = (128, 128, 128)

        logger.info(f"Generated {len(voxel_dict)} voxels (fast voxelizer)")
        return voxel_dict
    except Exception as e:
        logger.warning(f"Fast voxelizer failed ({e}), falling back to batched contains()")

    # --------------- Fallback method (with progress) ---------------
    bounds = mesh.bounds
    min_bound = bounds[0]
    max_bound = bounds[1]
    dims = (max_bound - min_bound) / max(resolution, 1e-6)
    grid_dims = np.ceil(dims).astype(int)

    logger.info(f"Voxel grid dimensions: {grid_dims} (resolution={resolution})")

    max_voxels = 50000
    total_voxels = int(grid_dims[0] * grid_dims[1] * grid_dims[2])

    if total_voxels > max_voxels:
        logger.warning(f"Voxel count {total_voxels} exceeds limit {max_voxels}, truncating by adjusting resolution")
        scale_factor = (max_voxels / max(total_voxels, 1)) ** (1/3)
        resolution = resolution / max(scale_factor, 1e-6)
        dims = (max_bound - min_bound) / resolution
        grid_dims = np.ceil(dims).astype(int)
        total_voxels = int(grid_dims[0] * grid_dims[1] * grid_dims[2])
        logger.info(f"Adjusted resolution: {resolution:.3f}, new grid: {grid_dims}")

    voxel_dict: dict[tuple[int, int, int], tuple[int, int, int]] = {}

    BATCH = 8192
    points: list = []
    coords: list = []

    processed = 0
    next_pct = 5

    def maybe_log_progress():
        nonlocal next_pct
        if total_voxels <= 0:
            return
        pct = int(processed * 100 / total_voxels)
        while pct >= next_pct and next_pct <= 100:
            logger.info(f"Voxelization progress: {next_pct}% ({processed}/{total_voxels})")
            next_pct += 5

    # Precompute colors if available
    import numpy as np  # ensure available here
    has_face = face_cols is not None

    def color_for_point(pt):
        if has_face:
            from trimesh.proximity import closest_point
            _, _, fid = closest_point(mesh, pt.reshape(1, 3))
            fid = int(max(0, min(int(fid[0]), len(face_cols) - 1)))
            col = face_cols[fid]
            return (int(col[0]), int(col[1]), int(col[2]))
        return (128, 128, 128)

    for x in range(int(grid_dims[0])):
        for y in range(int(grid_dims[1])):
            for z in range(int(grid_dims[2])):
                world_pos = min_bound + (np.array([x + 0.5, y + 0.5, z + 0.5]) * resolution)
                points.append(world_pos)
                coords.append((x, y, z))
                if len(points) >= BATCH:
                    # Assign colors
                    for (cx, cy, cz), pt in zip(coords, points):
                        voxel_dict[(int(cx), int(cy), int(cz))] = color_for_point(pt)
                    processed += len(coords)
                    points = []
                    coords = []
                    maybe_log_progress()
    # Flush remaining
    for (cx, cy, cz), pt in zip(coords, points):
        voxel_dict[(int(cx), int(cy), int(cz))] = color_for_point(pt)
    processed += len(coords)

    logger.info(f"Voxelization progress: 100% ({processed}/{total_voxels})")
    logger.info(f"Generated {len(voxel_dict)} voxels (fallback)")
    return voxel_dict


def _get_voxel_color(mesh, point) -> tuple:
    # Deprecated: kept for compatibility, not used in fast path anymore
    try:
        if hasattr(mesh, 'visual') and hasattr(mesh.visual, 'vertex_colors'):
            colors = mesh.visual.vertex_colors
            if getattr(colors, 'shape', [0])[0] > 0:
                import numpy as np
                avg_color = np.mean(colors[:, :3], axis=0)
                return (int(avg_color[0]), int(avg_color[1]), int(avg_color[2]))
    except Exception:
        pass
    return (128, 128, 128)
