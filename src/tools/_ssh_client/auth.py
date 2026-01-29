"""Authentication helpers for SSH Client."""
from __future__ import annotations
from typing import Optional
from pathlib import Path
import paramiko


def create_ssh_client(
    host: str,
    port: int,
    username: str,
    auth_type: str,
    password: Optional[str] = None,
    key_file: Optional[str] = None,
    key_passphrase: Optional[str] = None,
    timeout: int = 30,
    verify_host_key: str = "auto_add"
) -> paramiko.SSHClient:
    """Create and connect SSH client.
    
    Args:
        host: Server hostname or IP
        port: SSH port
        username: Username
        auth_type: Authentication type (password, key, agent)
        password: Password (if auth_type=password)
        key_file: Path to SSH key (if auth_type=key)
        key_passphrase: Passphrase for key (optional)
        timeout: Connection timeout in seconds
        verify_host_key: Host key verification (strict, auto_add, disabled)
        
    Returns:
        Connected SSHClient instance
        
    Raises:
        paramiko.AuthenticationException: Authentication failed
        paramiko.SSHException: SSH error
        Exception: Other errors
    """
    client = paramiko.SSHClient()
    
    # Host key policy
    if verify_host_key == "disabled":
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
    elif verify_host_key == "auto_add":
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:  # strict
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
    
    # Connect based on auth_type
    if auth_type == "password":
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False
        )
    
    elif auth_type == "key":
        # Load key
        key_path = Path(key_file).expanduser()
        
        # Try to determine key type and load (removed DSS as it's deprecated)
        pkey = None
        key_types = [
            paramiko.RSAKey,
            paramiko.Ed25519Key,
            paramiko.ECDSAKey
        ]
        
        last_error = None
        for key_class in key_types:
            try:
                pkey = key_class.from_private_key_file(
                    str(key_path),
                    password=key_passphrase
                )
                break
            except Exception as e:
                last_error = e
                continue
        
        if pkey is None:
            raise ValueError(f"Could not load SSH key: {last_error}")
        
        client.connect(
            hostname=host,
            port=port,
            username=username,
            pkey=pkey,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False
        )
    
    elif auth_type == "agent":
        client.connect(
            hostname=host,
            port=port,
            username=username,
            timeout=timeout,
            allow_agent=True,
            look_for_keys=True
        )
    
    else:
        raise ValueError(f"Invalid auth_type: {auth_type}")
    
    return client


def mask_password(password: Optional[str]) -> str:
    """Mask password for logging.
    
    Args:
        password: Password to mask
        
    Returns:
        Masked password (e.g., "****")
    """
    if not password:
        return ""
    
    return "****"
