"""
Minecraft Control - RCON-based Minecraft server control
Execute commands, spawn entities, build structures, import 3D models
"""
import json
import os

def spec():
    """Load canonical JSON spec"""
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'minecraft_control.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run(**params):
    """Execute Minecraft operation via RCON
    
    Params:
        operation: str - Operation to perform
        **kwargs: Operation-specific parameters
        
    Returns:
        dict: {success, operation, result, stats, warnings}
    """
    from ._minecraft_control.api import execute_operation
    return execute_operation(**params)
