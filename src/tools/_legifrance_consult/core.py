"""Core execution logic via SSH."""
from typing import Dict, Any
import json
import logging
from .utils import get_ssh_config, build_cli_command

LOG = logging.getLogger(__name__)

def execute_ssh(operation: str, **params) -> Dict[str, Any]:
    cmd = build_cli_command(operation, **params)
    config = get_ssh_config()
    
    try:
        # Import dynamic
        import sys
        import os
        # Add root to path if needed (dirty fix for tool import)
        root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        if root_path not in sys.path:
            sys.path.insert(0, root_path)
            
        try:
            from src.tools.ssh_client import run as ssh_run
        except ImportError:
            # Fallback
            from ssh_client import run as ssh_run

        result = ssh_run(
            operation="exec",
            host=config["host"].split("@")[1],
            username=config["host"].split("@")[0],
            auth_type="key",
            key_file=config["key_path"],
            key_passphrase=config["key_passphrase"],
            command=cmd,
            timeout=120
        )
        
        if "error" in result:
            return result
            
        try:
            return json.loads(result.get("stdout", "{}"))
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "raw": result.get("stdout")}
            
    except Exception as e:
        return {"error": str(e)}
