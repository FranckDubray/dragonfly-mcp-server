"""
3D shape generation
"""
import logging
import math
from ..config import SPHERE_PRECISION, CYLINDER_PRECISION

logger = logging.getLogger(__name__)

def generate_shape_volume(start: dict, end: dict, shape: str, hollow: bool = False) -> tuple[dict, dict]:
    """Generate bounding volume for shape
    
    Args:
        start: Start corner {x, y, z}
        end: End corner {x, y, z}
        shape: Shape type
        hollow: Create hollow shape
        
    Returns:
        (adjusted_start, adjusted_end) for /fill commands
        
    Note: Complex shapes (sphere, pyramid) are approximated with multiple chunks
    """
    if shape == "cube":
        return (start, end)
    
    elif shape == "sphere":
        return _shape_sphere(start, end, hollow)
    
    elif shape == "pyramid":
        return _shape_pyramid(start, end)
    
    elif shape == "cylinder":
        return _shape_cylinder(start, end, hollow)
    
    elif shape == "wall":
        return _shape_wall(start, end)
    
    elif shape == "platform":
        return _shape_platform(start, end)
    
    else:
        logger.warning(f"Unknown shape '{shape}', using cube")
        return (start, end)

def _shape_sphere(start: dict, end: dict, hollow: bool) -> tuple[dict, dict]:
    """Sphere approximation (returns bounding box)
    
    Note: Actual sphere generation requires per-block checking
    This returns the bounding cube for chunking
    """
    # Calculate center and radius
    cx = (start['x'] + end['x']) / 2
    cy = (start['y'] + end['y']) / 2
    cz = (start['z'] + end['z']) / 2
    
    rx = abs(end['x'] - start['x']) / 2
    ry = abs(end['y'] - start['y']) / 2
    rz = abs(end['z'] - start['z']) / 2
    
    # For sphere, use average radius
    r = (rx + ry + rz) / 3
    
    sphere_start = {
        'x': cx - r,
        'y': cy - r,
        'z': cz - r
    }
    sphere_end = {
        'x': cx + r,
        'y': cy + r,
        'z': cz + r
    }
    
    logger.info(f"Sphere center=({cx:.1f},{cy:.1f},{cz:.1f}) radius={r:.1f}")
    return (sphere_start, sphere_end)

def _shape_pyramid(start: dict, end: dict) -> tuple[dict, dict]:
    """Pyramid (returns bounding box for base)
    
    Pyramid tapers from base to apex
    Apex is at max Y coordinate
    """
    # Pyramid uses full XZ extent at base (min Y)
    # Tapers to point at top (max Y)
    return (start, end)

def _shape_cylinder(start: dict, end: dict, hollow: bool) -> tuple[dict, dict]:
    """Cylinder along Y axis"""
    # Cylinder uses full Y extent
    # Circular cross-section in XZ plane
    cx = (start['x'] + end['x']) / 2
    cz = (start['z'] + end['z']) / 2
    
    rx = abs(end['x'] - start['x']) / 2
    rz = abs(end['z'] - start['z']) / 2
    r = (rx + rz) / 2  # Average radius
    
    cyl_start = {
        'x': cx - r,
        'y': start['y'],
        'z': cz - r
    }
    cyl_end = {
        'x': cx + r,
        'y': end['y'],
        'z': cz + r
    }
    
    return (cyl_start, cyl_end)

def _shape_wall(start: dict, end: dict) -> tuple[dict, dict]:
    """Vertical wall (thin in one dimension)"""
    # Wall is typically thin in X or Z
    # Make thickness = 1 block in thinnest dimension
    dx = abs(end['x'] - start['x'])
    dz = abs(end['z'] - start['z'])
    
    if dx < dz:
        # Wall along Z axis, thin in X
        wall_end = end.copy()
        wall_end['x'] = start['x']
        return (start, wall_end)
    else:
        # Wall along X axis, thin in Z
        wall_end = end.copy()
        wall_end['z'] = start['z']
        return (start, wall_end)

def _shape_platform(start: dict, end: dict) -> tuple[dict, dict]:
    """Horizontal platform (thin in Y)"""
    # Platform is 1 block thick in Y
    platform_end = end.copy()
    platform_end['y'] = start['y']
    return (start, platform_end)

def is_point_in_shape(point: dict, center: dict, dimensions: dict, shape: str) -> bool:
    """Check if point is inside shape (for per-block generation)
    
    Args:
        point: {x, y, z} to test
        center: Shape center
        dimensions: Shape dimensions
        shape: Shape type
        
    Returns:
        True if point inside shape
    """
    if shape == "sphere":
        return _point_in_sphere(point, center, dimensions)
    elif shape == "pyramid":
        return _point_in_pyramid(point, center, dimensions)
    elif shape == "cylinder":
        return _point_in_cylinder(point, center, dimensions)
    else:
        return True  # Cube/other shapes use bounding box

def _point_in_sphere(point: dict, center: dict, dims: dict) -> bool:
    """Point in sphere test"""
    rx = dims['width'] / 2
    ry = dims['height'] / 2
    rz = dims['depth'] / 2
    
    dx = (point['x'] - center['x']) / rx
    dy = (point['y'] - center['y']) / ry
    dz = (point['z'] - center['z']) / rz
    
    return (dx*dx + dy*dy + dz*dz) <= 1.0

def _point_in_pyramid(point: dict, center: dict, dims: dict) -> bool:
    """Point in pyramid test (apex at top)"""
    # Pyramid tapers linearly from base to apex
    base_y = center['y'] - dims['height'] / 2
    apex_y = center['y'] + dims['height'] / 2
    
    if point['y'] < base_y or point['y'] > apex_y:
        return False
    
    # Calculate taper factor (1.0 at base, 0.0 at apex)
    taper = 1.0 - (point['y'] - base_y) / dims['height']
    
    # Check if within tapered bounds
    max_x = (dims['width'] / 2) * taper
    max_z = (dims['depth'] / 2) * taper
    
    dx = abs(point['x'] - center['x'])
    dz = abs(point['z'] - center['z'])
    
    return dx <= max_x and dz <= max_z

def _point_in_cylinder(point: dict, center: dict, dims: dict) -> bool:
    """Point in cylinder test (along Y axis)"""
    # Check Y bounds
    half_h = dims['height'] / 2
    if abs(point['y'] - center['y']) > half_h:
        return False
    
    # Check circular cross-section
    rx = dims['width'] / 2
    rz = dims['depth'] / 2
    r = (rx + rz) / 2
    
    dx = point['x'] - center['x']
    dz = point['z'] - center['z']
    dist = math.sqrt(dx*dx + dz*dz)
    
    return dist <= r
