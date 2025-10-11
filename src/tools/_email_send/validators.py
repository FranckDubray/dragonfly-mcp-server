"""Input validation for email_send operations."""

import re
from typing import Dict, Any, List


def validate_email(email: str) -> bool:
    """Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_send_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate send operation parameters.
    
    Args:
        params: Send parameters
        
    Returns:
        Validated parameters
        
    Raises:
        ValueError: If validation fails
    """
    # Validate 'to' recipients
    to = params.get("to", [])
    if not to or not isinstance(to, list):
        raise ValueError("Parameter 'to' is required and must be a list of email addresses")
    
    if len(to) > 100:
        raise ValueError("Parameter 'to' cannot exceed 100 recipients")
    
    for email in to:
        if not validate_email(email):
            raise ValueError(f"Invalid email address in 'to': {email}")
    
    # Validate subject
    subject = params.get("subject", "").strip()
    if not subject:
        raise ValueError("Parameter 'subject' is required and cannot be empty")
    
    if len(subject) > 500:
        raise ValueError("Parameter 'subject' cannot exceed 500 characters")
    
    # Validate body
    body = params.get("body", "").strip()
    if not body:
        raise ValueError("Parameter 'body' is required and cannot be empty")
    
    # Validate body_type
    body_type = params.get("body_type", "text")
    valid_body_types = ["text", "html"]
    if body_type not in valid_body_types:
        raise ValueError(f"Parameter 'body_type' must be one of: {', '.join(valid_body_types)}")
    
    # Validate CC (optional)
    cc = params.get("cc", [])
    if cc:
        if not isinstance(cc, list):
            raise ValueError("Parameter 'cc' must be a list of email addresses")
        if len(cc) > 50:
            raise ValueError("Parameter 'cc' cannot exceed 50 recipients")
        for email in cc:
            if not validate_email(email):
                raise ValueError(f"Invalid email address in 'cc': {email}")
    
    # Validate BCC (optional)
    bcc = params.get("bcc", [])
    if bcc:
        if not isinstance(bcc, list):
            raise ValueError("Parameter 'bcc' must be a list of email addresses")
        if len(bcc) > 50:
            raise ValueError("Parameter 'bcc' cannot exceed 50 recipients")
        for email in bcc:
            if not validate_email(email):
                raise ValueError(f"Invalid email address in 'bcc': {email}")
    
    # Validate reply_to (optional)
    reply_to = params.get("reply_to", "").strip()
    if reply_to and not validate_email(reply_to):
        raise ValueError(f"Invalid email address in 'reply_to': {reply_to}")
    
    # Validate attachments (optional)
    attachments = params.get("attachments", [])
    if attachments:
        if not isinstance(attachments, list):
            raise ValueError("Parameter 'attachments' must be a list of file paths")
        if len(attachments) > 10:
            raise ValueError("Parameter 'attachments' cannot exceed 10 files")
    
    # Validate from_name (optional)
    from_name = params.get("from_name", "").strip()
    if from_name and len(from_name) > 100:
        raise ValueError("Parameter 'from_name' cannot exceed 100 characters")
    
    # Validate priority (optional)
    priority = params.get("priority", "normal")
    valid_priorities = ["low", "normal", "high"]
    if priority not in valid_priorities:
        raise ValueError(f"Parameter 'priority' must be one of: {', '.join(valid_priorities)}")
    
    return {
        "to": [email.strip() for email in to],
        "subject": subject,
        "body": body,
        "body_type": body_type,
        "cc": [email.strip() for email in cc] if cc else [],
        "bcc": [email.strip() for email in bcc] if bcc else [],
        "reply_to": reply_to if reply_to else None,
        "attachments": attachments if attachments else [],
        "from_name": from_name if from_name else None,
        "priority": priority
    }
