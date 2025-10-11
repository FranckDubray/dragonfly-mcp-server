"""
Email send tool - Send emails via SMTP (Gmail or Infomaniak)

Uses same credentials as IMAP tool:
- IMAP_GMAIL_EMAIL + IMAP_GMAIL_PASSWORD (Gmail App Password)
- IMAP_INFOMANIAK_EMAIL + IMAP_INFOMANIAK_PASSWORD

SMTP servers are hardcoded:
- Gmail: smtp.gmail.com:587 (TLS)
- Infomaniak: mail.infomaniak.com:587 (TLS)
"""

from typing import Dict, Any
from ._email_send.api import route_operation
from ._email_send import spec as _spec


def run(provider: str = "gmail", operation: str = None, **params) -> Dict[str, Any]:
    """Execute email send operation.
    
    Args:
        provider: Email provider (gmail or infomaniak, default: gmail)
        operation: Operation to perform (test_connection, send)
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    # Normalize provider
    provider = (provider or "gmail").strip().lower()
    
    # Normalize operation
    op = (operation or params.get("operation") or "send").strip().lower()
    
    # Validate required params for 'send' operation
    if op == "send":
        if "to" not in params:
            return {"error": "Parameter 'to' is required for 'send' operation"}
        if "subject" not in params:
            return {"error": "Parameter 'subject' is required for 'send' operation"}
        if "body" not in params:
            return {"error": "Parameter 'body' is required for 'send' operation"}
    
    # Route to handler
    return route_operation(op, provider=provider, **params)


def spec() -> Dict[str, Any]:
    """Return tool specification.
    
    Returns:
        OpenAI function calling spec
    """
    return _spec()
