# Trivia API Tool

Complete Open Trivia Database API client for quiz/trivia questions.

## Features

- **24 categories** (General Knowledge, Science, Entertainment, Sports, etc.)
- **Multiple choice** and **True/False** questions
- **3 difficulty levels** (easy, medium, hard)
- **Session tokens** to avoid duplicate questions
- **Base64/URL encoding** support for special characters
- **Rate limiting** (1 req/sec minimum, auto-retry on code 5)
- **100% free** - no API key required

## Operations

### get_questions
Retrieve trivia questions with filters.

**Parameters:**
- `amount` (int, default: 10, max: 50) - Number of questions
- `category` (int, optional) - Category ID (9-32)
- `difficulty` (string, optional) - "easy", "medium", "hard"
- `type` (string, optional) - "multiple" or "boolean"
- `encode` (string, default: "base64") - Encoding type
- `token` (string, optional) - Session token

**Returns:**
- `count` - Number of questions returned
- `questions` - Array of question objects with shuffled answers

### list_categories
Get all available trivia categories.

**Returns:**
- `count` - Number of categories
- `categories` - Array of category objects (id + name)

### get_category_count
Get question count for a specific category.

**Parameters:**
- `category` (int, required) - Category ID (9-32)

**Returns:**
- `category_id` - Category ID
- `counts` - Question counts by difficulty (total, easy, medium, hard)

### get_global_count
Get global question counts across all categories.

**Returns:**
- `overall` - Total question counts
- `categories` - Per-category breakdown

### create_session_token
Create a session token to track used questions.

**Returns:**
- `token` - Session token string (64 chars)

### reset_session_token
Reset a session token to replay all questions.

**Parameters:**
- `token` (string, required) - Token to reset

**Returns:**
- `token` - Reset token

## Response Codes

API returns response codes in responses:
- `0` - Success
- `1` - No results (invalid amount)
- `2` - Not enough questions for filters
- `3` - Token not found
- `4` - Token empty (reset needed)
- `5` - Rate limit (auto-retry after 5s)

## Examples

### Get 10 random questions
```json
{
  "operation": "get_questions",
  "amount": 10
}
```

### Get Science questions (medium difficulty)
```json
{
  "operation": "get_questions",
  "amount": 5,
  "category": 18,
  "difficulty": "medium"
}
```

### Session workflow
```json
// 1. Create token
{"operation": "create_session_token"}
// Returns: {"token": "abc123..."}

// 2. Use token in questions
{"operation": "get_questions", "amount": 10, "token": "abc123..."}

// 3. Reset when exhausted
{"operation": "reset_session_token", "token": "abc123..."}
```

## Architecture

- `trivia_api.py` - Bootstrap (spec + run)
- `api.py` - Routing + error handling
- `core.py` - Business logic
- `utils.py` - Helpers (decode, parse, format)
- `validators.py` - Parameter validation
- `services/api_client.py` - HTTP client (rate limiting, retries)

## Technical Details

- **Rate limiting**: 1 second minimum between requests
- **Timeout**: 10 seconds per request
- **Retry**: Auto-retry on rate limit (code 5) after 5s
- **Encoding**: Base64 default (handles special chars)
- **Shuffling**: Answers shuffled with `correct_answer_index` provided
- **Validation**: Strict param validation (amount 1-50, category 9-32)

## Error Handling

All operations return structured errors:
- **Validation errors** - Invalid parameters
- **API errors** - External API issues (timeout, connection, HTTP errors)
- **Type errors** - Wrong parameter types

## Conformity

✅ Category: `entertainment`
✅ Tags: `quiz`, `games`, `educational`, `trivia`
✅ Logging: INFO/WARNING levels
✅ Outputs: Minimal (count + data only)
✅ Validation: Strict limits enforced
✅ Error handling: Try-catch at routing level
✅ Files: All < 7KB

## API Reference

Open Trivia Database: https://opentdb.com/api_config.php
