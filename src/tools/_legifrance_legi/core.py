"""Core SSH client for Légifrance LEGI."""
from __future__ import annotations
from typing import Dict, Any
import subprocess
import logging
import time

from .utils import build_ssh_command, parse_remote_response, get_timeout_config

LOG = logging.getLogger(__name__)


def execute_ssh_operation(operation: str, **params) -> Dict[str, Any]:
    """Execute LEGI operation via SSH.
    
    Args:
        operation: Operation name (get_summary or get_article)
        **params: Operation parameters
        
    Returns:
        Operation result or error
    """
    # Get timeout for this operation
    timeout_config = get_timeout_config()
    timeout = timeout_config.get("summary" if operation == "get_summary" else "article", 60)
    
    # Build SSH command
    try:
        cmd = build_ssh_command(operation, **params)
    except Exception as e:
        LOG.error(f"Failed to build SSH command: {e}")
        return {"error": f"Failed to build SSH command: {e}", "error_type": "command_build"}
    
    # Log command (without sensitive data)
    LOG.info(f"🔗 Executing SSH command: {operation} (timeout: {timeout}s)")
    
    # Execute command
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        elapsed = time.time() - start_time
        
        # Log execution time
        LOG.info(f"⏱️ SSH command completed in {elapsed:.2f}s (exit code: {result.returncode})")
        
        # Parse response
        response = parse_remote_response(result.stdout, result.stderr, result.returncode)
        
        # Add metadata
        if "error" not in response:
            response["_meta"] = {
                "execution_time_seconds": round(elapsed, 2),
                "data_size_bytes": len(result.stdout)
            }
            LOG.info(f"✅ {operation} succeeded ({len(result.stdout)} bytes)")
        else:
            LOG.warning(f"❌ {operation} failed: {response.get('error', 'Unknown error')}")
        
        return response
    
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        LOG.error(f"⏱️ SSH command timed out after {elapsed:.2f}s")
        return {
            "error": f"SSH command timed out after {timeout} seconds",
            "error_type": "timeout",
            "hint": f"Try reducing depth or limit for get_summary, or increase LEGI_TIMEOUT_{operation.upper()}"
        }
    
    except FileNotFoundError:
        LOG.error("❌ SSH command not found. Is SSH installed?")
        return {
            "error": "SSH command not found. Please install OpenSSH client.",
            "error_type": "ssh_not_installed"
        }
    
    except Exception as e:
        LOG.error(f"💥 Unexpected error executing SSH command: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "unknown"
        }


def get_summary(scope: str, depth: int, limit: int) -> Dict[str, Any]:
    """Get codes summary via SSH.
    
    Args:
        scope: Scope (codes_en_vigueur, codes_abroges, all)
        depth: Depth level (1-5)
        limit: Max number of codes
        
    Returns:
        Summary data or error
    """
    return execute_ssh_operation(
        "get_summary",
        scope=scope,
        depth=depth,
        limit=limit
    )


def get_article(article_ids: list, date: str = None, include_links: bool = True, include_breadcrumb: bool = True) -> Dict[str, Any]:
    """Get articles via SSH.
    
    Args:
        article_ids: List of article IDs
        date: Date for version filtering (YYYY-MM-DD)
        include_links: Include juridical links
        include_breadcrumb: Include breadcrumb trail
        
    Returns:
        Articles data or error
    """
    return execute_ssh_operation(
        "get_article",
        article_ids=article_ids,
        date=date,
        include_links=include_links,
        include_breadcrumb=include_breadcrumb
    )
