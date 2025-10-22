"""
Block chunking for large operations
"""
import logging
import math
from ..config import MAX_BLOCKS_PER_CHUNK

logger = logging.getLogger(__name__)

def chunk_blocks(start_pos: dict, end_pos: dict) -> list[tuple[dict, dict]]:
    """Split large volume into chunks <32k blocks
    
    Args:
        start_pos: {x, y, z} start corner
        end_pos: {x, y, z} end corner
        
    Returns:
        List of (chunk_start, chunk_end) tuples
    """
    # Calculate total volume
    dx = abs(end_pos['x'] - start_pos['x']) + 1
    dy = abs(end_pos['y'] - start_pos['y']) + 1
    dz = abs(end_pos['z'] - start_pos['z']) + 1
    total_blocks = dx * dy * dz
    
    if total_blocks <= MAX_BLOCKS_PER_CHUNK:
        return [(start_pos, end_pos)]
    
    logger.info(f"Chunking {total_blocks} blocks into <{MAX_BLOCKS_PER_CHUNK} block chunks")
    
    chunks = []
    
    # Calculate optimal chunk size (cubic chunks)
    chunk_size = int(math.pow(MAX_BLOCKS_PER_CHUNK * 0.95, 1/3))  # 95% safety margin
    
    # Normalize coordinates (ensure start < end)
    min_x, max_x = sorted([start_pos['x'], end_pos['x']])
    min_y, max_y = sorted([start_pos['y'], end_pos['y']])
    min_z, max_z = sorted([start_pos['z'], end_pos['z']])
    
    # Generate chunks
    x = min_x
    while x <= max_x:
        y = min_y
        while y <= max_y:
            z = min_z
            while z <= max_z:
                chunk_start = {
                    'x': x,
                    'y': y,
                    'z': z
                }
                chunk_end = {
                    'x': min(x + chunk_size - 1, max_x),
                    'y': min(y + chunk_size - 1, max_y),
                    'z': min(z + chunk_size - 1, max_z)
                }
                chunks.append((chunk_start, chunk_end))
                z += chunk_size
            y += chunk_size
        x += chunk_size
    
    logger.info(f"Created {len(chunks)} chunks")
    return chunks

def estimate_blocks(start_pos: dict, end_pos: dict) -> int:
    """Estimate number of blocks in volume"""
    dx = abs(end_pos['x'] - start_pos['x']) + 1
    dy = abs(end_pos['y'] - start_pos['y']) + 1
    dz = abs(end_pos['z'] - start_pos['z']) + 1
    return int(dx * dy * dz)
