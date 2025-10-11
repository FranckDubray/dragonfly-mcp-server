"""Core logic for email send operations."""

from typing import Dict, Any
from .services.smtp_client import SMTPClient
from .validators import validate_send_params


def handle_test_connection(provider: str = "gmail", **params) -> Dict[str, Any]:
    """Handle test_connection operation.
    
    Args:
        provider: Email provider (gmail or infomaniak)
    
    Tests SMTP connection and authentication.
    
    Returns:
        Connection test results
    """
    try:
        client = SMTPClient(provider=provider)
        return client.test_connection()
        
    except ValueError as e:
        return {"error": f"Configuration error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def handle_send(provider: str = "gmail", **params) -> Dict[str, Any]:
    """Handle send operation.
    
    Args:
        provider: Email provider (gmail or infomaniak)
        **params: Send parameters
            - to (list): Recipient email addresses (required)
            - subject (str): Email subject (required)
            - body (str): Email body content (required)
            - body_type (str): Body type - text or html (default: text)
            - cc (list): CC recipients (optional)
            - bcc (list): BCC recipients (optional)
            - reply_to (str): Reply-To address (optional)
            - attachments (list): File paths to attach (optional)
            - from_name (str): Sender display name (optional)
            - priority (str): Email priority - low, normal, high (default: normal)
    
    Returns:
        Send results
    """
    try:
        # Validate parameters
        validated = validate_send_params(params)
        
        # Initialize SMTP client
        client = SMTPClient(provider=provider)
        
        # Send email
        return client.send(
            to=validated["to"],
            subject=validated["subject"],
            body=validated["body"],
            body_type=validated["body_type"],
            cc=validated["cc"],
            bcc=validated["bcc"],
            reply_to=validated["reply_to"],
            attachments=validated["attachments"],
            from_name=validated["from_name"],
            priority=validated["priority"]
        )
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
