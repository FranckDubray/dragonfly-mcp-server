"""
Basic SSH operations: connect, exec, exec_file.
"""
from __future__ import annotations
from typing import Dict, Any, Tuple
import time
import shlex

try:
    from .client import create_ssh_client
    from .utils import truncate_output, resolve_local_path
    from .logger import log_ssh_operation
    from .profiles import get_profile
except Exception:
    from src.tools._ssh_admin.client import create_ssh_client
    from src.tools._ssh_admin.utils import truncate_output, resolve_local_path
    from src.tools._ssh_admin.logger import log_ssh_operation
    from src.tools._ssh_admin.profiles import get_profile


def _execute_bash_script(
    profile_name: str,
    script_content: str,
    timeout: int,
    command_label: str
) -> Tuple[str, str, int, int, int]:
    """
    Execute bash script on remote server.
    
    Returns: (stdout, stderr, exit_code, duration_ms, output_size)
    
    Raises: RuntimeError on execution failure
    """
    start_time = time.time()
    client = create_ssh_client(profile_name)
    
    try:
        # Execute via bash -s (supports multi-line scripts)
        stdin, stdout, stderr = client.exec_command("bash -s", timeout=timeout)
        stdin.write(script_content)
        stdin.close()
        
        # Read output
        stdout_text = stdout.read().decode("utf-8", errors="replace")
        stderr_text = stderr.read().decode("utf-8", errors="replace")
        exit_code = stdout.channel.recv_exit_status()
        
        duration_ms = int((time.time() - start_time) * 1000)
        output_size = len(stdout_text.encode('utf-8')) + len(stderr_text.encode('utf-8'))
        
        return stdout_text, stderr_text, exit_code, duration_ms, output_size
    
    finally:
        client.close()


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
        
        # Get server banner with timeout protection
        ssh_version = "unknown"
        try:
            banner = transport.get_banner()
            if banner:
                ssh_version = banner.decode('utf-8', errors='ignore').strip()
        except Exception:
            # Banner read failed, but connection OK
            pass
        
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
    
    try:
        # Execute using common function
        stdout_text, stderr_text, exit_code, duration_ms, output_size = _execute_bash_script(
            profile_name, command, timeout, command[:200]
        )
        
        # Truncate output if too large (LLM_DEV_GUIDE compliance)
        stdout_truncated, stdout_was_truncated = truncate_output(stdout_text, max_bytes=10240)
        stderr_truncated, stderr_was_truncated = truncate_output(stderr_text, max_bytes=10240)
        
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
    
    except Exception as e:
        duration_ms = int((time.time() - time.time()) * 1000)
        
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


def op_exec_file(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute local bash script on remote server."""
    profile_name = params["profile"]
    script_path_str = params.get("script_path")
    args = params.get("args", [])
    timeout = params.get("timeout", 30)
    
    if not script_path_str:
        raise ValueError("'script_path' parameter required for 'exec_file' operation")
    
    # Resolve and validate local script path
    script_path = resolve_local_path(script_path_str)
    
    if not script_path.exists():
        raise FileNotFoundError(
            f"Script not found: {script_path_str}\n"
            f"Full path: {script_path}\n"
            f"Make sure the script exists and path is relative to project root."
        )
    
    if not script_path.is_file():
        raise ValueError(f"Script path is not a file: {script_path_str}")
    
    # Read script content
    try:
        script_content = script_path.read_text(encoding='utf-8')
    except Exception as e:
        raise ValueError(f"Failed to read script {script_path_str}: {e}")
    
    # Validate script content
    if not script_content.strip():
        raise ValueError(f"Script is empty: {script_path_str}")
    
    # Validate shebang (warning only)
    warnings = []
    if not script_content.startswith("#!"):
        warnings.append("Script has no shebang. Recommended: #!/bin/bash")
    elif not script_content.startswith("#!/bin/bash") and not script_content.startswith("#!/usr/bin/env bash"):
        warnings.append(f"Non-bash shebang detected. This tool executes via 'bash -s'.")
    
    # Check for set -e (best practice)
    if "set -e" not in script_content.split('\n')[:10]:
        warnings.append("Script missing 'set -e'. Errors may be ignored.")
    
    try:
        # Build command with args using shlex.quote (shell-safe)
        if args:
            escaped_args = [shlex.quote(str(arg)) for arg in args]
            # Prepend set -- to set positional parameters
            script_with_args = f"set -- {' '.join(escaped_args)}\n{script_content}"
        else:
            script_with_args = script_content
        
        # Execute using common function
        stdout_text, stderr_text, exit_code, duration_ms, output_size = _execute_bash_script(
            profile_name, script_with_args, timeout, f"[script: {script_path_str}]"
        )
        
        # Truncate output if too large
        stdout_truncated, stdout_was_truncated = truncate_output(stdout_text, max_bytes=10240)
        stderr_truncated, stderr_was_truncated = truncate_output(stderr_text, max_bytes=10240)
        
        # Log success
        log_ssh_operation(
            profile=profile_name,
            operation="exec_file",
            command=f"[script: {script_path_str}]",
            duration_ms=duration_ms,
            success=(exit_code == 0),
            exit_code=exit_code,
            output_size_bytes=output_size
        )
        
        result = {
            "status": "ok",
            "script_path": script_path_str,
            "script_size_bytes": len(script_content.encode('utf-8')),
            "args": args,
            "stdout": stdout_truncated,
            "stderr": stderr_truncated,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "output_size_bytes": output_size
        }
        
        # Add warnings
        if warnings:
            result["warnings"] = warnings
        
        # Add truncation warnings
        if stdout_was_truncated or stderr_was_truncated:
            result["truncated"] = True
            if "warnings" not in result:
                result["warnings"] = []
            result["warnings"].append("Output truncated to 10KB (LLM context protection)")
        
        return result
    
    except Exception as e:
        duration_ms = int((time.time() - time.time()) * 1000)
        
        # Log failure
        log_ssh_operation(
            profile=profile_name,
            operation="exec_file",
            command=f"[script: {script_path_str}]",
            duration_ms=duration_ms,
            success=False,
            error_message=str(e)
        )
        
        raise RuntimeError(f"Script execution failed: {e}")
