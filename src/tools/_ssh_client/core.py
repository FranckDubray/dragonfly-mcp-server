"""Core business logic for SSH Client."""
from __future__ import annotations
from typing import Dict, Any, Optional
import logging
import time
import paramiko

from .validators import (
    validate_host,
    validate_port,
    validate_timeout,
    validate_command,
    validate_auth_params
)
from .auth import create_ssh_client, mask_password
from .utils import build_command_with_env, parse_exit_code

LOG = logging.getLogger(__name__)


def execute_command(**params) -> Dict[str, Any]:
    """Execute command on remote server.
    
    Args:
        **params: Command parameters (host, username, command, etc.)
        
    Returns:
        Command result with stdout, stderr, exit_code
    """
    # Extract params
    host = params.get("host")
    port = params.get("port")
    username = params.get("username")
    auth_type = params.get("auth_type")
    password = params.get("password")
    key_file = params.get("key_file")
    key_passphrase = params.get("key_passphrase")
    command = params.get("command")
    cwd = params.get("cwd")
    sudo = params.get("sudo", False)
    sudo_password = params.get("sudo_password")
    timeout = params.get("timeout")
    verify_host_key = params.get("verify_host_key", "auto_add")
    env = params.get("env", {})
    
    # Validate host
    valid, error = validate_host(host)
    if not valid:
        LOG.warning(f"❌ Invalid host: {error}")
        return {"error": error, "error_type": "validation"}
    
    # Validate port
    valid, port, error = validate_port(port)
    if not valid:
        LOG.warning(f"❌ Invalid port: {error}")
        return {"error": error, "error_type": "validation"}
    
    # Validate timeout
    valid, timeout, error = validate_timeout(timeout)
    if not valid:
        LOG.warning(f"❌ Invalid timeout: {error}")
        return {"error": error, "error_type": "validation"}
    
    # Validate command
    if not command:
        LOG.warning("❌ Command is required for operation=exec")
        return {"error": "Command is required", "error_type": "validation"}
    
    valid, error = validate_command(command)
    if not valid:
        LOG.warning(f"❌ Invalid command: {error}")
        return {"error": error, "error_type": "validation"}
    
    # Validate auth
    valid, error = validate_auth_params(auth_type, password, key_file)
    if not valid:
        LOG.warning(f"❌ Invalid auth: {error}")
        return {"error": error, "error_type": "authentication"}
    
    # Build full command
    full_command = command
    
    # Add cwd if specified
    if cwd:
        full_command = f"cd {cwd} && {full_command}"
    
    # Add env vars if specified
    if env:
        full_command = build_command_with_env(full_command, env)
    
    # Add sudo if specified
    if sudo:
        if sudo_password:
            # Use sudo -S to read password from stdin
            full_command = f"echo '{sudo_password}' | sudo -S {full_command}"
        else:
            full_command = f"sudo {full_command}"
    
    # Log command execution (mask password)
    password_display = mask_password(password)
    LOG.info(f"🔧 SSH exec: {username}@{host}:{port} (auth={auth_type}, timeout={timeout}s)")
    LOG.info(f"📝 Command: {command}")
    
    start_time = time.time()
    
    try:
        # Create SSH client
        client = create_ssh_client(
            host=host,
            port=port,
            username=username,
            auth_type=auth_type,
            password=password,
            key_file=key_file,
            key_passphrase=key_passphrase,
            timeout=timeout,
            verify_host_key=verify_host_key
        )
        
        # Execute command
        stdin, stdout, stderr = client.exec_command(full_command, timeout=timeout)
        
        # Read output
        stdout_data = stdout.read().decode("utf-8", errors="replace")
        stderr_data = stderr.read().decode("utf-8", errors="replace")
        exit_code = stdout.channel.recv_exit_status()
        
        # Close client
        client.close()
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log result
        if exit_code == 0:
            LOG.info(f"✅ Command succeeded (exit_code={exit_code}, {duration_ms}ms)")
        else:
            LOG.warning(f"⚠️ Command failed (exit_code={exit_code}, {duration_ms}ms)")
        
        # Check for large output
        stdout_len = len(stdout_data)
        stderr_len = len(stderr_data)
        
        if stdout_len > 100_000:
            LOG.warning(f"⚠️ Large stdout: {stdout_len} bytes ({stdout_len / 1024:.1f} KB)")
        
        # Build result
        result = {
            "operation": "exec",
            "exit_code": exit_code,
            "stdout": stdout_data,
            "stderr": stderr_data,
            "duration_ms": duration_ms,
            "host": host,
            "username": username,
            "command": command,
            "truncated": False
        }
        
        # Add truncation warning if needed
        if stdout_len > 100_000:
            result["truncation_warning"] = f"stdout is large: {stdout_len / 1024:.1f} KB"
        
        return result
        
    except paramiko.AuthenticationException as e:
        LOG.error(f"🔒 Authentication failed: {e}")
        return {
            "error": f"Authentication failed: {str(e)}",
            "error_type": "authentication",
            "host": host,
            "username": username
        }
    
    except paramiko.SSHException as e:
        LOG.error(f"❌ SSH error: {e}")
        return {
            "error": f"SSH error: {str(e)}",
            "error_type": "ssh",
            "host": host
        }
    
    except TimeoutError as e:
        LOG.error(f"⏱️ Timeout: {e}")
        return {
            "error": f"Command timed out after {timeout} seconds",
            "error_type": "timeout",
            "host": host,
            "command": command
        }
    
    except Exception as e:
        LOG.error(f"💥 Unexpected error: {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "error_type": "unknown",
            "host": host
        }


