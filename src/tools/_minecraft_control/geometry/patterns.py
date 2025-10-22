"""
Entity spread patterns
"""
import logging
import math
import random
from ..config import ENTITY_SPREAD_SPACING, RANDOM_SPREAD_RADIUS

logger = logging.getLogger(__name__)

def calculate_spread_positions(base_pos: dict, count: int, 
                               pattern: str = "random", 
                               spacing: float = ENTITY_SPREAD_SPACING) -> list[dict]:
    """Calculate positions for entity spread
    
    Args:
        base_pos: Center position {x, y, z}
        count: Number of positions
        pattern: line/circle/grid/random
        spacing: Distance between entities
        
    Returns:
        List of {x, y, z} positions
    """
    if count == 1:
        return [base_pos.copy()]
    
    generators = {
        'line': _pattern_line,
        'circle': _pattern_circle,
        'grid': _pattern_grid,
        'random': _pattern_random
    }
    
    generator = generators.get(pattern, _pattern_random)
    positions = generator(base_pos, count, spacing)
    
    logger.debug(f"Generated {len(positions)} positions with pattern '{pattern}'")
    return positions

def _pattern_line(base: dict, count: int, spacing: float) -> list[dict]:
    """Line pattern along X axis"""
    positions = []
    start_x = base['x'] - (count - 1) * spacing / 2
    
    for i in range(count):
        positions.append({
            'x': start_x + i * spacing,
            'y': base['y'],
            'z': base['z']
        })
    
    return positions

def _pattern_circle(base: dict, count: int, spacing: float) -> list[dict]:
    """Circle pattern around center"""
    positions = []
    radius = (count * spacing) / (2 * math.pi)  # Approximate radius
    
    for i in range(count):
        angle = 2 * math.pi * i / count
        positions.append({
            'x': base['x'] + radius * math.cos(angle),
            'y': base['y'],
            'z': base['z'] + radius * math.sin(angle)
        })
    
    return positions

def _pattern_grid(base: dict, count: int, spacing: float) -> list[dict]:
    """Grid pattern (square arrangement)"""
    positions = []
    cols = int(math.ceil(math.sqrt(count)))
    
    start_x = base['x'] - (cols - 1) * spacing / 2
    start_z = base['z'] - (cols - 1) * spacing / 2
    
    for i in range(count):
        row = i // cols
        col = i % cols
        positions.append({
            'x': start_x + col * spacing,
            'y': base['y'],
            'z': start_z + row * spacing
        })
    
    return positions

def _pattern_random(base: dict, count: int, spacing: float) -> list[dict]:
    """Random scatter around center"""
    positions = []
    radius = RANDOM_SPREAD_RADIUS
    
    for _ in range(count):
        # Random position within radius
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, radius)
        
        positions.append({
            'x': base['x'] + dist * math.cos(angle),
            'y': base['y'],
            'z': base['z'] + dist * math.sin(angle)
        })
    
    return positions
