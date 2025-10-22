"""
Voxel package (3D model processing)
"""
from .voxelizer import voxelize_model, load_3d_model
from .block_mapper import map_voxels_to_blocks, BLOCK_COLOR_PALETTE

__all__ = [
    'voxelize_model',
    'load_3d_model',
    'map_voxels_to_blocks',
    'BLOCK_COLOR_PALETTE'
]
