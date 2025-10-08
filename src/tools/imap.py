"""
IMAP Email Tool — Universal email access via IMAP protocol
Supports: Gmail, Outlook, Yahoo, iCloud, Infomaniak, custom servers
Operations: connect, list_folders, search_messages, get_message, download_attachments, 
            mark_read/unread (single + batch), move_message (single + batch), 
            mark_spam (batch), delete_message (single + batch)

Configuration via .env (per provider):
- IMAP_<PROVIDER>_EMAIL (ex: IMAP_GMAIL_EMAIL, IMAP_INFOMANIAK_EMAIL)
- IMAP_<PROVIDER>_PASSWORD
- IMAP_CUSTOM_SERVER, IMAP_CUSTOM_PORT, IMAP_CUSTOM_USE_SSL (custom only)

Example:
  IMAP_GMAIL_EMAIL=user@gmail.com
  IMAP_GMAIL_PASSWORD=app_password
  
  IMAP_INFOMANIAK_EMAIL=user@infomaniak.com
  IMAP_INFOMANIAK_PASSWORD=password
"""
from __future__ import annotations
import os
import json
from typing import Dict, Any, List
from ._imap.connection import IMAPConnection
from ._imap import operations as ops


def run(provider: str = "gmail", operation: str = None, **params) -> Dict[str, Any]:
    """
    Main entry point for IMAP operations.
    
    Credentials are read from environment variables (.env) based on provider:
    - IMAP_<PROVIDER>_EMAIL (ex: IMAP_GMAIL_EMAIL)
    - IMAP_<PROVIDER>_PASSWORD
    
    For custom provider:
    - IMAP_CUSTOM_SERVER, IMAP_CUSTOM_PORT, IMAP_CUSTOM_USE_SSL
    
    Parameters:
    - provider: gmail, outlook, yahoo, icloud, infomaniak, custom (default: gmail)
    - operation: connect, list_folders, search_messages, get_message, etc.
    
    Operations:
    - connect: Test connection
    - list_folders: List all folders
    - search_messages: Search with IMAP criteria
    - get_message: Get full message by UID
    - download_attachments: Download attachments to files/
    - mark_read / mark_unread: Single message
    - mark_read_batch / mark_unread_batch: Multiple messages
    - move_message: Single message to another folder
    - move_messages_batch: Multiple messages to another folder
    - mark_spam: Move multiple messages to spam folder
    - delete_message: Single message
    - delete_messages_batch: Multiple messages
    """
    if not operation:
        return {"error": "operation parameter is required"}
    
    # Normalize provider name
    provider = (provider or "gmail").lower()
    provider_upper = provider.upper()
    
    # Read credentials from environment (provider-specific)
    email_key = f"IMAP_{provider_upper}_EMAIL"
    password_key = f"IMAP_{provider_upper}_PASSWORD"
    
    email = os.getenv(email_key)
    password = os.getenv(password_key)
    
    # For custom provider, read additional config
    imap_server = None
    imap_port = None
    use_ssl = True
    
    if provider == "custom":
        imap_server = os.getenv("IMAP_CUSTOM_SERVER")
        imap_port_str = os.getenv("IMAP_CUSTOM_PORT")
        use_ssl_str = os.getenv("IMAP_CUSTOM_USE_SSL", "true")
        use_ssl = use_ssl_str.lower() in ("true", "1", "yes")
        
        if imap_port_str:
            try:
                imap_port = int(imap_port_str)
            except ValueError:
                imap_port = None
    
    # Validate credentials
    if not email:
        return {
            "error": f"{email_key} not configured",
            "hint": f"Set {email_key} in .env or via /config endpoint",
            "example": f"{email_key}=user@example.com"
        }
    if not password:
        return {
            "error": f"{password_key} not configured",
            "hint": f"Set {password_key} in .env (use App Password for Gmail/Yahoo/iCloud)",
            "example": f"{password_key}=your_app_password"
        }
    
    try:
        # Create connection
        conn = IMAPConnection(
            provider=provider,
            email=email,
            password=password,
            imap_server=imap_server,
            imap_port=imap_port,
            use_ssl=use_ssl,
            timeout=30
        )
        
        # Route operations
        if operation == "connect":
            return ops.op_connect(conn)
        
        # For all other ops, use context manager to ensure proper cleanup
        with conn:
            if operation == "list_folders":
                return ops.op_list_folders(conn)
            
            elif operation == "search_messages":
                folder = params.get("folder", "inbox")
                query = params.get("query", {})
                max_results = params.get("max_results", 50)
                return ops.op_search_messages(conn, folder, query, max_results)
            
            elif operation == "get_message":
                message_id = params.get("message_id")
                if not message_id:
                    return {"error": "message_id is required"}
                folder = params.get("folder", "inbox")
                include_body = params.get("include_body", True)
                include_attachments_metadata = params.get("include_attachments_metadata", True)
                return ops.op_get_message(conn, message_id, folder, include_body, include_attachments_metadata)
            
            elif operation == "download_attachments":
                message_id = params.get("message_id")
                if not message_id:
                    return {"error": "message_id is required"}
                folder = params.get("folder", "inbox")
                output_dir = params.get("output_dir")
                return ops.op_download_attachments(conn, message_id, folder, output_dir)
            
            elif operation == "mark_read":
                message_id = params.get("message_id")
                if not message_id:
                    return {"error": "message_id is required"}
                folder = params.get("folder", "inbox")
                return ops.op_mark_read(conn, message_id, folder)
            
            elif operation == "mark_unread":
                message_id = params.get("message_id")
                if not message_id:
                    return {"error": "message_id is required"}
                folder = params.get("folder", "inbox")
                return ops.op_mark_unread(conn, message_id, folder)
            
            elif operation == "mark_read_batch":
                message_ids = params.get("message_ids")
                if not message_ids or not isinstance(message_ids, list):
                    return {"error": "message_ids (array) is required"}
                folder = params.get("folder", "inbox")
                return ops.op_mark_read_batch(conn, message_ids, folder)
            
            elif operation == "mark_unread_batch":
                message_ids = params.get("message_ids")
                if not message_ids or not isinstance(message_ids, list):
                    return {"error": "message_ids (array) is required"}
                folder = params.get("folder", "inbox")
                return ops.op_mark_unread_batch(conn, message_ids, folder)
            
            elif operation == "move_message":
                message_id = params.get("message_id")
                target_folder = params.get("target_folder")
                if not message_id or not target_folder:
                    return {"error": "message_id and target_folder are required"}
                folder = params.get("folder", "inbox")
                return ops.op_move_message(conn, message_id, folder, target_folder)
            
            elif operation == "move_messages_batch":
                message_ids = params.get("message_ids")
                target_folder = params.get("target_folder")
                if not message_ids or not isinstance(message_ids, list) or not target_folder:
                    return {"error": "message_ids (array) and target_folder are required"}
                folder = params.get("folder", "inbox")
                return ops.op_move_messages_batch(conn, message_ids, folder, target_folder)
            
            elif operation == "mark_spam":
                message_ids = params.get("message_ids")
                if not message_ids or not isinstance(message_ids, list):
                    return {"error": "message_ids (array) is required"}
                folder = params.get("folder", "inbox")
                return ops.op_mark_spam(conn, message_ids, folder)
            
            elif operation == "delete_message":
                message_id = params.get("message_id")
                if not message_id:
                    return {"error": "message_id is required"}
                folder = params.get("folder", "inbox")
                expunge = params.get("expunge", True)
                return ops.op_delete_message(conn, message_id, folder, expunge)
            
            elif operation == "delete_messages_batch":
                message_ids = params.get("message_ids")
                if not message_ids or not isinstance(message_ids, list):
                    return {"error": "message_ids (array) is required"}
                folder = params.get("folder", "inbox")
                expunge = params.get("expunge", True)
                return ops.op_delete_messages_batch(conn, message_ids, folder, expunge)
            
            else:
                return {"error": f"Unknown operation: {operation}"}
    
    except ConnectionError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Operation failed: {str(e)}"}


def spec() -> Dict[str, Any]:
    """Load and return the canonical JSON spec (source of truth)."""
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'imap.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
