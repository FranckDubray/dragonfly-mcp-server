"""
IMAP operations: search, get, list_folders, download, mark, move, delete
"""
from __future__ import annotations
import os
from typing import Dict, Any, List
from .connection import IMAPConnection
from .presets import normalize_folder_name
from .utils import build_imap_search_query, parse_message_ids
from .parsers import parse_email_message, extract_attachments


def op_connect(conn: IMAPConnection) -> Dict[str, Any]:
    """Test connection and return info"""
    return conn.connect()


def op_list_folders(conn: IMAPConnection) -> Dict[str, Any]:
    """List all available IMAP folders"""
    try:
        status, folders_data = conn.connection.list()
        if status != 'OK':
            return {"success": False, "error": "Failed to list folders"}
        
        folders = []
        for folder_line in folders_data:
            # Parse: b'(\\HasNoChildren) "/" "INBOX"'
            if isinstance(folder_line, bytes):
                folder_line = folder_line.decode('utf-8')
            
            # Extract folder name (last quoted part)
            parts = folder_line.split('"')
            if len(parts) >= 3:
                folder_name = parts[-2]
                folders.append({
                    "name": folder_name,
                    "raw": folder_line
                })
        
        return {
            "success": True,
            "folders": folders,
            "count": len(folders)
        }
    
    except Exception as e:
        return {"success": False, "error": f"List folders failed: {str(e)}"}


def op_search_messages(conn: IMAPConnection, 
                       folder: str = "INBOX",
                       query: Dict[str, Any] = None,
                       max_results: int = 50) -> Dict[str, Any]:
    """
    Search messages in a folder with IMAP criteria.
    Returns list of message UIDs and basic metadata.
    """
    try:
        # Normalize folder name
        folder = normalize_folder_name(conn.provider, folder)
        
        # Select folder
        status, _ = conn.connection.select(folder, readonly=True)
        if status != 'OK':
            return {"success": False, "error": f"Failed to select folder: {folder}"}
        
        # Build search query
        search_criteria = build_imap_search_query(query or {})
        
        # Search
        status, data = conn.connection.uid('SEARCH', None, search_criteria)
        if status != 'OK':
            return {"success": False, "error": "Search failed"}
        
        # Parse message UIDs
        message_uids = parse_message_ids(data[0])
        
        # Limit results
        message_uids = message_uids[-max_results:] if len(message_uids) > max_results else message_uids
        
        # Fetch basic info for each message
        messages = []
        for uid in reversed(message_uids):  # Most recent first
            try:
                # Fetch envelope + flags
                status, msg_data = conn.connection.uid('FETCH', uid, '(FLAGS ENVELOPE BODY.PEEK[HEADER.FIELDS (SUBJECT FROM TO DATE)])')
                if status == 'OK' and msg_data and msg_data[0]:
                    # Parse headers
                    header_data = msg_data[0][1] if len(msg_data[0]) > 1 else b''
                    import email
                    msg = email.message_from_bytes(header_data)
                    
                    messages.append({
                        "uid": uid,
                        "subject": msg.get("Subject", ""),
                        "from": msg.get("From", ""),
                        "to": msg.get("To", ""),
                        "date": msg.get("Date", ""),
                        "flags": str(msg_data[0][0]) if msg_data[0] else ""
                    })
            except Exception:
                continue
        
        return {
            "success": True,
            "folder": folder,
            "query": query,
            "messages": messages,
            "count": len(messages),
            "total_matching": len(message_uids)
        }
    
    except Exception as e:
        return {"success": False, "error": f"Search failed: {str(e)}"}


def op_get_message(conn: IMAPConnection,
                   message_id: str,
                   folder: str = "INBOX",
                   include_body: bool = True,
                   include_attachments_metadata: bool = True) -> Dict[str, Any]:
    """Get full message details by UID"""
    try:
        # Normalize folder
        folder = normalize_folder_name(conn.provider, folder)
        
        # Select folder
        status, _ = conn.connection.select(folder, readonly=True)
        if status != 'OK':
            return {"success": False, "error": f"Failed to select folder: {folder}"}
        
        # Fetch full message
        status, msg_data = conn.connection.uid('FETCH', message_id, '(RFC822 FLAGS)')
        if status != 'OK' or not msg_data or not msg_data[0]:
            return {"success": False, "error": f"Message not found: {message_id}"}
        
        raw_email = msg_data[0][1]
        flags = str(msg_data[0][0])
        
        # Parse message
        parsed = parse_email_message(raw_email, include_body, include_attachments_metadata)
        
        return {
            "success": True,
            "uid": message_id,
            "folder": folder,
            "flags": flags,
            **parsed
        }
    
    except Exception as e:
        return {"success": False, "error": f"Get message failed: {str(e)}"}


