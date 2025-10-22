"""
Spawn entities operation
"""
import logging
import time
from ..geometry import calculate_spread_positions
from ..utils import CommandBuilder, build_nbt

logger = logging.getLogger(__name__)

def spawn_entities_op(params: dict, rcon, context: dict) -> dict:
    """Spawn entities with spread pattern
    
    Strategy:
    - If relative_to_player=True (default): use execute-as local coordinates (^x ^y ^z)
      so we don't depend on absolute player position/rotation.
    - Otherwise: use absolute world coordinates (context.resolved_position)
    
    Args:
        params: {entity_type, count, position, spread_pattern, nbt_data, player_name}
        rcon: RconClient
        context: {resolved_position, ...}
        
    Returns:
        {success, spawned_count, entity_type, positions, warnings}
    """
    entity_type = params.get('entity_type')
    count = params.get('count', 1)
    pattern = params.get('spread_pattern', 'random')
    nbt_data = params.get('nbt_data')
    player_selector = params.get('player_name', '@p')
    relative = params.get('relative_to_player', True)
    
    if not entity_type:
        return {
            "success": False,
            "error": "entity_type required"
        }
    
    try:
        start_time = time.time()
        warnings = []
        nbt_str = build_nbt(nbt_data) if nbt_data else ""
        
        if relative:
            # Offsets in LOCAL frame (right, up, forward)
            off = params.get('offset', {}) or {}
            forward_offset = float(off.get('forward', 0) or 0)
            up_offset = float(off.get('up', 0) or 0)
            right_offset = float(off.get('right', 0) or 0)
            
            # Base local anchor around player
            base_local = {"x": right_offset, "y": up_offset, "z": forward_offset}
            local_positions = calculate_spread_positions(base_local, count, pattern)
            
            commands = []
            for pos in local_positions:
                dx = pos['x']
                dy = pos['y']
                dz = pos['z']
                local_pos = f"^{dx:.2f} ^{dy:.2f} ^{dz:.2f}"
                cmd = f"execute as {player_selector} at @s run summon {entity_type} {local_pos}"
                if nbt_str:
                    cmd += f" {nbt_str}"
                commands.append(cmd)
        else:
            # Absolute world coords (fallback)
            base_pos = context.get('resolved_position', {'x': 0, 'y': 64, 'z': 0})
            positions = calculate_spread_positions(base_pos, count, pattern)
            commands = []
            for pos in positions:
                cmd = CommandBuilder.summon(
                    entity_type,
                    pos['x'], pos['y'], pos['z'],
                    nbt_str
                )
                commands.append(cmd)
        
        # Execute batch
        logger.info(f"Spawning {count} {entity_type} entities (relative={relative}) with pattern '{pattern}'")
        results = rcon.execute_batch(commands, delay_ms=params.get('delay_ms', 50))
        
        spawned = sum(1 for r in results if r['success'])
        failed = len(commands) - spawned
        
        elapsed = (time.time() - start_time) * 1000
        
        if failed > 0:
            warnings.append(f"{failed} entities failed to spawn")
        
        # Output (return local offsets when relative)
        limit = params.get('limit', 50)
        truncated = len(commands) > limit
        if relative:
            listed_positions = local_positions[:limit] if truncated else local_positions
        else:
            listed_positions = positions[:limit] if truncated else positions
        if truncated:
            warnings.append(f"Position list truncated ({len(commands)} total, showing {limit})")
        
        return {
            "success": spawned > 0,
            "spawned_count": spawned,
            "failed_count": failed,
            "entity_type": entity_type,
            "pattern": pattern,
            "positions": listed_positions,
            "total_positions": len(commands),
            "truncated": truncated,
            "time_ms": elapsed,
            "warnings": warnings
        }
    
    except Exception as e:
        logger.error(f"Spawn entities failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "entity_type": entity_type
        }
