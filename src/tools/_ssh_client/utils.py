"""Utility functions for SSH Client."""
from __future__ import annotations
from typing import Dict, Any, Optional


def build_command_with_env(command: str, env: Dict[str, str]) -> str:
    """Build command with environment variables.
    
    Args:
        command: Base command
        env: Environment variables dict
        
    Returns:
        Command with env vars prepended
    """
    if not env:
        return command
    
    # Build env string: KEY1=value1 KEY2=value2 command
    env_parts = []
    for key, value in env.items():
        # Escape single quotes in value
        value_escaped = value.replace("'", "'\\''")
        env_parts.append(f"{key}='{value_escaped}'")
    
    env_string = " ".join(env_parts)
    return f"{env_string} {command}"


def parse_exit_code(exit_code: int) -> Dict[str, Any]:
    """Parse exit code and return status info.
    
    Args:
        exit_code: Command exit code
        
    Returns:
        Dict with status info
    """
    status = {
        "exit_code": exit_code,
        "success": exit_code == 0
    }
    
    # Add human-readable status
    if exit_code == 0:
        status["message"] = "Success"
    elif exit_code == 1:
        status["message"] = "General error"
    elif exit_code == 2:
        status["message"] = "Misuse of shell command"
    elif exit_code == 126:
        status["message"] = "Command cannot execute (permission denied)"
    elif exit_code == 127:
        status["message"] = "Command not found"
    elif exit_code == 130:
        status["message"] = "Terminated by Ctrl+C"
    elif exit_code == 137:
        status["message"] = "Killed (SIGKILL)"
    elif exit_code == 143:
        status["message"] = "Terminated (SIGTERM)"
    else:
        status["message"] = f"Exited with code {exit_code}"
    
    return status


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"


def truncate_output(output: str, max_length: int = 100_000) -> tuple[str, bool]:
    """Truncate output if too large.
    
    Args:
        output: Output string
        max_length: Maximum length before truncation
        
    Returns:
        Tuple of (truncated_output, was_truncated)
    """
    if len(output) <= max_length:
        return output, False
    
    # Keep first 80% and last 10%
    keep_start = int(max_length * 0.8)
    keep_end = int(max_length * 0.1)
    
    truncated = (
        output[:keep_start] +
        f"\n\n... [TRUNCATED {len(output) - max_length} bytes] ...\n\n" +
        output[-keep_end:]
    )
    
    return truncated, True
