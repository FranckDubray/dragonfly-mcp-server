"""
Build structure operation
"""
import logging
import time
from ..geometry import generate_shape_volume
from ..utils import CommandBuilder, chunk_blocks, estimate_blocks

logger = logging.getLogger(__name__)

def build_structure_op(params: dict, rcon, context: dict) -> dict:
    """Build geometric structure
    
    Args:
        params: {block_type, dimensions, shape, hollow, start_pos, end_pos}
        rcon: RconClient
        context: {resolved_position, ...}
        
    Returns:
        {success, blocks_placed, chunks_count, shape, time_ms, warnings}
    """
    block_type = params.get('block_type')
    shape = params.get('shape', 'cube')
    hollow = params.get('hollow', False)
    
    if not block_type:
        return {
            "success": False,
            "error": "block_type required"
        }
    
    try:
        start_time = time.time()
        
        # Resolve bounds
        start_pos, end_pos = _resolve_structure_bounds(params, context)
        
        # Estimate total blocks
        total_blocks = estimate_blocks(start_pos, end_pos)
        logger.info(f"Building {shape} structure: {total_blocks} blocks estimated")
        
        # Adjust for shape
        shape_start, shape_end = generate_shape_volume(start_pos, end_pos, shape, hollow)
        
        # Chunk if needed
        chunks = chunk_blocks(shape_start, shape_end)
        
        # Build fill commands
        commands = []
        for chunk_start, chunk_end in chunks:
            cmd = CommandBuilder.fill(
                chunk_start['x'], chunk_start['y'], chunk_start['z'],
                chunk_end['x'], chunk_end['y'], chunk_end['z'],
                block_type
            )
            commands.append(cmd)
        
        # Execute batch with throttling
        logger.info(f"Executing {len(commands)} fill commands")
        results = rcon.execute_batch(commands, delay_ms=params.get('delay_ms', 50))
        
        # Calculate blocks placed
        successful_chunks = sum(1 for r in results if r['success'])
        failed_chunks = len(chunks) - successful_chunks
        
        # Estimate actual blocks placed (rough calculation)
        blocks_per_chunk = total_blocks / len(chunks) if chunks else total_blocks
        blocks_placed = int(successful_chunks * blocks_per_chunk)
        
        elapsed = (time.time() - start_time) * 1000
        
        warnings = []
        if failed_chunks > 0:
            warnings.append(f"{failed_chunks} chunks failed to place")
        if total_blocks > 10000:
            warnings.append(f"Large structure ({total_blocks} blocks) - may cause lag")
        
        return {
            "success": successful_chunks > 0,
            "blocks_placed": blocks_placed,
            "blocks_estimated": total_blocks,
            "chunks_count": len(chunks),
            "failed_chunks": failed_chunks,
            "shape": shape,
            "block_type": block_type,
            "dimensions": {
                "width": abs(end_pos['x'] - start_pos['x']) + 1,
                "height": abs(end_pos['y'] - start_pos['y']) + 1,
                "depth": abs(end_pos['z'] - start_pos['z']) + 1
            },
            "time_ms": elapsed,
            "warnings": warnings
        }
    
    except Exception as e:
        logger.error(f"Build structure failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "block_type": block_type,
            "shape": shape
        }

def _resolve_structure_bounds(params: dict, context: dict) -> tuple[dict, dict]:
    """Resolve start/end positions for structure
    
    Returns:
        (start_pos, end_pos) tuple
    """
    # Explicit start/end
    if 'start_pos' in params and 'end_pos' in params:
        return (params['start_pos'], params['end_pos'])
    
    # Dimensions-based
    if 'dimensions' in params:
        dims = params['dimensions']
        base_pos = context.get('resolved_position', {'x': 0, 'y': 64, 'z': 0})
        
        width = dims.get('width', 10)
        height = dims.get('height', 10)
        depth = dims.get('depth', 10)
        
        # Center structure at base position
        start_pos = {
            'x': base_pos['x'] - width // 2,
            'y': base_pos['y'],
            'z': base_pos['z'] - depth // 2
        }
        end_pos = {
            'x': start_pos['x'] + width - 1,
            'y': start_pos['y'] + height - 1,
            'z': start_pos['z'] + depth - 1
        }
        
        return (start_pos, end_pos)
    
    # Default 10x10x10 cube
    base_pos = context.get('resolved_position', {'x': 0, 'y': 64, 'z': 0})
    start_pos = {'x': base_pos['x'] - 5, 'y': base_pos['y'], 'z': base_pos['z'] - 5}
    end_pos = {'x': base_pos['x'] + 4, 'y': base_pos['y'] + 9, 'z': base_pos['z'] + 4}
    
    return (start_pos, end_pos)
