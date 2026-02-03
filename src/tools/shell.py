"""
Shell command executor.
Execute shell commands (bash/sh/python3) with timeout and output capture.
"""
import subprocess
import os
import json
from typing import Any, Dict


def run(command: str, cwd: str = None, timeout: int = 30, capture_output: bool = True, shell: str = "bash", **kwargs) -> Dict[str, Any]:
    """
    Execute a shell commann    
    Args:
        command: Shell command to execute
        cwd: Working directory (default: project root)
        timeout: Timeout in seconds (max: 300)
        capture_output: Capture stdout/stderr
       : Shell to use (bash/sh/python3/node)
    
    Returns:
        {
         ess": bool,
            "stdout": str,
            "stderr": str,
            "returncode": int,
            "command": str,
            "cwd": str
        }
    """
    try:
        # Determine working directory
        if cwd is None:
            # Default to project root
            cwd = os.getcwd()
        else:
            # Resolve relative to project root
            if not os.path.isabs(cwd):
                cwd = os.path.join(os.getcwd(), cwd)
        
        # Validate cwd exists
        if not os.path.exists(cwd):
            return {
                "success": False,
                "error": f"Working directory does not exist: {cwd}",
                "command": command
            }
        
        # Validate timeout
        timeout = min(max(1, timeout), 300)
        
        # Select shell
        if shell == "python3":
            cmd = ["python3", "-c", command]
        elif shell == "node":
            cmd = ["node", "-e", command]
        elif shell == "sh":
            cmd = ["sh", "-c", command]
        else:  # bash (default)
            cmd = ["bash", "-c", command]
        
        # Execute
        if capture_output:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": command,
                "cwd": cwd
            }
        else:
            # No capture (for interactive commands)
            result = subprocess.run(
                cmd,
                cwd=cwd,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "command": command,
                "cwd": cwd,
                "note": "Output not captured (capture_output=false)"
            }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Command timed out after {timeout} seconds",
            "command": command,
            "cwd": cwd
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": command,
            "cwd": cwd
        }


def spec() -> Dict[str, Any]:
    """Load tool specification."""
    import json
    import os
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'shell.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
