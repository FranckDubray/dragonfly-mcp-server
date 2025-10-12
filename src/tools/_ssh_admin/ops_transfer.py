"""
File transfer operations: upload, download (SCP).
"""
from __future__ import annotations
from typing import Dict, Any
import time
import os

try:
    from .client import create_ssh_client
    from .utils import resolve_local_path
    from .logger import log_ssh_operation
except Exception:
    from src.tools._ssh_admin.client import create_ssh_client
    from src.tools._ssh_admin.utils import resolve_local_path
    from src.tools._ssh_admin.logger import log_ssh_operation

def op_upload(params: Dict[str, Any]) -> Dict[str, Any]:
    """Upload file from local to remote server (SCP)."""
    profile_name = params["profile"]
    local_path_str = params.get("local_path")
    remote_path = params.get("remote_path")
    timeout = params.get("timeout", 60)
    
    if not local_path_str:
        raise ValueError("'local_path' parameter required for 'upload' operation")
    if not remote_path:
        raise ValueError("'remote_path' parameter required for 'upload' operation")
    
    # Resolve and validate local path
    local_path = resolve_local_path(local_path_str)
    
    if not local_path.exists():
        raise FileNotFoundError(f"Local file not found: {local_path_str}")
    
    if not local_path.is_file():
        raise ValueError(f"Local path is not a file: {local_path_str}")
    
    start_time = time.time()
    
    try:
        client = create_ssh_client(profile_name)
        
        try:
            # Open SFTP session
            sftp = client.open_sftp()
            sftp.get_channel().settimeout(timeout)
            
            # Upload file
            sftp.put(str(local_path), remote_path)
            
            # Get file stats
            local_size = local_path.stat().st_size
            remote_stat = sftp.stat(remote_path)
            remote_size = remote_stat.st_size
            
            sftp.close()
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Verify sizes match
            if local_size != remote_size:
                raise RuntimeError(
                    f"Size mismatch: local={local_size} bytes, remote={remote_size} bytes"
                )
            
            # Log success
            log_ssh_operation(
                profile=profile_name,
                operation="upload",
                local_path=local_path_str,
                remote_path=remote_path,
                duration_ms=duration_ms,
                success=True,
                output_size_bytes=local_size
            )
            
            return {
                "status": "ok",
                "operation": "upload",
                "local_path": local_path_str,
                "remote_path": remote_path,
                "size_bytes": local_size,
                "size_mb": round(local_size / (1024 * 1024), 2),
                "duration_ms": duration_ms,
                "speed_mbps": round((local_size / (1024 * 1024)) / (duration_ms / 1000), 2) if duration_ms > 0 else 0
            }
        
        finally:
            client.close()
    
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log failure
        log_ssh_operation(
            profile=profile_name,
            operation="upload",
            local_path=local_path_str,
            remote_path=remote_path,
            duration_ms=duration_ms,
            success=False,
            error_message=str(e)
        )
        
        raise RuntimeError(f"Upload failed: {e}")

def op_download(params: Dict[str, Any]) -> Dict[str, Any]:
    """Download file from remote server to local (SCP)."""
    profile_name = params["profile"]
    remote_path = params.get("remote_path")
    local_path_str = params.get("local_path")
    timeout = params.get("timeout", 60)
    
    if not remote_path:
        raise ValueError("'remote_path' parameter required for 'download' operation")
    if not local_path_str:
        raise ValueError("'local_path' parameter required for 'download' operation")
    
    # Resolve local path
    local_path = resolve_local_path(local_path_str)
    
    # Create parent directories if needed
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    
    try:
        client = create_ssh_client(profile_name)
        
        try:
            # Open SFTP session
            sftp = client.open_sftp()
            sftp.get_channel().settimeout(timeout)
            
            # Check remote file exists
            try:
                remote_stat = sftp.stat(remote_path)
                remote_size = remote_stat.st_size
            except FileNotFoundError:
                raise FileNotFoundError(f"Remote file not found: {remote_path}")
            
            # Download file
            sftp.get(remote_path, str(local_path))
            
            sftp.close()
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Verify local file
            local_size = local_path.stat().st_size
            
            if local_size != remote_size:
                raise RuntimeError(
                    f"Size mismatch: remote={remote_size} bytes, local={local_size} bytes"
                )
            
            # Log success
            log_ssh_operation(
                profile=profile_name,
                operation="download",
                remote_path=remote_path,
                local_path=local_path_str,
                duration_ms=duration_ms,
                success=True,
                output_size_bytes=local_size
            )
            
            return {
                "status": "ok",
                "operation": "download",
                "remote_path": remote_path,
                "local_path": local_path_str,
                "local_path_absolute": str(local_path.resolve()),
                "size_bytes": local_size,
                "size_mb": round(local_size / (1024 * 1024), 2),
                "duration_ms": duration_ms,
                "speed_mbps": round((local_size / (1024 * 1024)) / (duration_ms / 1000), 2) if duration_ms > 0 else 0
            }
        
        finally:
            client.close()
    
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log failure
        log_ssh_operation(
            profile=profile_name,
            operation="download",
            remote_path=remote_path,
            local_path=local_path_str,
            duration_ms=duration_ms,
            success=False,
            error_message=str(e)
        )
        
        raise RuntimeError(f"Download failed: {e}")
