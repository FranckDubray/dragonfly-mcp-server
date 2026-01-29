"""SFTP file transfer operations for SSH Client."""
from __future__ import annotations
from typing import Dict, Any
import logging
import time
import os
from pathlib import Path
import paramiko

from .validators import (
    validate_host,
    validate_port,
    validate_timeout,
    validate_path,
    validate_auth_params
)
from .auth import create_ssh_client, mask_password

LOG = logging.getLogger(__name__)


def upload_file(**params) -> Dict[str, Any]:
    """Upload file to remote server via SFTP.
    
    Args:
        **params: Upload parameters (host, local_path, remote_path, etc.)
        
    Returns:
        Upload result with file info
    """
    # Extract params
    host = params.get("host")
    port = params.get("port")
    username = params.get("username")
    auth_type = params.get("auth_type")
    password = params.get("password")
    key_file = params.get("key_file")
    key_passphrase = params.get("key_passphrase")
    local_path = params.get("local_path")
    remote_path = params.get("remote_path")
    create_dirs = params.get("create_dirs", True)
    timeout = params.get("timeout")
    verify_host_key = params.get("verify_host_key", "auto_add")
    
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
    
    # Validate paths
    if not local_path:
        return {"error": "local_path is required", "error_type": "validation"}
    
    if not remote_path:
        return {"error": "remote_path is required", "error_type": "validation"}
    
    valid, local_path_norm, error = validate_path(local_path, "local")
    if not valid:
        LOG.warning(f"❌ Invalid local_path: {error}")
        return {"error": error, "error_type": "validation"}
    
    valid, remote_path_norm, error = validate_path(remote_path, "remote")
    if not valid:
        LOG.warning(f"❌ Invalid remote_path: {error}")
        return {"error": error, "error_type": "validation"}
    
    # Check local file exists
    local_file = Path(local_path_norm)
    if not local_file.exists():
        return {"error": f"Local file not found: {local_path}", "error_type": "file_not_found"}
    
    if not local_file.is_file():
        return {"error": f"Local path is not a file: {local_path}", "error_type": "validation"}
    
    # Validate auth
    valid, error = validate_auth_params(auth_type, password, key_file)
    if not valid:
        LOG.warning(f"❌ Invalid auth: {error}")
        return {"error": error, "error_type": "authentication"}
    
    # Get file size
    file_size = local_file.stat().st_size
    
    LOG.info(f"📤 Uploading: {local_path} → {username}@{host}:{remote_path_norm} ({file_size} bytes)")
    
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
        
        # Open SFTP session
        sftp = client.open_sftp()
        
        # Create remote directories if needed
        if create_dirs:
            remote_dir = os.path.dirname(remote_path_norm)
            if remote_dir:
                try:
                    _mkdir_p(sftp, remote_dir)
                except Exception as e:
                    LOG.warning(f"⚠️ Could not create remote directories: {e}")
        
        # Upload file
        sftp.put(str(local_file), remote_path_norm)
        
        # Close SFTP and SSH
        sftp.close()
        client.close()
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        LOG.info(f"✅ Upload successful ({file_size} bytes, {duration_ms}ms)")
        
        return {
            "operation": "upload",
            "local_path": local_path,
            "remote_path": remote_path_norm,
            "size_bytes": file_size,
            "transferred": True,
            "duration_ms": duration_ms,
            "host": host,
            "username": username
        }
        
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
    
    except IOError as e:
        LOG.error(f"💾 File error: {e}")
        return {
            "error": f"File error: {str(e)}",
            "error_type": "file",
            "local_path": local_path,
            "remote_path": remote_path_norm
        }
    
    except Exception as e:
        LOG.error(f"💥 Unexpected error: {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "error_type": "unknown",
            "host": host
        }


def download_file(**params) -> Dict[str, Any]:
    """Download file from remote server via SFTP.
    
    Args:
        **params: Download parameters (host, remote_path, local_path, etc.)
        
    Returns:
        Download result with file info
    """
    # Extract params
    host = params.get("host")
    port = params.get("port")
    username = params.get("username")
    auth_type = params.get("auth_type")
    password = params.get("password")
    key_file = params.get("key_file")
    key_passphrase = params.get("key_passphrase")
    remote_path = params.get("remote_path")
    local_path = params.get("local_path")
    timeout = params.get("timeout")
    verify_host_key = params.get("verify_host_key", "auto_add")
    
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
    
    # Validate paths
    if not remote_path:
        return {"error": "remote_path is required", "error_type": "validation"}
    
    if not local_path:
        return {"error": "local_path is required", "error_type": "validation"}
    
    valid, local_path_norm, error = validate_path(local_path, "local")
    if not valid:
        LOG.warning(f"❌ Invalid local_path: {error}")
        return {"error": error, "error_type": "validation"}
    
    valid, remote_path_norm, error = validate_path(remote_path, "remote")
    if not valid:
        LOG.warning(f"❌ Invalid remote_path: {error}")
        return {"error": error, "error_type": "validation"}
    
    # Validate auth
    valid, error = validate_auth_params(auth_type, password, key_file)
    if not valid:
        LOG.warning(f"❌ Invalid auth: {error}")
        return {"error": error, "error_type": "authentication"}
    
    LOG.info(f"📥 Downloading: {username}@{host}:{remote_path_norm} → {local_path}")
    
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
        
        # Open SFTP session
        sftp = client.open_sftp()
        
        # Create local directories if needed
        local_file = Path(local_path_norm)
        local_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Download file
        sftp.get(remote_path_norm, str(local_file))
        
        # Get file size
        file_size = local_file.stat().st_size
        
        # Close SFTP and SSH
        sftp.close()
        client.close()
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        LOG.info(f"✅ Download successful ({file_size} bytes, {duration_ms}ms)")
        
        return {
            "operation": "download",
            "remote_path": remote_path_norm,
            "local_path": str(local_file),
            "size_bytes": file_size,
            "transferred": True,
            "duration_ms": duration_ms,
            "host": host,
            "username": username
        }
        
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
    
    except IOError as e:
        LOG.error(f"💾 File error: {e}")
        return {
            "error": f"File error: {str(e)}",
            "error_type": "file",
            "remote_path": remote_path_norm,
            "local_path": local_path
        }
    
    except Exception as e:
        LOG.error(f"💥 Unexpected error: {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "error_type": "unknown",
            "host": host
        }


def _mkdir_p(sftp, remote_directory):
    """Create remote directory recursively (like mkdir -p).
    
    Args:
        sftp: SFTP client
        remote_directory: Directory to create
    """
    if remote_directory == '/':
        return
    
    if remote_directory == '':
        return
    
    try:
        sftp.stat(remote_directory)
    except IOError:
        # Directory doesn't exist, create parent first
        dirname, basename = os.path.split(remote_directory.rstrip('/'))
        _mkdir_p(sftp, dirname)
        sftp.mkdir(remote_directory)
