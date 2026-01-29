"""
SSH Client Tool - Universal SSH/SFTP client

Supports command execution, file transfers (upload/download), and server management
with authentication via password, SSH key, or SSH agent.

Example - Execute command:
  {
    "tool": "ssh_client",
    "params": {
      "operation": "exec",
      "host": "188.245.151.223",
      "username": "root",
      "auth_type": "password",
      "password": "...",
      "command": "ls -lah /var/www"
    }
  }

Example - Upload file:
  {
    "tool": "ssh_client",
    "params": {
      "operation": "upload",
      "host": "188.245.151.223",
      "username": "root",
      "auth_type": "key",
      "key_file": "~/.ssh/id_rsa",
      "local_path": "files/scripts/script.py",
      "remote_path": "/root/script.py"
    }
  }

Example - Download file:
  {
    "tool": "ssh_client",
    "params": {
      "operation": "download",
      "host": "188.245.151.223",
      "username": "root",
      "auth_type": "password",
      "password": "...",
      "remote_path": "/var/log/app.log",
      "local_path": "files/logs/app.log"
    }
  }
"""
from __future__ import annotations
from typing import Dict, Any
import json
import os

from ._ssh_client.api import route_operation
from ._ssh_client import spec as _spec


def run(**params) -> Dict[str, Any]:
    """Execute SSH operation.
    
    Args:
        **params: Operation parameters (operation, host, username, auth, etc.)
        
    Returns:
        Operation result (stdout, exit_code, file info, etc.)
    """
    # Extract operation
    operation = params.get("operation")
    
    # Validate required params
    if not operation:
        return {"error": "Parameter 'operation' is required"}
    
    # Normalize operation
    operation = str(operation).strip().lower()
    
    # Validate operation
    valid_operations = ["exec", "upload", "download", "status"]
    if operation not in valid_operations:
        return {
            "error": f"Invalid operation '{operation}'. Must be one of: {', '.join(valid_operations)}"
        }
    
    # Validate required fields
    if not params.get("host"):
        return {"error": "Parameter 'host' is required"}
    
    if not params.get("username"):
        return {"error": "Parameter 'username' is required"}
    
    if not params.get("auth_type"):
        return {"error": "Parameter 'auth_type' is required"}
    
    # Route to handler (pass all params, route_operation will extract what it needs)
    return route_operation(**params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
