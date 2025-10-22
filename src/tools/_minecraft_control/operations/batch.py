"""
Batch commands operation
"""
import logging
import time

logger = logging.getLogger(__name__)

def batch_commands_op(params: dict, rcon, context: dict) -> dict:
    """Execute batch of commands
    
    Args:
        params: {commands: list[str], delay_ms: int}
        rcon: RconClient
        context: Execution context
        
    Returns:
        {success, executed_count, failed_count, results, time_ms, warnings}
    """
    commands = params.get('commands', [])
    if not commands:
        return {
            "success": False,
            "error": "commands array required"
        }
    
    try:
        start_time = time.time()
        
        delay_ms = params.get('delay_ms', 50)
        limit = params.get('limit', 50)
        
        logger.info(f"Executing batch of {len(commands)} commands with {delay_ms}ms delay")
        
        # Execute batch
        results = rcon.execute_batch(commands, delay_ms=delay_ms)
        
        # Count successes/failures
        executed = sum(1 for r in results if r['success'])
        failed = len(commands) - executed
        
        elapsed = (time.time() - start_time) * 1000
        
        warnings = []
        if failed > 0:
            warnings.append(f"{failed} commands failed")
        
        # Truncate results output (LLM DEV GUIDE: output size limit)
        truncated = len(results) > limit
        returned_results = results[:limit] if truncated else results
        
        if truncated:
            warnings.append(f"Results truncated ({len(results)} total, showing {limit})")
        
        return {
            "success": executed > 0,
            "executed_count": executed,
            "failed_count": failed,
            "total_count": len(commands),
            "results": returned_results,
            "truncated": truncated,
            "time_ms": elapsed,
            "warnings": warnings
        }
    
    except Exception as e:
        logger.error(f"Batch commands failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "commands_count": len(commands)
        }
