"""
SSH profiles management (load from .env).
"""
from __future__ import annotations
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from .utils import resolve_key_path
except Exception:
    from src.tools._ssh_admin.utils import resolve_key_path

def load_profiles() -> Dict[str, Dict[str, Any]]:
    """
    Load SSH profiles from .env SSH_PROFILES_JSON.
    
    Returns dict: {profile_name: {host, port, user, key_path}}
    """
    profiles_json = os.getenv("SSH_PROFILES_JSON")
    if not profiles_json:
        raise ValueError(
            "SSH_PROFILES_JSON not configured in .env\n"
            "Example: SSH_PROFILES_JSON='{\"prod\": {\"host\": \"server.com\", \"port\": 22, \"user\": \"admin\", \"key_path\": \"ssh_keys/id_rsa_prod\"}}'"
        )
    
    try:
        profiles = json.loads(profiles_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in SSH_PROFILES_JSON: {e}")
    
    if not isinstance(profiles, dict):
        raise ValueError("SSH_PROFILES_JSON must be a JSON object (dict)")
    
    # Validate each profile
    for name, config in profiles.items():
        if not isinstance(config, dict):
            raise ValueError(f"Profile '{name}' must be an object")
        
        required = ["host", "port", "user", "key_path"]
        for field in required:
            if field not in config:
                raise ValueError(f"Profile '{name}' missing required field: {field}")
    
    return profiles

def get_profile(profile_name: str) -> Dict[str, Any]:
    """Get profile config by name."""
    profiles = load_profiles()
    
    if profile_name not in profiles:
        available = ", ".join(profiles.keys())
        raise ValueError(
            f"Profile '{profile_name}' not found.\n"
            f"Available profiles: {available}"
        )
    
    return profiles[profile_name]

def list_profiles() -> list[str]:
    """List available profile names."""
    try:
        profiles = load_profiles()
        return list(profiles.keys())
    except Exception:
        return []
