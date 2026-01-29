"""Core SSH client for Légifrance LEGI v2 - Using MCP ssh_client tool."""
from __future__ import annotations
from typing import Dict, Any
import logging
import time
import os
import json
import sys

from .utils import build_cli_command, get_ssh_config, get_timeout_config

LOG = logging.getLogger(__name__)


def execute_ssh_operation(operation: str, **params) -> Dict[str, Any]:
    """Execute LEGI operation via SSH using MCP ssh_client tool."""
    timeout_config = get_timeout_config()

    # Operation-specific timeouts
    if operation == "list_codes":
        timeout = 30  # Augmenté de 10→30s pour 170 codes avec cache
    elif operation == "get_code":
        timeout = timeout_config.get("summary", 60)
    else:  # get_articles
        timeout = timeout_config.get("article", 30)

    try:
        cli_command = build_cli_command(operation, **params)
    except Exception as e:
        LOG.error(f"Failed to build CLI command: {e}")
        return {"error": f"Failed to build CLI command: {e}", "error_type": "command_build"}

    ssh_config = get_ssh_config()

    # Log avec contexte enrichi (avant appel)
    if operation == "get_code":
        code_id = params.get("code_id", "")
        depth = params.get("depth", 3)
        LOG.info(f"📖 get_code: {code_id} (depth={depth})")
    elif operation == "list_codes":
        scope = params.get("scope", "codes_en_vigueur")
        LOG.info(f"📋 list_codes: scope={scope}")
    elif operation == "get_articles":
        article_ids = params.get("article_ids", [])
        LOG.info(f"📄 get_articles: {len(article_ids)} articles")
    else:
        LOG.info(f"🔗 Executing SSH command: {operation} (timeout: {timeout}s)")

    start_time = time.time()

    try:
        # Import ssh_client tool dynamically with multiple strategies
        ssh_run = None
        
        # Strategy 1: Direct import from src.tools
        try:
            from src.tools.ssh_client import run as ssh_run
        except ImportError:
            pass
        
        # Strategy 2: Relative import (if in same package structure)
        if ssh_run is None:
            try:
                import importlib
                ssh_module = importlib.import_module('src.tools.ssh_client')
                ssh_run = getattr(ssh_module, 'run')
            except (ImportError, AttributeError):
                pass
        
        # Strategy 3: Add to path and import
        if ssh_run is None:
            try:
                tools_path = os.path.join(os.path.dirname(__file__), '..', '..')
                if tools_path not in sys.path:
                    sys.path.insert(0, tools_path)
                from ssh_client import run as ssh_run
            except ImportError:
                pass
        
        if ssh_run is None:
            raise ImportError("Could not import ssh_client.run")

        result = ssh_run(
            operation="exec",
            host=ssh_config["host"].split("@")[1] if "@" in ssh_config["host"] else ssh_config["host"],
            username=ssh_config["host"].split("@")[0] if "@" in ssh_config["host"] else "root",
            auth_type="key",
            key_file=ssh_config["key_path"],
            key_passphrase=ssh_config.get("key_passphrase"),
            command=cli_command,
            timeout=timeout,
            verify_host_key="auto_add"
        )

        elapsed = time.time() - start_time

        # Parse result from ssh_client
        # ssh_client returns: {"operation": "exec", "exit_code": 0, "stdout": "...", "stderr": "...", ...}
        # OR {"error": "...", "error_type": "..."} on error
        if isinstance(result, dict):
            # Check for error response
            if "error" in result:
                error_msg = result.get("error", "Unknown SSH error")
                LOG.error(f"❌ SSH operation failed: {error_msg}")
                return {
                    "error": error_msg,
                    "error_type": result.get("error_type", "ssh_error"),
                    "details": result.get("details", "")
                }
            
            # Success response with exit_code
            if "exit_code" in result:
                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")
                exit_code = result.get("exit_code", 0)

                response = parse_remote_response(stdout, stderr, exit_code, operation)

                if isinstance(response, dict) and "error" not in response:
                    response["_meta"] = {
                        "execution_time_seconds": round(elapsed, 2),
                        "data_size_bytes": len(stdout)
                    }
                    
                    # Log success avec métadonnées (NOUVEAU v3.1)
                    log_success_with_metadata(operation, response, elapsed)
                elif isinstance(response, dict):
                    LOG.warning(f"❌ {operation} failed: {response.get('error', 'Unknown error')}")

                return response
            
            # Unexpected format
            LOG.error(f"💥 Unexpected ssh_client result format: {result}")
            return {
                "error": f"Unexpected ssh_client result format",
                "error_type": "unexpected_result",
                "result": str(result)[:200]
            }
        else:
            LOG.error(f"💥 Unexpected ssh_client result type: {type(result)}")
            return {
                "error": f"Unexpected ssh_client result type: {type(result)}",
                "error_type": "unexpected_result"
            }

    except ImportError as e:
        LOG.error(f"❌ Failed to import ssh_client tool: {e}")
        return {
            "error": f"ssh_client tool not available: {e}",
            "error_type": "missing_tool"
        }

    except Exception as e:
        elapsed = time.time() - start_time
        LOG.error(f"💥 Unexpected error executing SSH command: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "unknown",
            "execution_time_seconds": round(elapsed, 2)
        }


