"""
SSH client wrapper (paramiko).
"""
from __future__ import annotations
import paramiko
from typing import Dict, Any

try:
    from .utils import resolve_key_path
    from .profiles import get_profile
except Exception:
    from src.tools._ssh_admin.utils import resolve_key_path
    from src.tools._ssh_admin.profiles import get_profile

def create_ssh_client(profile_name: str) -> paramiko.SSHClient:
    """
    Create and connect SSH client for given profile.
    
    Raises:
        ValueError: Invalid profile or configuration
        FileNotFoundError: SSH key not found
        paramiko.AuthenticationException: Authentication failed
        paramiko.SSHException: Connection failed
    """
    profile = get_profile(profile_name)
    
    # Resolve key path
    key_path = resolve_key_path(profile["key_path"])
    
    # Create client
    client = paramiko.SSHClient()
    
    # Load system host keys
    try:
        client.load_system_host_keys()
    except Exception:
        pass
    
    # Auto-add unknown hosts (with warning)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Load private key
    try:
        # Try different key types
        pkey = None
        key_passphrase = profile.get("passphrase")
        
        # Try RSA
        try:
            pkey = paramiko.RSAKey.from_private_key_file(
                str(key_path),
                password=key_passphrase
            )
        except paramiko.SSHException:
            pass
        
        # Try ED25519
        if pkey is None:
            try:
                pkey = paramiko.Ed25519Key.from_private_key_file(
                    str(key_path),
                    password=key_passphrase
                )
            except paramiko.SSHException:
                pass
        
        # Try ECDSA
        if pkey is None:
            try:
                pkey = paramiko.ECDSAKey.from_private_key_file(
                    str(key_path),
                    password=key_passphrase
                )
            except paramiko.SSHException:
                pass
        
        if pkey is None:
            raise ValueError(
                f"Unable to load SSH key: {profile['key_path']}\n"
                f"Supported formats: RSA, ED25519, ECDSA"
            )
    
    except FileNotFoundError:
        raise FileNotFoundError(f"SSH key not found: {profile['key_path']}")
    except paramiko.PasswordRequiredException:
        raise ValueError(
            f"SSH key {profile['key_path']} requires passphrase.\n"
            f"Add 'passphrase' field to profile or remove passphrase from key."
        )
    
    # Connect
    try:
        timeout = int(os.getenv("SSH_CONNECT_TIMEOUT", "10"))
        
        client.connect(
            hostname=profile["host"],
            port=int(profile["port"]),
            username=profile["user"],
            pkey=pkey,
            timeout=timeout,
            look_for_keys=False,  # Don't try other keys
            allow_agent=False,    # Don't use SSH agent
        )
    except paramiko.AuthenticationException as e:
        raise ValueError(f"SSH authentication failed for {profile_name}: {e}")
    except paramiko.SSHException as e:
        raise RuntimeError(f"SSH connection failed for {profile_name}: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to connect to {profile_name}: {e}")
    
    return client

import os
