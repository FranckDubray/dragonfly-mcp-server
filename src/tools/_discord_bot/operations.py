"""
Discord Bot: Main operations router (29 ops - updated).
"""
from __future__ import annotations
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

try:
    from .ops_messages import (
        op_list_messages, op_get_message, op_send_message, op_edit_message,
        op_delete_message, op_bulk_delete, op_pin_message, op_unpin_message
    )
    from .ops_channels import (
        op_list_channels, op_get_channel, op_create_channel,
        op_modify_channel, op_delete_channel
    )
    from .ops_reactions import (
        op_add_reaction, op_remove_reaction, op_get_reactions
    )
    from .ops_threads import (
        op_create_thread, op_list_threads, op_join_thread,
        op_leave_thread, op_archive_thread
    )
    from .ops_utility import (
        op_list_guilds, op_search_messages, op_get_guild_info, op_list_members,
        op_get_permissions, op_get_user, op_list_emojis, op_health_check
    )
except Exception:
    from src.tools._discord_bot.ops_messages import (
        op_list_messages, op_get_message, op_send_message, op_edit_message,
        op_delete_message, op_bulk_delete, op_pin_message, op_unpin_message
    )
    from src.tools._discord_bot.ops_channels import (
        op_list_channels, op_get_channel, op_create_channel,
        op_modify_channel, op_delete_channel
    )
    from src.tools._discord_bot.ops_reactions import (
        op_add_reaction, op_remove_reaction, op_get_reactions
    )
    from src.tools._discord_bot.ops_threads import (
        op_create_thread, op_list_threads, op_join_thread,
        op_leave_thread, op_archive_thread
    )
    from src.tools._discord_bot.ops_utility import (
        op_list_guilds, op_search_messages, op_get_guild_info, op_list_members,
        op_get_permissions, op_get_user, op_list_emojis, op_health_check
    )

OPERATIONS_MAP = {
    # Messages (8)
    "list_messages": op_list_messages,
    "get_message": op_get_message,
    "send_message": op_send_message,
    "edit_message": op_edit_message,
    "delete_message": op_delete_message,
    "bulk_delete": op_bulk_delete,
    "pin_message": op_pin_message,
    "unpin_message": op_unpin_message,
    
    # Channels (5)
    "list_channels": op_list_channels,
    "get_channel": op_get_channel,
    "create_channel": op_create_channel,
    "modify_channel": op_modify_channel,
    "delete_channel": op_delete_channel,
    
    # Reactions (3)
    "add_reaction": op_add_reaction,
    "remove_reaction": op_remove_reaction,
    "get_reactions": op_get_reactions,
    
    # Threads (5)
    "create_thread": op_create_thread,
    "list_threads": op_list_threads,
    "join_thread": op_join_thread,
    "leave_thread": op_leave_thread,
    "archive_thread": op_archive_thread,
    
    # Utility (8 - updated)
    "list_guilds": op_list_guilds,
    "search_messages": op_search_messages,
    "get_guild_info": op_get_guild_info,
    "list_members": op_list_members,
    "get_permissions": op_get_permissions,
    "get_user": op_get_user,
    "list_emojis": op_list_emojis,
    "health_check": op_health_check,
}

def run_operation(**params) -> Any:
    """Main entry point for discord_bot operations."""
    operation = params.get("operation")
    
    if not operation:
        return {
            "error": "Missing required parameter: 'operation'",
            "available_operations": list(OPERATIONS_MAP.keys())
        }
    
    handler = OPERATIONS_MAP.get(operation)
    
    if not handler:
        return {
            "error": f"Unknown operation: '{operation}'",
            "available_operations": list(OPERATIONS_MAP.keys())
        }
    
    try:
        return handler(params)
    except ValueError as e:
        logger.error(f"discord_bot validation error in {operation}: {e}")
        return {"error": f"Validation error: {str(e)}"}
    except RuntimeError as e:
        logger.error(f"discord_bot runtime error in {operation}: {e}")
        return {"error": f"Runtime error: {str(e)}"}
    except Exception as e:
        logger.exception(f"discord_bot unexpected error in {operation}")
        return {
            "error": f"Unexpected error in operation '{operation}': {type(e).__name__}: {str(e)}",
            "operation": operation,
            "error_type": type(e).__name__
        }
