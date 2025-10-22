"""
Execute raw command operation
"""
import logging
import time

logger = logging.getLogger(__name__)

def execute_command_op(params: dict, rcon, context: dict) -> dict:
    """Execute raw Minecraft command
    
    Args:
        params: {command: str, player_name: str}
        rcon: RconClient instance
        context: Execution context
        
    Returns:
        {success, command, response, executed_at}
    """
    command = params.get('command', '')
    if not command:
        return {
            "success": False,
            "error": "command parameter required",
            "command": ""
        }
    
    try:
        start_time = time.time()
        response = rcon.execute(command)
        elapsed = (time.time() - start_time) * 1000
        
        logger.info(f"Command executed: /{command}")
        
        return {
            "success": True,
            "command": command,
            "response": response,
            "executed_at": time.time(),
            "time_ms": elapsed
        }
    
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": command
        }
