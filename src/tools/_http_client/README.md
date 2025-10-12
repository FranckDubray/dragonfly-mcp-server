# HTTP Client Module

Universal HTTP/REST client with comprehensive features.

## Features

- **All HTTP methods**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Authentication**: Basic, Bearer, API Key
- **Retry logic**: Exponential backoff (0-5 retries)
- **Timeouts**: Configurable (1-600s, default: 30s)
- **Response parsing**: Auto-detect JSON/text, or force format
- **Proxy support**: HTTP/HTTPS/SOCKS5
- **SSL verification**: Configurable (default: enabled)
- **Response saving**: Optional file save (JSON format)
- **Error handling**: Typed errors (connection, timeout, SSL, request)
- **Logging**: INFO for requests, WARNING for errors/large bodies

## Architecture

```
_http_client/
├── __init__.py       # Spec loader
├── api.py            # Request routing (636 B)
├── core.py           # Main execution logic (6.9 KB)
├── auth.py           # Authentication helpers (3 KB)
├── validators.py     # Input validation (4.4 KB)
├── utils.py          # Response parsing + saving (4 KB)
├── retry.py          # Retry with backoff (1.8 KB)
└── README.md         # This file
```

All files < 7KB ✅

## Usage Examples

### Basic GET

```json
{
  "tool": "http_client",
  "params": {
    "method": "GET",
    "url": "https://api.github.com/zen"
  }
}
```

### GET with query params

```json
{
  "tool": "http_client",
  "params": {
    "method": "GET",
    "url": "https://api.github.com/search/repositories",
    "params": {"q": "fastapi", "per_page": "5"}
  }
}
```

### POST with JSON body + Bearer auth

```json
{
  "tool": "http_client",
  "params": {
    "method": "POST",
    "url": "https://api.example.com/data",
    "json": {"name": "test", "value": 42},
    "auth_type": "bearer",
    "auth_token": "your_token_here"
  }
}
```

### GET with retry + timeout

```json
{
  "tool": "http_client",
  "params": {
    "method": "GET",
    "url": "https://unreliable-api.com/data",
    "timeout": 10,
    "max_retries": 3,
    "retry_delay": 2.0
  }
}
```

### POST with Basic Auth

```json
{
  "tool": "http_client",
  "params": {
    "method": "POST",
    "url": "https://api.example.com/secure",
    "auth_type": "basic",
    "auth_user": "username",
    "auth_password": "password"
  }
}
```

### GET with API Key header

```json
{
  "tool": "http_client",
  "params": {
    "method": "GET",
    "url": "https://api.example.com/data",
    "auth_type": "api_key",
    "auth_api_key_name": "X-API-Key",
    "auth_api_key_value": "your_api_key"
  }
}
```

### GET with custom headers + proxy

```json
{
  "tool": "http_client",
  "params": {
    "method": "GET",
    "url": "https://api.example.com/data",
    "headers": {"Accept": "application/json", "User-Agent": "MyApp/1.0"},
    "proxy": "http://proxy.company.com:8080"
  }
}
```

### POST with form data

```json
{
  "tool": "http_client",
  "params": {
    "method": "POST",
    "url": "https://example.com/login",
    "form_data": {"username": "user", "password": "pass"}
  }
}
```

### GET with response saving

```json
{
  "tool": "http_client",
  "params": {
    "method": "GET",
    "url": "https://api.example.com/large-dataset",
    "save_response": true
  }
}
```

## Response Format

**Success response:**

```json
{
  "status_code": 200,
  "ok": true,
  "headers": {"Content-Type": "application/json", ...},
  "body": "...",
  "body_length": 1234,
  "request": {
    "method": "GET",
    "url": "https://...",
    "timeout": 30
  }
}
```

**Error response:**

```json
{
  "error": "Connection error: ...",
  "error_type": "connection"
}
```

**Error types:**
- `connection` — Network/DNS error
- `timeout` — Request timed out
- `ssl` — SSL certificate error
- `request` — Other HTTP error
- `unknown` — Unexpected error

## Truncation Warnings

**Large responses** (> 100 KB) trigger a warning:

```json
{
  "status_code": 200,
  "ok": true,
  "body": "...",
  "body_length": 256789,
  "truncation_warning": "Response body is large: 250.8 KB"
}
```

## Validation

**All inputs are validated:**

- URL: must use `http://` or `https://`, valid domain
- Timeout: 1-600 seconds
- Max retries: 0-5
- Retry delay: 0.1-10.0 seconds
- Proxy: valid URL (http/https/socks5)
- Auth: complete credentials for auth_type

**Validation errors** return immediately:

```json
{
  "error": "Timeout must be at least 1 second"
}
```

## Retry Logic

**Exponential backoff** for retry:

```python
delay = retry_delay * (2 ** attempt)
```

Example with `max_retries=3, retry_delay=1.0`:
- Attempt 1: immediate
- Attempt 2: wait 1s
- Attempt 3: wait 2s
- Attempt 4: wait 4s

**Should retry on:**
- 408 (Request Timeout)
- 429 (Too Many Requests)
- 500 (Internal Server Error)
- 502 (Bad Gateway)
- 503 (Service Unavailable)
- 504 (Gateway Timeout)

## Performance

- **No event loop blocking**: requests library is synchronous, but called in thread executor via `/execute` endpoint
- **Configurable timeouts**: prevent hanging requests
- **Retry with backoff**: avoid hammering failing endpoints
- **Response size warning**: alerts for large payloads (> 100 KB)

## Security

- **SSL verification** enabled by default (`verify_ssl: true`)
- **Timeout enforcement**: prevents indefinite waiting
- **URL validation**: only http/https schemes allowed
- **No secret logging**: auth tokens not logged (warning: not yet masked in error messages)

## Logging

**INFO level:**
- Request start: `🌐 GET https://... (timeout: 30s, retries: 0)`
- Request success: `✅ GET https://... → 200 (1234 bytes)`

**WARNING level:**
- HTTP errors: `⚠️ GET https://... → 404 (HTTP error)`
- Large responses: `⚠️ Large response body: 256789 bytes (250.8 KB)`
- Network errors: `❌ Connection error: GET https://...`
- Timeouts: `⏱️ Timeout: GET https://... after 30s`
- SSL errors: `🔒 SSL error: GET https://...`

**ERROR level:**
- Unexpected exceptions: `💥 Unexpected error: GET https://... - ...`

## Known Limitations

1. **No secret masking in errors**: Auth tokens/passwords may appear in exception messages (to be fixed)
2. **No streaming response support**: entire body loaded into memory
3. **No file upload support**: only JSON/form/raw body
4. **No async support**: uses synchronous requests library

## Dependencies

- `requests` (2.32+) — HTTP library

## Maintainer Notes

- **Keep files < 7KB**: split if needed
- **No code duplication**: use shared helpers
- **Validate everything**: fail fast with clear errors
- **Log important events**: INFO for flow, WARNING for issues
- **Test edge cases**: timeouts, retries, large responses, bad URLs
