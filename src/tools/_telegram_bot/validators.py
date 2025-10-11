"""
Input validation for Telegram Bot operations
"""


def validate_params(params):
    """Validate and normalize parameters"""
    operation = params.get('operation')
    if not operation:
        raise ValueError("Missing required parameter: operation")
    
    # Validate operation-specific requirements
    if operation in ['send_message', 'send_photo', 'send_document', 'send_location', 'send_video', 'delete_message', 'edit_message', 'send_poll']:
        if not params.get('chat_id'):
            raise ValueError(f"{operation} requires 'chat_id'")
    
    if operation == 'send_message':
        if not params.get('text'):
            raise ValueError("send_message requires 'text'")
        if len(params['text']) > 4096:
            raise ValueError("text must be max 4096 characters")
    
    elif operation == 'send_photo':
        if not params.get('photo'):
            raise ValueError("send_photo requires 'photo' (URL or file_id)")
    
    elif operation == 'send_document':
        if not params.get('document'):
            raise ValueError("send_document requires 'document' (URL or file_id)")
    
    elif operation == 'send_video':
        if not params.get('video'):
            raise ValueError("send_video requires 'video' (URL or file_id)")
    
    elif operation == 'send_location':
        if not (params.get('latitude') is not None and params.get('longitude') is not None):
            raise ValueError("send_location requires 'latitude' and 'longitude'")
        # Validate coordinates
        lat = params['latitude']
        lon = params['longitude']
        if not isinstance(lat, (int, float)) or lat < -90 or lat > 90:
            raise ValueError("latitude must be a number between -90 and 90")
        if not isinstance(lon, (int, float)) or lon < -180 or lon > 180:
            raise ValueError("longitude must be a number between -180 and 180")
    
    elif operation in ['delete_message', 'edit_message']:
        if not params.get('message_id'):
            raise ValueError(f"{operation} requires 'message_id'")
    
    elif operation == 'edit_message':
        if not params.get('text'):
            raise ValueError("edit_message requires 'text'")
        if len(params['text']) > 4096:
            raise ValueError("text must be max 4096 characters")
    
    elif operation == 'send_poll':
        if not params.get('question'):
            raise ValueError("send_poll requires 'question'")
        if len(params['question']) > 300:
            raise ValueError("question must be max 300 characters")
        if not params.get('options'):
            raise ValueError("send_poll requires 'options' array")
        if not isinstance(params['options'], list):
            raise ValueError("options must be an array")
        if len(params['options']) < 2 or len(params['options']) > 10:
            raise ValueError("options must have 2-10 items")
        for opt in params['options']:
            if len(opt) > 100:
                raise ValueError("Each poll option must be max 100 characters")
    
    # Validate caption length if provided
    if params.get('caption') and len(params['caption']) > 1024:
        raise ValueError("caption must be max 1024 characters")
    
    # Set defaults
    validated = params.copy()
    validated.setdefault('parse_mode', 'Markdown')
    validated.setdefault('disable_notification', False)
    validated.setdefault('is_anonymous', True)
    validated.setdefault('allows_multiple_answers', False)
    validated.setdefault('limit', 20)
    validated.setdefault('timeout', 0)
    
    return validated