def op_download_attachments(conn: IMAPConnection,
                            message_id: str,
                            folder: str = "INBOX",
                            output_dir: str = None) -> Dict[str, Any]:
    """Download all attachments from a message"""
    try:
        # Normalize folder
        folder = normalize_folder_name(conn.provider, folder)
        
        # Select folder
        status, _ = conn.connection.select(folder, readonly=True)
        if status != 'OK':
            return {"success": False, "error": f"Failed to select folder: {folder}"}
        
        # Fetch full message
        status, msg_data = conn.connection.uid('FETCH', message_id, '(RFC822)')
        if status != 'OK' or not msg_data or not msg_data[0]:
            return {"success": False, "error": f"Message not found: {message_id}"}
        
        raw_email = msg_data[0][1]
        
        # Parse attachments
        import email
        msg = email.message_from_bytes(raw_email)
        attachments = extract_attachments(msg)
        
        if not attachments:
            return {"success": True, "message": "No attachments found", "files": []}
        
        # Determine output directory
        if not output_dir:
            output_dir = f"files/imap/attachments/{message_id}"
        
        # Ensure output directory exists and is relative to project root
        output_abs = os.path.abspath(output_dir)
        os.makedirs(output_abs, exist_ok=True)
        
        # Save files
        saved_files = []
        for filename, content_bytes, content_type in attachments:
            filepath = os.path.join(output_abs, filename)
            try:
                with open(filepath, 'wb') as f:
                    f.write(content_bytes)
                
                saved_files.append({
                    "filename": filename,
                    "path": output_dir + "/" + filename,  # Relative path
                    "size": len(content_bytes),
                    "content_type": content_type
                })
            except Exception as e:
                saved_files.append({
                    "filename": filename,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "message_id": message_id,
            "output_dir": output_dir,
            "files": saved_files,
            "count": len(saved_files)
        }
    
    except Exception as e:
        return {"success": False, "error": f"Download attachments failed: {str(e)}"}


def op_mark_read(conn: IMAPConnection, message_id: str, folder: str = "INBOX") -> Dict[str, Any]:
    """Mark message as read (set \\Seen flag)"""
    return _set_flag(conn, message_id, folder, '\\Seen', add=True)


def op_mark_unread(conn: IMAPConnection, message_id: str, folder: str = "INBOX") -> Dict[str, Any]:
    """Mark message as unread (remove \\Seen flag)"""
    return _set_flag(conn, message_id, folder, '\\Seen', add=False)


def op_mark_read_batch(conn: IMAPConnection, message_ids: List[str], folder: str = "INBOX") -> Dict[str, Any]:
    """Mark multiple messages as read in one call"""
    return _set_flag_batch(conn, message_ids, folder, '\\Seen', add=True)


def op_mark_unread_batch(conn: IMAPConnection, message_ids: List[str], folder: str = "INBOX") -> Dict[str, Any]:
    """Mark multiple messages as unread in one call"""
    return _set_flag_batch(conn, message_ids, folder, '\\Seen', add=False)


def op_move_message(conn: IMAPConnection, message_id: str, folder: str, target_folder: str) -> Dict[str, Any]:
    """Move message to another folder"""
    try:
        folder = normalize_folder_name(conn.provider, folder)
        target_folder = normalize_folder_name(conn.provider, target_folder)
        
        # Select source folder (read-write)
        status, _ = conn.connection.select(folder, readonly=False)
        if status != 'OK':
            return {"success": False, "error": f"Failed to select folder: {folder}"}
        
        # Copy to target
        status, _ = conn.connection.uid('COPY', message_id, target_folder)
        if status != 'OK':
            return {"success": False, "error": f"Failed to copy to {target_folder}"}
        
        # Mark as deleted in source
        conn.connection.uid('STORE', message_id, '+FLAGS', '\\Deleted')
        conn.connection.expunge()
        
        return {
            "success": True,
            "message_id": message_id,
            "from": folder,
            "to": target_folder
        }
    
    except Exception as e:
        return {"success": False, "error": f"Move failed: {str(e)}"}


def op_move_messages_batch(conn: IMAPConnection, message_ids: List[str], folder: str, target_folder: str) -> Dict[str, Any]:
    """Move multiple messages to another folder in one call"""
    try:
        folder = normalize_folder_name(conn.provider, folder)
        target_folder = normalize_folder_name(conn.provider, target_folder)
        
        # Select source folder (read-write)
        status, _ = conn.connection.select(folder, readonly=False)
        if status != 'OK':
            return {"success": False, "error": f"Failed to select folder: {folder}"}
        
        moved = []
        failed = []
        
        for msg_id in message_ids:
            try:
                # Copy to target
                status, _ = conn.connection.uid('COPY', msg_id, target_folder)
                if status != 'OK':
                    failed.append({"id": msg_id, "error": f"Failed to copy to {target_folder}"})
                    continue
                
                # Mark as deleted in source
                conn.connection.uid('STORE', msg_id, '+FLAGS', '\\Deleted')
                moved.append(msg_id)
            except Exception as e:
                failed.append({"id": msg_id, "error": str(e)})
        
        # Expunge all at once
        conn.connection.expunge()
        
        return {
            "success": len(failed) == 0,
            "moved": moved,
            "moved_count": len(moved),
            "failed": failed,
            "failed_count": len(failed),
            "from": folder,
            "to": target_folder
        }
    
    except Exception as e:
        return {"success": False, "error": f"Batch move failed: {str(e)}"}


def op_mark_spam(conn: IMAPConnection, message_ids: List[str], folder: str = "INBOX") -> Dict[str, Any]:
    """Mark messages as spam (move to spam folder)"""
    spam_folder = normalize_folder_name(conn.provider, "spam")
    return op_move_messages_batch(conn, message_ids, folder, spam_folder)


def op_delete_message(conn: IMAPConnection, message_id: str, folder: str = "INBOX", expunge: bool = True) -> Dict[str, Any]:
    """Delete message (mark as \\Deleted and optionally expunge)"""
    try:
        folder = normalize_folder_name(conn.provider, folder)
        
        # Select folder (read-write)
        status, _ = conn.connection.select(folder, readonly=False)
        if status != 'OK':
            return {"success": False, "error": f"Failed to select folder: {folder}"}
        
        # Mark as deleted
        status, _ = conn.connection.uid('STORE', message_id, '+FLAGS', '\\Deleted')
        if status != 'OK':
            return {"success": False, "error": "Failed to mark as deleted"}
        
        # Expunge if requested
        if expunge:
            conn.connection.expunge()
        
        return {
            "success": True,
            "message_id": message_id,
            "folder": folder,
            "expunged": expunge
        }
    
    except Exception as e:
        return {"success": False, "error": f"Delete failed: {str(e)}"}


def op_delete_messages_batch(conn: IMAPConnection, message_ids: List[str], folder: str = "INBOX", expunge: bool = True) -> Dict[str, Any]:
    """Delete multiple messages in one call"""
    try:
        folder = normalize_folder_name(conn.provider, folder)
        
        # Select folder (read-write)
        status, _ = conn.connection.select(folder, readonly=False)
        if status != 'OK':
            return {"success": False, "error": f"Failed to select folder: {folder}"}
        
        deleted = []
        failed = []
        
        for msg_id in message_ids:
            try:
                status, _ = conn.connection.uid('STORE', msg_id, '+FLAGS', '\\Deleted')
                if status == 'OK':
                    deleted.append(msg_id)
                else:
                    failed.append({"id": msg_id, "error": "Failed to mark as deleted"})
            except Exception as e:
                failed.append({"id": msg_id, "error": str(e)})
        
        # Expunge if requested
        if expunge:
            conn.connection.expunge()
        
        return {
            "success": len(failed) == 0,
            "deleted": deleted,
            "deleted_count": len(deleted),
            "failed": failed,
            "failed_count": len(failed),
            "folder": folder,
            "expunged": expunge
        }
    
    except Exception as e:
        return {"success": False, "error": f"Batch delete failed: {str(e)}"}


def _set_flag(conn: IMAPConnection, message_id: str, folder: str, flag: str, add: bool = True) -> Dict[str, Any]:
    """Internal helper to set/unset a flag"""
    try:
        folder = normalize_folder_name(conn.provider, folder)
        
        # Select folder (read-write)
        status, _ = conn.connection.select(folder, readonly=False)
        if status != 'OK':
            return {"success": False, "error": f"Failed to select folder: {folder}"}
        
        # Set flag
        cmd = '+FLAGS' if add else '-FLAGS'
        status, _ = conn.connection.uid('STORE', message_id, cmd, flag)
        if status != 'OK':
            return {"success": False, "error": f"Failed to set flag: {flag}"}
        
        return {
            "success": True,
            "message_id": message_id,
            "folder": folder,
            "flag": flag,
            "action": "added" if add else "removed"
        }
    
    except Exception as e:
        return {"success": False, "error": f"Set flag failed: {str(e)}"}


def _set_flag_batch(conn: IMAPConnection, message_ids: List[str], folder: str, flag: str, add: bool = True) -> Dict[str, Any]:
    """Internal helper to set/unset a flag on multiple messages"""
    try:
        folder = normalize_folder_name(conn.provider, folder)
        
        # Select folder (read-write)
        status, _ = conn.connection.select(folder, readonly=False)
        if status != 'OK':
            return {"success": False, "error": f"Failed to select folder: {folder}"}
        
        cmd = '+FLAGS' if add else '-FLAGS'
        updated = []
        failed = []
        
        for msg_id in message_ids:
            try:
                status, _ = conn.connection.uid('STORE', msg_id, cmd, flag)
                if status == 'OK':
                    updated.append(msg_id)
                else:
                    failed.append({"id": msg_id, "error": f"Failed to set flag: {flag}"})
            except Exception as e:
                failed.append({"id": msg_id, "error": str(e)})
        
        return {
            "success": len(failed) == 0,
            "updated": updated,
            "updated_count": len(updated),
            "failed": failed,
            "failed_count": len(failed),
            "folder": folder,
            "flag": flag,
            "action": "added" if add else "removed"
        }
    
    except Exception as e:
        return {"success": False, "error": f"Batch set flag failed: {str(e)}"}