def check_status(**params) -> Dict[str, Any]:
    """Check SSH connection status.
    
    Args:
        **params: Connection parameters
        
    Returns:
        Status information
    """
    host = params.get("host")
    port = params.get("port", 22)
    username = params.get("username")
    auth_type = params.get("auth_type")
    password = params.get("password")
    key_file = params.get("key_file")
    key_passphrase = params.get("key_passphrase")
    timeout = params.get("timeout", 30)
    verify_host_key = params.get("verify_host_key", "auto_add")
    
    # Validate
    valid, error = validate_host(host)
    if not valid:
        return {"error": error, "error_type": "validation"}
    
    valid, port, error = validate_port(port)
    if not valid:
        return {"error": error, "error_type": "validation"}
    
    valid, timeout, error = validate_timeout(timeout)
    if not valid:
        return {"error": error, "error_type": "validation"}
    
    valid, error = validate_auth_params(auth_type, password, key_file)
    if not valid:
        return {"error": error, "error_type": "authentication"}
    
    LOG.info(f"🔍 Checking SSH status: {username}@{host}:{port}")
    
    try:
        # Create client
        client = create_ssh_client(
            host=host,
            port=port,
            username=username,
            auth_type=auth_type,
            password=password,
            key_file=key_file,
            key_passphrase=key_passphrase,
            timeout=timeout,
            verify_host_key=verify_host_key
        )
        
        # Get OS info
        stdin, stdout, stderr = client.exec_command("uname -a", timeout=10)
        os_info = stdout.read().decode("utf-8", errors="replace").strip()
        
        # Get uptime
        stdin, stdout, stderr = client.exec_command("uptime -p 2>/dev/null || uptime", timeout=10)
        uptime = stdout.read().decode("utf-8", errors="replace").strip()
        
        # Close client
        client.close()
        
        LOG.info(f"✅ SSH connection successful")
        
        return {
            "operation": "status",
            "connected": True,
            "host": host,
            "port": port,
            "username": username,
            "os_info": os_info,
            "uptime": uptime
        }
        
    except paramiko.AuthenticationException as e:
        LOG.error(f"🔒 Authentication failed: {e}")
        return {
            "error": f"Authentication failed: {str(e)}",
            "error_type": "authentication",
            "connected": False,
            "host": host,
            "username": username
        }
    
    except Exception as e:
        LOG.error(f"❌ Connection failed: {e}")
        return {
            "error": f"Connection failed: {str(e)}",
            "error_type": "connection",
            "connected": False,
            "host": host
        }
