"""
Main router for SSH operations.
"""
from __future__ import annotations
from typing import Any, Dict

try:
    from .ops_basic import op_connect, op_exec, op_exec_file
    from .ops_transfer import op_upload, op_download
except Exception:
    from src.tools._ssh_admin.ops_basic import op_connect, op_exec, op_exec_file
    from src.tools._ssh_admin.ops_transfer import op_upload, op_download

def run_operation(**params) -> Any:
    """
    Route operation to appropriate handler.
    
    Operations:
    - connect: test SSH connection
    - exec: execute command/script inline
    - exec_file: execute local bash script on remote server
    - upload: SCP upload
    - download: SCP download
    """
    operation = params.get("operation")
    
    if not operation:
        raise ValueError("'operation' parameter required")
    
    # Route to handler
    if operation == "connect":
        return op_connect(params)
    elif operation == "exec":
        return op_exec(params)
    elif operation == "exec_file":
        return op_exec_file(params)
    elif operation == "upload":
        return op_upload(params)
    elif operation == "download":
        return op_download(params)
    else:
        raise ValueError(
            f"Invalid operation: {operation}\n"
            f"Valid operations: connect, exec, exec_file, upload, download"
        )
