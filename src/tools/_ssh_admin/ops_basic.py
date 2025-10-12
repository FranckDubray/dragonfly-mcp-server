"""
Basic SSH operations: connect, exec.
"""
from __future__ import annotations
from typing import Dict, Any
import time

try:
    from .client import create_ssh_client
    from .utils import truncate_output
    from .logger import log_ssh_operation
    from .profiles import get_profile
except Exception:
    from src.tools._ssh_admin.client import create_ssh_client
    from src.tools._ssh_admin.utils import truncate_output
    from src.tools._ssh_admin.logger import log_ssh_operation
    from src.tools._ssh_admin.profiles import get_profile

def op_connect(params: Dict[str, Any]) -> Dict[str, Any]:
    """Test SSH connection."""
    profile_name = params["profile"]
    start_time = time.time()
    
    try:
        profile = get_profile(profile_name)
        client = create_ssh_client(profile_name)
        
        # Test connection by getting transport
        transport = client.get_transport()
        if not transport or not transport.is_active():
            raise RuntimeError("Transport not active")
        
        # Get server banner
        banner = transport.get_banner()
        ssh_version = banner.decode('utf-8', errors='ignore').strip() if banner else "unknown"
        
        client.close()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log success
        log_ssh_operation(
            profile=profile_name,
            operation="connect",
            duration_ms=duration_ms,
            success=True
        )
        
        return {
            "status": "ok",
            "profile": profile_name,
            "host": profile["host"],
            "port": profile["port"],
            "user": profile["user"],
            "ssh_version": ssh_version,
            "latency_ms": duration_ms
        }
    
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log failure
        log_ssh_operation(
            profile=profile_name,
            operation="connect",
            duration_ms=duration_ms,
            success=False,
            error_message=str(e)
        )
        
        raise RuntimeError(f"Connection failed: {e}")

def op_exec(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute command/script on remote server."""
    profile_name = params["profile"]
    command = params.get("command")
    timeout = params.get("timeout", 30)
    
    if not command:
        raise ValueError("'command' parameter required for 'exec' operation")
    
    start_time = time.time()
    
    try:
        client = create_ssh_client(profile_name)
        
        try:
            # Execute via bash -s (supports multi-line scripts)
            stdin, stdout, stderr = client.exec_command("bash -s", timeout=timeout)
            stdin.write(command)
            stdin.close()
            
            # Read output
            stdout_text = stdout.read().decode("utf-8", errors="replace")
            stderr_text = stderr.read().decode("utf-8", errors="replace")
            exit_code = stdout.channel.recv_exit_status()
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Truncate output if too large (LLM_DEV_GUIDE compliance)
            stdout_truncated, stdout_was_truncated = truncate_output(stdout_text, max_bytes=10240)
            stderr_truncated, stderr_was_truncated = truncate_output(stderr_text, max_bytes=10240)
            
            output_size = len(stdout_text.encode('utf-8')) + len(stderr_text.encode('utf-8'))
            
            # Log success
            log_ssh_operation(
                profile=profile_name,
                operation="exec",
                command=command[:200],  # Truncate long commands in log
                duration_ms=duration_ms,
                success=(exit_code == 0),
                exit_code=exit_code,
                output_size_bytes=output_size
            )
            
            result = {
                "status": "ok",
                "stdout": stdout_truncated,
                "stderr": stderr_truncated,
                "exit_code": exit_code,
                "duration_ms": duration_ms,
                "output_size_bytes": output_size
            }
            
            # Add truncation warnings
            if stdout_was_truncated or stderr_was_truncated:
                result["truncated"] = True
                result["warning"] = "Output truncated to 10KB (LLM context protection)"
            
            return result
        
        finally:
            client.close()
    
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log failure
        log_ssh_operation(
            profile=profile_name,
            operation="exec",
            command=command[:200],
            duration_ms=duration_ms,
            success=False,
            error_message=str(e)
        )
        
        raise RuntimeError(f"Command execution failed: {e}")
