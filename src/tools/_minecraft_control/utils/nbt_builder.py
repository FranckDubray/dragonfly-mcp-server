"""
NBT tag builder
"""
import json
import logging

logger = logging.getLogger(__name__)

def build_nbt(data: dict) -> str:
    """Build NBT string from dict
    
    Args:
        Python dict with NBT data
        
    Returns:
        NBT string format (Minecraft JSON-like)
        
    Example:
        {"CustomName": "Test"} -> '{CustomName:"Test"}'
    """
    if not data:
        return ""
    
    def serialize_value(val):
        """Serialize Python value to NBT format"""
        if isinstance(val, str):
            # String values in quotes
            return f'"{val}"'
        elif isinstance(val, bool):
            # Boolean as 1b/0b
            return "1b" if val else "0b"
        elif isinstance(val, int):
            return str(val)
        elif isinstance(val, float):
            return f"{val}f"
        elif isinstance(val, list):
            # Arrays
            items = [serialize_value(item) for item in val]
            return f"[{','.join(items)}]"
        elif isinstance(val, dict):
            # Nested compound
            return serialize_compound(val)
        else:
            return str(val)
    
    def serialize_compound(compound: dict) -> str:
        """Serialize compound tag"""
        parts = []
        for key, val in compound.items():
            parts.append(f"{key}:{serialize_value(val)}")
        return f"{{{','.join(parts)}}}"
    
    try:
        return serialize_compound(data)
    except Exception as e:
        logger.warning(f"NBT build failed: {e}, using JSON fallback")
        return json.dumps(data)
