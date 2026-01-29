"""Input validation for SSH Client."""
from __future__ import annotations
from typing import Any, Tuple
import re
from pathlib import Path


def validate_host(host: str) -> Tuple[bool, str]:
    """Validate host (IP or hostname)."""
    if not host or not isinstance(host, str):
        return False, "Host must be a non-empty string"
    host = host.strip()
    if not host:
        return False, "Host cannot be empty"

    dangerous = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
    if any(c in host for c in dangerous):
        return False, "Host contains invalid characters"

    if not re.match(r"^[a-zA-Z0-9\.\-]+$", host):
        return False, "Host must be a valid IP or hostname"

    return True, ""


def validate_port(port: Any) -> Tuple[bool, int, str]:
    """Validate port number."""
    if port is None:
        return True, 22, ""
    try:
        port = int(port)
        if port < 1 or port > 65535:
            return False, 0, "Port must be between 1 and 65535"
        return True, port, ""
    except (ValueError, TypeError):
        return False, 0, "Port must be an integer"


def validate_timeout(timeout: Any) -> Tuple[bool, int, str]:
    """Validate timeout value."""
    if timeout is None:
        return True, 30, ""
    try:
        timeout = int(timeout)
        if timeout < 1:
            return False, 0, "Timeout must be at least 1 second"
        if timeout > 600:
            return False, 0, "Timeout cannot exceed 600 seconds"
        return True, timeout, ""
    except (ValueError, TypeError):
        return False, 0, "Timeout must be an integer"


def validate_command(command: str) -> Tuple[bool, str]:
    """Validate command (basic injection prevention).

    NOTE:
    - This validator is a safety net, not a full sandbox.
    - We keep a minimal blocklist for catastrophic commands.

    Security rule:
    - Block ONLY the catastrophic 'rm -rf /' (root wipe), but allow 'rm -rf /mnt/...'
    """
    if not command or not isinstance(command, str):
        return False, "Command must be a non-empty string"

    command = command.strip()
    if not command:
        return False, "Command cannot be empty"

    dangerous_patterns = [
        r"rm\s+-rf\s+/\s*$",  # ONLY 'rm -rf /' (exact root)
        r":\(\)\{.*:\|:.*\};:",  # Fork bomb
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Command contains dangerous pattern: {pattern}"

    return True, ""


def validate_path(path: str, path_type: str = "local") -> Tuple[bool, str, str]:
    """Validate file path."""
    if not path or not isinstance(path, str):
        return False, "", f"{path_type.capitalize()} path must be a non-empty string"

    path = path.strip()
    if not path:
        return False, "", f"{path_type.capitalize()} path cannot be empty"

    if path_type == "local":
        if path.startswith("~"):
            path = str(Path(path).expanduser())

        try:
            path_obj = Path(path)
            if not path_obj.is_absolute():
                project_root = Path(__file__).parent.parent.parent.parent
                
                # Check if path starts with allowed prefixes
                if path.startswith("server_legifrance/"):
                    # Use server_legifrance/ directly (miroir serveur)
                    path_obj = project_root / path
                else:
                    # Default to files/ for other relative paths
                    path_obj = project_root / "files" / path
            
            path = str(path_obj.resolve())
        except Exception as e:
            return False, "", f"Invalid local path: {str(e)}"

    else:
        dangerous = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
        if any(c in path for c in dangerous):
            return False, "", "Remote path contains invalid characters"

    return True, path, ""


def validate_auth_params(auth_type: str, password: str = None, key_file: str = None) -> Tuple[bool, str]:
    """Validate authentication parameters."""
    if not auth_type:
        return False, "auth_type is required"

    auth_type = auth_type.lower().strip()

    if auth_type not in ["password", "key", "agent"]:
        return False, f"Invalid auth_type '{auth_type}'. Must be: password, key, or agent"

    if auth_type == "password":
        if not password:
            return False, "Password is required when auth_type=password"

    elif auth_type == "key":
        if not key_file:
            return False, "key_file is required when auth_type=key"

        key_path = Path(key_file).expanduser()
        if not key_path.exists():
            return False, f"Key file not found: {key_file}"

        if not key_path.is_file():
            return False, f"Key file is not a file: {key_file}"

    return True, ""
