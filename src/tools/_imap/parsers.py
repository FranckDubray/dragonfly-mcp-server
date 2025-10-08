"""
MIME message parsing: headers, body (text/html), attachments
"""
from __future__ import annotations
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import Dict, Any, List, Optional, Tuple
import base64
import quopri
from .utils import safe_decode, normalize_email_address, truncate_text


def parse_email_message(raw_email: bytes, 
                        include_body: bool = True,
                        include_attachments_metadata: bool = True) -> Dict[str, Any]:
    """
    Parse raw email bytes into structured data.
    Returns: {headers, flags, body, attachments, meta}
    """
    msg = email.message_from_bytes(raw_email)
    
    # Parse headers
    headers = {
        "from": decode_header_value(msg.get("From", "")),
        "to": decode_header_value(msg.get("To", "")),
        "cc": decode_header_value(msg.get("Cc", "")),
        "bcc": decode_header_value(msg.get("Bcc", "")),
        "subject": decode_header_value(msg.get("Subject", "")),
        "date": msg.get("Date", ""),
        "message_id": msg.get("Message-ID", ""),
        "in_reply_to": msg.get("In-Reply-To", "")
    }
    
    # Parse date
    try:
        date_obj = parsedate_to_datetime(headers["date"])
        headers["date_parsed"] = date_obj.isoformat()
    except Exception:
        headers["date_parsed"] = None
    
    # Extract body and attachments
    body = {"text": "", "html": ""}
    attachments = []
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            
            # Body parts
            if "attachment" not in content_disposition:
                if content_type == "text/plain" and include_body:
                    text = decode_payload(part)
                    body["text"] += text
                elif content_type == "text/html" and include_body:
                    html = decode_payload(part)
                    body["html"] += html
            
            # Attachments
            elif include_attachments_metadata:
                filename = part.get_filename()
                if filename:
                    filename = decode_header_value(filename)
                    attachments.append({
                        "filename": filename,
                        "content_type": content_type,
                        "size": len(part.get_payload(decode=True) or b''),
                        "content_id": part.get("Content-ID", "")
                    })
    else:
        # Non-multipart
        content_type = msg.get_content_type()
        if content_type == "text/plain" and include_body:
            body["text"] = decode_payload(msg)
        elif content_type == "text/html" and include_body:
            body["html"] = decode_payload(msg)
    
    # Truncate bodies for safety
    if body["text"]:
        body["text"] = truncate_text(body["text"], max_length=50000)
    if body["html"]:
        body["html"] = truncate_text(body["html"], max_length=50000)
    
    return {
        "headers": headers,
        "body": body if include_body else None,
        "attachments": attachments if include_attachments_metadata else None,
        "has_attachments": len(attachments) > 0
    }


def decode_header_value(header: str) -> str:
    """Decode encoded email header (RFC 2047)"""
    if not header:
        return ""
    
    decoded_parts = []
    for part, encoding in decode_header(header):
        if isinstance(part, bytes):
            try:
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
            except Exception:
                decoded_parts.append(part.decode('utf-8', errors='replace'))
        else:
            decoded_parts.append(part)
    
    return " ".join(decoded_parts)


def decode_payload(part: email.message.Message) -> str:
    """Decode message part payload (handles base64, quoted-printable, 7bit, 8bit)"""
    try:
        payload = part.get_payload(decode=True)
        if payload is None:
            return ""
        
        # Get charset
        charset = part.get_content_charset() or 'utf-8'
        
        # Decode bytes to string
        return safe_decode(payload, charset)
    
    except Exception:
        # Fallback
        payload = part.get_payload()
        if isinstance(payload, bytes):
            return safe_decode(payload)
        return str(payload)


def extract_attachments(msg: email.message.Message) -> List[Tuple[str, bytes, str]]:
    """
    Extract attachments from message.
    Returns list of (filename, content_bytes, content_type)
    """
    attachments = []
    
    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    filename = decode_header_value(filename)
                    content_bytes = part.get_payload(decode=True) or b''
                    content_type = part.get_content_type()
                    attachments.append((filename, content_bytes, content_type))
    
    return attachments