def log_success_with_metadata(operation: str, response: Dict[str, Any], elapsed: float):
    """Log success avec métadonnées enrichies (v3.1)."""
    if operation == "get_code":
        code_titre = response.get("code_titre", "")
        code_id = response.get("code_id", "")
        from_cache = response.get("from_cache", False)
        cache_emoji = "⚡" if from_cache else "🐢"
        
        if code_titre:
            LOG.info(f"✅ {code_titre} ({code_id}) retrieved in {elapsed:.2f}s {cache_emoji}")
        else:
            LOG.info(f"✅ {operation} succeeded ({len(response.get('tree', []))} sections, {elapsed:.2f}s)")
    
    elif operation == "list_codes":
        total = response.get("total", 0)
        LOG.info(f"✅ list_codes: {total} codes retrieved in {elapsed:.2f}s")
    
    elif operation == "get_articles":
        total = response.get("total", 0)
        LOG.info(f"✅ get_articles: {total} articles retrieved in {elapsed:.2f}s")
    
    else:
        LOG.info(f"✅ {operation} succeeded ({elapsed:.2f}s)")


def parse_remote_response(stdout: str, stderr: str, exit_code: int, operation: str = "") -> Dict[str, Any]:
    """Parse response from remote CLI script."""
    if exit_code != 0:
        if stderr.strip():
            try:
                return json.loads(stderr)
            except json.JSONDecodeError:
                pass
        return format_ssh_error(stderr, exit_code)

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


def format_ssh_error(stderr: str, exit_code: int) -> Dict[str, Any]:
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
        "error": f"SSH command failed with exit code {exit_code}",
        "error_type": "ssh_error",
        "details": stderr
    }


def list_codes(scope: str, nature: str = "CODE") -> Dict[str, Any]:
    """List codes with optional filtering by nature.
    
    Args:
        scope: codes_en_vigueur, codes_abroges, or all
        nature: CODE, ARRETE, DECRET, LOI, ORDONNANCE, or ALL (default: CODE)
    
    Returns:
        Filtered list of codes
    """
    result = execute_ssh_operation(
        "list_codes",
        scope=scope
    )
    
    # Filter by nature if not ALL
    if isinstance(result, dict) and "codes" in result and nature != "ALL":
        original_total = result.get("total", 0)
        filtered_codes = [c for c in result["codes"] if c.get("nature") == nature]
        result["codes"] = filtered_codes
        result["total"] = len(filtered_codes)
        result["_filter"] = {
            "nature": nature,
            "original_total": original_total,
            "filtered_total": len(filtered_codes)
        }
        LOG.info(f"🔍 Filtered {original_total} → {len(filtered_codes)} (nature={nature})")
    
    return result


def get_code(code_id: str, depth: int, include_articles: bool, root_section_id: str | None = None) -> Dict[str, Any]:
    return execute_ssh_operation(
        "get_code",
        code_id=code_id,
        depth=depth,
        include_articles=include_articles,
        root_section_id=root_section_id
    )


def get_articles(article_ids: list, date: str | None = None, include_links: bool = True, include_breadcrumb: bool = True) -> Dict[str, Any]:
    return execute_ssh_operation(
        "get_articles",
        article_ids=article_ids,
        date=date,
        include_links=include_links,
        include_breadcrumb=include_breadcrumb
    )
