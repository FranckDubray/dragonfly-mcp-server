"""
Fit/scale helpers for voxel import.
"""
from typing import Tuple, Optional

def fit_scale_from_bounds(mesh, orient: str, target_height: Optional[float], base_scale: float) -> Tuple[float, bool]:
    """Compute a new scale to meet target_height (if any) and decide z-up usage for fit.

    Returns (new_scale, use_z_up_for_fit)
    """
    try:
        bounds = getattr(mesh, 'bounds', None)
        if bounds is None:
            return base_scale, False
        import numpy as _np
        extents = _np.array(bounds[1]) - _np.array(bounds[0])
        y_extent = float(extents[1])
        z_extent = float(extents[2])
        use_z_up_for_fit = False
        if orient == 'z_up_to_y':
            use_z_up_for_fit = True
        elif orient == 'auto':
            use_z_up_for_fit = z_extent > (y_extent * 1.25)
        height_extent = z_extent if use_z_up_for_fit else y_extent
        if target_height and height_extent > 1e-6:
            fit_scale = float(target_height) / height_extent
            return base_scale * fit_scale, use_z_up_for_fit
        return base_scale, use_z_up_for_fit
    except Exception:
        return base_scale, False
