"""
Set environment operation
"""
import logging
import time
from ..utils import CommandBuilder

logger = logging.getLogger(__name__)

def set_environment_op(params: dict, rcon, context: dict) -> dict:
    """Set world environment (weather, time, difficulty)
    
    Args:
        params: {weather, time, time_value, difficulty}
        rcon: RconClient
        context: Execution context
        
    Returns:
        {success, changes, responses, time_ms}
    """
    try:
        start_time = time.time()
        
        commands = []
        changes = {}
        
        # Weather
        if 'weather' in params:
            weather = params['weather']
            commands.append(CommandBuilder.weather(weather))
            changes['weather'] = weather
        
        # Time
        if 'time' in params:
            time_preset = params['time']
            commands.append(CommandBuilder.time_set(preset=time_preset))
            changes['time'] = time_preset
        elif 'time_value' in params:
            time_val = params['time_value']
            commands.append(CommandBuilder.time_set(value=time_val))
            changes['time_value'] = time_val
        
        # Difficulty
        if 'difficulty' in params:
            difficulty = params['difficulty']
            commands.append(CommandBuilder.difficulty(difficulty))
            changes['difficulty'] = difficulty
        
        if not commands:
            return {
                "success": False,
                "error": "At least one environment parameter required (weather, time, difficulty)"
            }
        
        # Execute commands
        logger.info(f"Setting environment: {changes}")
        results = rcon.execute_batch(commands, delay_ms=100)
        
        # Collect responses
        responses = [r['response'] for r in results if r['success']]
        failed_count = sum(1 for r in results if not r['success'])
        
        elapsed = (time.time() - start_time) * 1000
        
        warnings = []
        if failed_count > 0:
            warnings.append(f"{failed_count} commands failed")
        
        return {
            "success": len(responses) > 0,
            "changes": changes,
            "responses": responses,
            "failed_count": failed_count,
            "time_ms": elapsed,
            "warnings": warnings
        }
    
    except Exception as e:
        logger.error(f"Set environment failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
