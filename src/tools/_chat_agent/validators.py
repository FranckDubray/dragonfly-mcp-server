"""Input validation for chat_agent parameters."""

from typing import Any, Dict, List, Optional


def validate_params(
    message: str,
    model: str,
    tools: List[str],
    thread_id: Optional[str],
    output_mode: str,
    max_iterations: int,
    timeout: int,
    temperature: float,
) -> Optional[Dict[str, Any]]:
    """Validate all input parameters.
    
    Returns:
        None if valid, error dict if invalid
    """
    # Message
    if not message or not isinstance(message, str):
        return {"error": "message is required and must be a non-empty string"}
    
    if len(message) > 100000:
        return {"error": f"message too long ({len(message)} chars, max: 100000)"}
    
    # Model
    if not model or not isinstance(model, str):
        return {"error": "model is required and must be a string"}
    
    # Tools
    if not isinstance(tools, list):
        return {"error": "tools must be a list"}
    
    if len(tools) > 20:
        return {"error": f"too many tools ({len(tools)}, max: 20)"}
    
    for tool in tools:
        if not isinstance(tool, str) or not tool.strip():
            return {"error": f"invalid tool name: {tool}"}
    
    # Thread ID
    if thread_id is not None and (not isinstance(thread_id, str) or not thread_id.strip()):
        return {"error": "thread_id must be a non-empty string if provided"}
    
    # Output mode
    valid_modes = ["minimal", "intermediate", "debug"]
    if output_mode not in valid_modes:
        return {"error": f"output_mode must be one of {valid_modes}, got: {output_mode}"}
    
    # Max iterations
    if not isinstance(max_iterations, int) or max_iterations < 1 or max_iterations > 50:
        return {"error": f"max_iterations must be between 1 and 50, got: {max_iterations}"}
    
    # Timeout
    if not isinstance(timeout, int) or timeout < 10 or timeout > 600:
        return {"error": f"timeout must be between 10 and 600 seconds, got: {timeout}"}
    
    # Temperature
    if not isinstance(temperature, (int, float)) or temperature < 0.0 or temperature > 2.0:
        return {"error": f"temperature must be between 0.0 and 2.0, got: {temperature}"}
    
    return None


def validate_token_env(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Validate AI_PORTAL_TOKEN environment variable.
    
    Returns:
        None if valid, error dict if invalid
    """
    if not token or not isinstance(token, str):
        return {
            "error": "AI_PORTAL_TOKEN environment variable is required",
            "hint": "Set AI_PORTAL_TOKEN in your .env file"
        }
    
    if len(token) < 10:
        return {"error": "AI_PORTAL_TOKEN appears invalid (too short)"}
    
    return None
