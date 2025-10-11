"""
Utility functions for Telegram Bot
"""


def format_message(data):
    """Format message result"""
    chat = data.get('chat', {})
    from_user = data.get('from', {})
    
    formatted = {
        'message_id': data.get('message_id'),
        'date': data.get('date'),
        'chat': {
            'id': chat.get('id'),
            'type': chat.get('type'),
            'title': chat.get('title'),
            'username': chat.get('username'),
            'first_name': chat.get('first_name'),
            'last_name': chat.get('last_name')
        },
        'from': {
            'id': from_user.get('id'),
            'is_bot': from_user.get('is_bot'),
            'first_name': from_user.get('first_name'),
            'username': from_user.get('username')
        } if from_user else None
    }
    
    # Add content fields if present
    if 'text' in data:
        formatted['text'] = data['text']
    
    if 'caption' in data:
        formatted['caption'] = data['caption']
    
    if 'photo' in data:
        # Photo is array of different sizes, take largest
        photos = data['photo']
        if photos:
            largest = max(photos, key=lambda p: p.get('file_size', 0))
            formatted['photo'] = {
                'file_id': largest.get('file_id'),
                'file_unique_id': largest.get('file_unique_id'),
                'width': largest.get('width'),
                'height': largest.get('height'),
                'file_size': largest.get('file_size')
            }
    
    if 'document' in data:
        doc = data['document']
        formatted['document'] = {
            'file_id': doc.get('file_id'),
            'file_unique_id': doc.get('file_unique_id'),
            'file_name': doc.get('file_name'),
            'mime_type': doc.get('mime_type'),
            'file_size': doc.get('file_size')
        }
    
    if 'video' in data:
        video = data['video']
        formatted['video'] = {
            'file_id': video.get('file_id'),
            'file_unique_id': video.get('file_unique_id'),
            'width': video.get('width'),
            'height': video.get('height'),
            'duration': video.get('duration'),
            'mime_type': video.get('mime_type'),
            'file_size': video.get('file_size')
        }
    
    if 'location' in data:
        loc = data['location']
        formatted['location'] = {
            'latitude': loc.get('latitude'),
            'longitude': loc.get('longitude')
        }
    
    if 'poll' in data:
        poll = data['poll']
        formatted['poll'] = {
            'id': poll.get('id'),
            'question': poll.get('question'),
            'options': [
                {
                    'text': opt.get('text'),
                    'voter_count': opt.get('voter_count')
                }
                for opt in poll.get('options', [])
            ],
            'is_closed': poll.get('is_closed'),
            'is_anonymous': poll.get('is_anonymous'),
            'allows_multiple_answers': poll.get('allows_multiple_answers')
        }
    
    return formatted


def format_update(data):
    """Format update result"""
    formatted = {
        'update_id': data.get('update_id')
    }
    
    # Update can contain different types of content
    if 'message' in data:
        formatted['message'] = format_message(data['message'])
    
    if 'edited_message' in data:
        formatted['edited_message'] = format_message(data['edited_message'])
    
    if 'channel_post' in data:
        formatted['channel_post'] = format_message(data['channel_post'])
    
    if 'edited_channel_post' in data:
        formatted['edited_channel_post'] = format_message(data['edited_channel_post'])
    
    if 'callback_query' in data:
        callback = data['callback_query']
        formatted['callback_query'] = {
            'id': callback.get('id'),
            'from': {
                'id': callback.get('from', {}).get('id'),
                'first_name': callback.get('from', {}).get('first_name'),
                'username': callback.get('from', {}).get('username')
            },
            'data': callback.get('data'),
            'message': format_message(callback['message']) if 'message' in callback else None
        }
    
    return formatted
