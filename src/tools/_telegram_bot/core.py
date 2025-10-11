"""
Telegram Bot core business logic
"""
from .services.api_client import make_request
from .utils import format_message, format_update


def send_text_message(params):
    """Send text message"""
    payload = {
        'chat_id': params['chat_id'],
        'text': params['text'],
        'parse_mode': params['parse_mode'],
        'disable_notification': params['disable_notification']
    }
    
    if params.get('reply_to_message_id'):
        payload['reply_to_message_id'] = params['reply_to_message_id']
    
    result = make_request('sendMessage', data=payload)
    
    return {
        'success': True,
        'operation': 'send_message',
        'message': format_message(result)
    }


def send_photo_message(params):
    """Send photo message"""
    payload = {
        'chat_id': params['chat_id'],
        'photo': params['photo'],
        'disable_notification': params['disable_notification']
    }
    
    if params.get('caption'):
        payload['caption'] = params['caption']
        payload['parse_mode'] = params['parse_mode']
    
    if params.get('reply_to_message_id'):
        payload['reply_to_message_id'] = params['reply_to_message_id']
    
    result = make_request('sendPhoto', data=payload)
    
    return {
        'success': True,
        'operation': 'send_photo',
        'message': format_message(result)
    }


def send_document_message(params):
    """Send document message"""
    payload = {
        'chat_id': params['chat_id'],
        'document': params['document'],
        'disable_notification': params['disable_notification']
    }
    
    if params.get('caption'):
        payload['caption'] = params['caption']
        payload['parse_mode'] = params['parse_mode']
    
    if params.get('reply_to_message_id'):
        payload['reply_to_message_id'] = params['reply_to_message_id']
    
    result = make_request('sendDocument', data=payload)
    
    return {
        'success': True,
        'operation': 'send_document',
        'message': format_message(result)
    }


def send_video_message(params):
    """Send video message"""
    payload = {
        'chat_id': params['chat_id'],
        'video': params['video'],
        'disable_notification': params['disable_notification']
    }
    
    if params.get('caption'):
        payload['caption'] = params['caption']
        payload['parse_mode'] = params['parse_mode']
    
    if params.get('reply_to_message_id'):
        payload['reply_to_message_id'] = params['reply_to_message_id']
    
    result = make_request('sendVideo', data=payload)
    
    return {
        'success': True,
        'operation': 'send_video',
        'message': format_message(result)
    }


def send_location_message(params):
    """Send location message"""
    payload = {
        'chat_id': params['chat_id'],
        'latitude': params['latitude'],
        'longitude': params['longitude'],
        'disable_notification': params['disable_notification']
    }
    
    if params.get('reply_to_message_id'):
        payload['reply_to_message_id'] = params['reply_to_message_id']
    
    result = make_request('sendLocation', data=payload)
    
    return {
        'success': True,
        'operation': 'send_location',
        'message': format_message(result)
    }


def get_bot_updates(params):
    """Get bot updates (messages, commands)"""
    query_params = {
        'limit': params['limit'],
        'timeout': params['timeout']
    }
    
    if params.get('offset'):
        query_params['offset'] = params['offset']
    
    # Use longer timeout for long polling
    request_timeout = params['timeout'] + 10 if params['timeout'] > 0 else 10
    
    result = make_request('getUpdates', params=query_params, timeout=request_timeout)
    
    # Result is an array of updates
    updates = result if isinstance(result, list) else []
    
    return {
        'success': True,
        'operation': 'get_updates',
        'updates': [format_update(u) for u in updates],
        'count': len(updates),
        'latest_update_id': updates[-1]['update_id'] if updates else None
    }


def get_bot_info(params):
    """Get bot information"""
    result = make_request('getMe')
    
    return {
        'success': True,
        'operation': 'get_me',
        'bot_info': {
            'id': result.get('id'),
            'is_bot': result.get('is_bot'),
            'first_name': result.get('first_name'),
            'username': result.get('username'),
            'can_join_groups': result.get('can_join_groups'),
            'can_read_all_group_messages': result.get('can_read_all_group_messages'),
            'supports_inline_queries': result.get('supports_inline_queries')
        }
    }


def delete_bot_message(params):
    """Delete a message"""
    payload = {
        'chat_id': params['chat_id'],
        'message_id': params['message_id']
    }
    
    result = make_request('deleteMessage', data=payload)
    
    return {
        'success': True,
        'operation': 'delete_message',
        'chat_id': params['chat_id'],
        'message_id': params['message_id'],
        'deleted': result
    }


def edit_bot_message(params):
    """Edit a message text"""
    payload = {
        'chat_id': params['chat_id'],
        'message_id': params['message_id'],
        'text': params['text'],
        'parse_mode': params['parse_mode']
    }
    
    result = make_request('editMessageText', data=payload)
    
    return {
        'success': True,
        'operation': 'edit_message',
        'message': format_message(result)
    }


def send_bot_poll(params):
    """Send a poll"""
    payload = {
        'chat_id': params['chat_id'],
        'question': params['question'],
        'options': params['options'],
        'is_anonymous': params['is_anonymous'],
        'allows_multiple_answers': params['allows_multiple_answers'],
        'disable_notification': params['disable_notification']
    }
    
    if params.get('reply_to_message_id'):
        payload['reply_to_message_id'] = params['reply_to_message_id']
    
    result = make_request('sendPoll', data=payload)
    
    return {
        'success': True,
        'operation': 'send_poll',
        'message': format_message(result)
    }
