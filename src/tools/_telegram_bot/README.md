# Telegram Bot Tool

Complete Telegram Bot API access for sending messages, managing chats, and retrieving updates.

## Features

- ✅ **10 operations** for comprehensive bot management
- ✅ **Free & unlimited** (no API key limits)
- ✅ **Secure** (token masking in logs/errors)
- ✅ **Real-time** updates with long polling support
- ✅ **Rich content** (text, photos, documents, videos, locations, polls)
- ✅ **Formatting** (Markdown, HTML support)

---

## Configuration

Required environment variable:
```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

To create a bot:
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow instructions to get your bot token
4. Add token to `.env` file

---

## Operations

### 1. get_me
Get bot information (username, ID, capabilities).

**Parameters**: None

**Example**:
```json
{
  "operation": "get_me"
}
```

**Returns**:
```json
{
  "bot_info": {
    "id": 123456789,
    "is_bot": true,
    "first_name": "My Bot",
    "username": "mybot",
    "can_join_groups": true,
    "can_read_all_group_messages": false,
    "supports_inline_queries": false
  }
}
```

---

### 2. get_updates
Retrieve new messages and events. Supports long polling.

**Parameters**:
- `limit` (integer, optional): Max updates to retrieve (default: 20, max: 100)
- `timeout` (integer, optional): Long polling timeout in seconds (default: 0, max: 50)
- `offset` (integer, optional): Update offset for pagination (use `latest_update_id + 1` to acknowledge)

**Example**:
```json
{
  "operation": "get_updates",
  "limit": 10,
  "timeout": 30
}
```

**Returns**:
```json
{
  "updates": [
    {
      "update_id": 123456789,
      "message": {
        "message_id": 1,
        "date": 1234567890,
        "chat": {
          "id": 987654321,
          "type": "private",
          "first_name": "John"
        },
        "from": {
          "id": 987654321,
          "is_bot": false,
          "first_name": "John"
        },
        "text": "Hello!"
      }
    }
  ],
  "returned_count": 1,
  "latest_update_id": 123456789
}
```

---

### 3. send_message
Send text message to a chat.

**Parameters**:
- `chat_id` (string, required): Chat ID, user ID, or channel username (@channelname)
- `text` (string, required): Message text (max 4096 chars)
- `parse_mode` (string, optional): "Markdown", "MarkdownV2", or "HTML" (default: "Markdown")
- `disable_notification` (boolean, optional): Silent message (default: false)
- `reply_to_message_id` (integer, optional): Reply to specific message

**Example**:
```json
{
  "operation": "send_message",
  "chat_id": "987654321",
  "text": "Hello from my bot!",
  "parse_mode": "Markdown"
}
```

---

### 4. send_photo
Send photo message.

**Parameters**:
- `chat_id` (string, required)
- `photo` (string, required): Photo URL or file_id
- `caption` (string, optional): Photo caption (max 1024 chars)
- `parse_mode` (string, optional): Caption formatting
- `disable_notification` (boolean, optional)
- `reply_to_message_id` (integer, optional)

**Example**:
```json
{
  "operation": "send_photo",
  "chat_id": "987654321",
  "photo": "https://example.com/image.jpg",
  "caption": "Check out this photo!"
}
```

---

### 5. send_document
Send document file (PDF, ZIP, etc.).

**Parameters**:
- `chat_id` (string, required)
- `document` (string, required): Document URL or file_id
- `caption` (string, optional)
- `parse_mode` (string, optional)
- `disable_notification` (boolean, optional)
- `reply_to_message_id` (integer, optional)

---

### 6. send_video
Send video file.

**Parameters**:
- `chat_id` (string, required)
- `video` (string, required): Video URL or file_id
- `caption` (string, optional)
- `parse_mode` (string, optional)
- `disable_notification` (boolean, optional)
- `reply_to_message_id` (integer, optional)

---

### 7. send_location
Send GPS location.

**Parameters**:
- `chat_id` (string, required)
- `latitude` (number, required): -90 to 90
- `longitude` (number, required): -180 to 180
- `disable_notification` (boolean, optional)
- `reply_to_message_id` (integer, optional)

**Example**:
```json
{
  "operation": "send_location",
  "chat_id": "987654321",
  "latitude": 48.8566,
  "longitude": 2.3522
}
```

---

### 8. send_poll
Create a poll/survey.

**Parameters**:
- `chat_id` (string, required)
- `question` (string, required): Poll question (max 300 chars)
- `options` (array, required): Poll options (2-10 items, each max 100 chars)
- `is_anonymous` (boolean, optional): Anonymous poll (default: true)
- `allows_multiple_answers` (boolean, optional): Allow multiple selections (default: false)
- `disable_notification` (boolean, optional)
- `reply_to_message_id` (integer, optional)

**Example**:
```json
{
  "operation": "send_poll",
  "chat_id": "987654321",
  "question": "What's your favorite color?",
  "options": ["Red", "Blue", "Green"],
  "is_anonymous": true,
  "allows_multiple_answers": false
}
```

---

### 9. edit_message
Edit existing text message.

**Parameters**:
- `chat_id` (string, required)
- `message_id` (integer, required): Message to edit
- `text` (string, required): New text (max 4096 chars)
- `parse_mode` (string, optional)

**Example**:
```json
{
  "operation": "edit_message",
  "chat_id": "987654321",
  "message_id": 123,
  "text": "Updated message text"
}
```

---

### 10. delete_message
Delete a message.

**Parameters**:
- `chat_id` (string, required)
- `message_id` (integer, required): Message to delete

**Example**:
```json
{
  "operation": "delete_message",
  "chat_id": "987654321",
  "message_id": 123
}
```

---

## Tips & Best Practices

### Finding Chat IDs

Use `get_updates` to discover chat IDs:
1. Send a message to your bot in Telegram
2. Call `get_updates`
3. Extract `chat.id` from the response

### Long Polling for Real-time

For real-time bot responses, use long polling:
```json
{
  "operation": "get_updates",
  "timeout": 30,
  "offset": 123456790
}
```

This keeps the connection open for 30s, reducing API calls and latency.

### Acknowledging Updates

To prevent receiving duplicate updates, use the offset parameter:
```json
{
  "operation": "get_updates",
  "offset": 123456790
}
```

Set `offset` to `latest_update_id + 1` from previous response.

### Truncation & Pagination

If you receive `returned_count == limit`, there may be more updates available.
Use pagination to retrieve remaining updates:
```json
{
  "operation": "get_updates",
  "limit": 100,
  "offset": 123456790
}
```

### Text Formatting

**Markdown** (default):
```
*bold* _italic_ `code` [link](url)
```

**HTML**:
```html
<b>bold</b> <i>italic</i> <code>code</code> <a href="url">link</a>
```

### Rate Limits

Telegram Bot API has global rate limits:
- **Normal messages**: 30 messages/second
- **Group messages**: 20 messages/minute per group
- **Same user**: 1 message/second

The tool automatically handles rate limit errors (HTTP 429).

---

## Error Handling

All errors return:
```json
{
  "error": "Error message",
  "error_type": "ValueError"
}
```

Common errors:
- `"Missing TELEGRAM_BOT_TOKEN"`: Set token in `.env`
- `"send_message requires 'chat_id'"`: Missing required parameter
- `"Invalid TELEGRAM_BOT_TOKEN"`: Wrong/expired token
- `"Bad request: chat not found"`: Invalid chat_id
- `"Too many requests"`: Rate limited (retry after delay)

**Security**: Bot tokens are automatically masked in error messages for security.

---

## Architecture

```
_telegram_bot/
├── __init__.py           # Package init
├── api.py                # Operation routing
├── core.py               # Business logic (10 handlers)
├── validators.py         # Parameter validation
├── utils.py              # Message/update formatting
└── services/
    ├── __init__.py
    └── api_client.py     # Telegram API HTTP client
```

**Logging**: All operations log info/warnings to help debugging.

---

## Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [BotFather](https://t.me/BotFather) - Create bots
- [Telegram Bot Features](https://core.telegram.org/bots/features)
