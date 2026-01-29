"""
SSH Diagnostics Tool - Troubleshoot unstable SSH connections

Comprehensive diagnostics for SSH disconnection issues:
- Connection testing with verbose debug output
- Server-side log analysis (auth.log, secure)
- Keepalive configuration check and recommendations
- Network connectivity tests (ping, traceroute, MTR)
- Firewall rules inspection (iptables, ufw, nftables)
- Fail2ban status and banned IPs
- Server load monitoring (CPU, RAM, OOM)
- Optimized SSH config generation

Example (full diagnostic):
  {
    "tool": "ssh_diagnostics",
    "params": {
      "operation": "full_diagnostic",
      "host": "188.245.151.223",
      "user": "root",
      "port": 22
    }
  }

Example (generate SSH config with keepalive):
  {
    "tool": "ssh_diagnostics",
    "params": {
      "operation": "generate_ssh_config",
      "host": "188.245.151.223",
      "user": "root",
      "keepalive_interval": 30,
      "keepalive_count_max": 6
    }
  }

Example (check server logs - run ON the SSH server):
  {
    "tool": "ssh_diagnostics",
    "params": {
      "operation": "check_server_logs",
      "log_lines": 200
    }
  }
"""
from __future__ import annotations
from typing import Dict, Any

from ._ssh_diagnostics.api import route_request
from ._ssh_diagnostics import spec as _spec


def run(**params) -> Dict[str, Any]:
    """Execute SSH diagnostic operation.
    
    Args:
        **params: Operation parameters (operation, host, user, etc.)
        
    Returns:
        Diagnostic results
    """
    # Extract operation
    operation = params.get("operation")
    
    # Validate required params
    if not operation:
        return {"error": "Parameter 'operation' is required"}
    
    # Remove operation from params to avoid duplicate arguments
    clean_params = {k: v for k, v in params.items() if k != "operation"}
    
    # Route to handler
    return route_request(operation, **clean_params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
