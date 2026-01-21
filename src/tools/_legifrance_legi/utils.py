"""Utility functions for Légifrance LEGI."""
from __future__ import annotations
from typing import Dict, Any, List
import os
import logging
import shlex

LOG = logging.getLogger(__name__)


def get_ssh_config() -> Dict[str, Any]:
    """Get SSH configuration from environment variables.
    
    Returns:
        {"host": str, "key_path": str, "cli_cmd": list}
    """
    cli_path = os.getenv("LEGI_CLI_PATH", "/mnt/legifrance/repo/legifrance/scripts/legi_cli.py")
    
    # Parse CLI path (peut être "script.py" ou "/path/python /path/script.py")
    cli_parts = shlex.split(cli_path)
    
    config = {
        "host": os.getenv("LEGI_SSH_HOST", "root@188.245.151.223"),
        "key_path": os.getenv("LEGI_SSH_KEY", ""),  # Empty = use default key
        "cli_cmd": cli_parts  # List of command parts
    }
    
    return config


def get_timeout_config() -> Dict[str, int]:
    """Get timeout configuration from environment variables.
    
    Returns:
        {"summary": int, "article": int}
    """
    try:
        summary_timeout = int(os.getenv("LEGI_TIMEOUT_SUMMARY", "60"))
    except ValueError:
        LOG.warning("Invalid LEGI_TIMEOUT_SUMMARY, using default 60s")
        summary_timeout = 60
    
    try:
        article_timeout = int(os.getenv("LEGI_TIMEOUT_ARTICLE", "30"))
    except ValueError:
        LOG.warning("Invalid LEGI_TIMEOUT_ARTICLE, using default 30s")
        article_timeout = 30
    
    return {
        "summary": summary_timeout,
        "article": article_timeout
    }


def build_ssh_command(operation: str, **params) -> List[str]:
    """Build SSH command for the given operation.
    
    Args:
        operation: Operation name (get_summary or get_article)
        **params: Operation parameters
        
    Returns:
        List of command parts for subprocess.run()
    """
    ssh_config = get_ssh_config()
    
    # Base SSH command
    cmd = ["ssh"]
    
    # Add SSH key if specified
    if ssh_config["key_path"]:
        cmd.extend(["-i", ssh_config["key_path"]])
    
    # Add host
    cmd.append(ssh_config["host"])
    
    # Build remote command using cli_cmd from config
    cli_cmd_parts = ssh_config["cli_cmd"]
    
    if operation == "get_summary":
        remote_cmd_parts = cli_cmd_parts + [
            "get_codes",
            f"--scope={params.get('scope', 'codes_en_vigueur')}",
            f"--depth={params.get('depth', 2)}",
            f"--limit={params.get('limit', 77)}"
        ]
    
    elif operation == "get_article":
        article_ids = params.get("article_ids", [])
        ids_str = ",".join(article_ids)
        remote_cmd_parts = cli_cmd_parts + [
            "get_articles",
            f"--ids={ids_str}"
        ]
        
        if params.get("date"):
            remote_cmd_parts.append(f"--date={params['date']}")
        
        if params.get("include_links", True):
            remote_cmd_parts.append("--include_links")
        
        if params.get("include_breadcrumb", True):
            remote_cmd_parts.append("--include_breadcrumb")
    
    else:
        raise ValueError(f"Unknown operation: {operation}")
    
    # Join remote command parts into a single string for SSH
    remote_cmd = " ".join(remote_cmd_parts)
    cmd.append(remote_cmd)
    
    return cmd


def format_ssh_error(stderr: str, returncode: int) -> Dict[str, Any]:
    """Format SSH error for user-friendly output.
    
    Args:
        stderr: Error output from SSH
        returncode: Exit code
        
    Returns:
        Error dict with type and message
    """
    # Parse common SSH errors
    if "Connection refused" in stderr:
        return {
            "error": "SSH connection refused. Check that the server is accessible.",
            "error_type": "ssh_connection",
            "details": stderr
        }
    
    if "Permission denied" in stderr or "publickey" in stderr:
        return {
            "error": "SSH authentication failed. Check your SSH key configuration.",
            "error_type": "ssh_auth",
            "details": stderr,
            "hint": "Verify LEGI_SSH_HOST and LEGI_SSH_KEY environment variables"
        }
    
    if "Host key verification failed" in stderr:
        return {
            "error": "SSH host key verification failed.",
            "error_type": "ssh_hostkey",
            "details": stderr,
            "hint": "Run: ssh-keyscan -H <host> >> ~/.ssh/known_hosts"
        }
    
    if "No such file or directory" in stderr and ("legi_cli.py" in stderr or "python" in stderr):
        return {
            "error": "LEGI CLI script or Python interpreter not found on remote server.",
            "error_type": "remote_script_missing",
            "details": stderr,
            "hint": "Check LEGI_CLI_PATH environment variable"
        }
    
    # Generic error
    return {
        "error": f"SSH command failed with exit code {returncode}",
        "error_type": "ssh_error",
        "details": stderr
    }


def parse_remote_response(stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
    """Parse response from remote CLI script.
    
    Args:
        stdout: Standard output
        stderr: Standard error
        returncode: Exit code
        
    Returns:
        Parsed JSON response or error
    """
    import json
    
    # If command failed, parse error
    if returncode != 0:
        # Try to parse JSON error from stderr
        if stderr.strip():
            try:
                error_json = json.loads(stderr)
                return error_json
            except json.JSONDecodeError:
                pass
        
        return format_ssh_error(stderr, returncode)
    
    # Parse stdout as JSON
    if not stdout.strip():
        return {"error": "Empty response from remote server", "error_type": "empty_response"}
    
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        LOG.error(f"Failed to parse JSON response: {e}")
        return {
            "error": f"Invalid JSON response from remote server: {e}",
            "error_type": "json_parse_error",
            "raw_output": stdout[:500]  # First 500 chars for debugging
        }
