"""Utility functions for Légifrance LEGI v2."""
from __future__ import annotations
from typing import Dict, Any, List
import os
import logging
import shlex

LOG = logging.getLogger(__name__)


def get_ssh_config() -> Dict[str, Any]:
    """Get SSH configuration from environment variables.

    Returns:
        {"host": str, "key_path": str, "key_passphrase": str, "cli_cmd": str}
    """
    cli_path = os.getenv("LEGI_CLI_PATH", "/mnt/legifrance/repo/legifrance/scripts/legi_cli.py")

    return {
        "host": os.getenv("LEGI_SSH_HOST", "root@188.245.151.223"),
        "key_path": os.getenv("LEGI_SSH_KEY", "~/.ssh/id_ed25519_legi"),
        "key_passphrase": os.getenv("LEGI_SSH_PASSPHRASE", ""),
        "cli_path": cli_path
    }


def get_timeout_config() -> Dict[str, int]:
    """Get timeout configuration from environment variables."""
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

    return {"summary": summary_timeout, "article": article_timeout}


def build_cli_command(operation: str, **params) -> str:
    """Build CLI command string for the given operation.
    
    Args:
        operation: One of 'list_codes', 'get_code', 'get_articles'
        **params: Operation-specific parameters
    
    Returns:
        Complete CLI command string
    """
    ssh_config = get_ssh_config()
    cli_path = ssh_config["cli_path"]

    # Build command parts
    if operation == "list_codes":
        scope = params.get('scope', 'codes_en_vigueur')
        cmd = f"{cli_path} list_codes --scope={scope}"

    elif operation == "get_code":
        code_id = params.get('code_id')
        if not code_id:
            raise ValueError("code_id is required for get_code operation")
        
        depth = params.get('depth', 3)
        cmd = f"{cli_path} get_code --code_id={code_id} --depth={depth}"
        
        if params.get('include_articles'):
            cmd += " --include_articles"
        
        if params.get('root_section_id'):
            cmd += f" --root_section_id={params['root_section_id']}"

    elif operation == "get_articles":
        article_ids = params.get('article_ids', [])
        if not article_ids:
            raise ValueError("article_ids is required for get_articles operation")
        
        ids_str = ",".join(article_ids)
        cmd = f"{cli_path} get_articles --ids={ids_str}"
        
        if params.get('date'):
            cmd += f" --date={params['date']}"
        
        if params.get('include_links', True):
            cmd += " --include_links"
        
        if params.get('include_breadcrumb', True):
            cmd += " --include_breadcrumb"

    else:
        raise ValueError(f"Unknown operation: {operation}")

    return cmd


def format_ssh_error(stderr: str, returncode: int) -> Dict[str, Any]:
    """Format SSH error for user-friendly output."""
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
            "hint": "Verify LEGI_SSH_HOST, LEGI_SSH_KEY, and LEGI_SSH_PASSPHRASE environment variables"
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

    return {
        "error": f"SSH command failed with exit code {returncode}",
        "error_type": "ssh_error",
        "details": stderr
    }


def parse_remote_response(stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
    """Parse response from remote CLI script."""
    import json

    if returncode != 0:
        if stderr.strip():
            try:
                return json.loads(stderr)
            except json.JSONDecodeError:
                pass
        return format_ssh_error(stderr, returncode)

    if not stdout.strip():
        return {"error": "Empty response from remote server", "error_type": "empty_response"}

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        LOG.error(f"Failed to parse JSON response: {e}")
        return {
            "error": f"Invalid JSON response from remote server: {e}",
            "error_type": "json_parse_error",
            "raw_output": stdout[:500]
        }
