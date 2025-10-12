"""
Telegram Bot API routing
"""
from .validators import validate_params
from .core import (
    send_text_message,
    send_photo_message,
    send_document_message,
    send_location_message,
    send_video_message,
    get_bot_updates,
    get_bot_info,
    delete_bot_message,
    edit_bot_message,
    send_bot_poll
)


def route_operation(**params):
    """Route to appropriate handler based on operation"""
    try:
        # Validate and normalize params
        validated = validate_params(params)
        operation = validated['operation']
        
        # Route to handlers
        if operation == 'send_message':
            return send_text_message(validated)
        elif operation == 'send_photo':
            return send_photo_message(validated)
        elif operation == 'send_document':
            return send_document_message(validated)
        elif operation == 'send_location':
            return send_location_message(validated)
        elif operation == 'send_video':
            return send_video_message(validated)
        elif operation == 'get_updates':
            return get_bot_updates(validated)
        elif operation == 'get_me':
            return get_bot_info(validated)
        elif operation == 'delete_message':
            return delete_bot_message(validated)
        elif operation == 'edit_message':
            return edit_bot_message(validated)
        elif operation == 'send_poll':
            return send_bot_poll(validated)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        return {
            'error': str(e),
            'error_type': type(e).__name__
        }
