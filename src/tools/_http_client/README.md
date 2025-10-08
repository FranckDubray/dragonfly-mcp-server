# HTTP Client Tool

Universal HTTP/REST client for interacting with any API.

## 🎯 Features

- **All HTTP methods**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Authentication**: Basic, Bearer, API Key
- **Body formats**: JSON, form-data, raw text
- **Retry logic**: Exponential backoff with configurable attempts
- **Timeout**: Configurable (1-300s)
- **Proxy**: HTTP/HTTPS/SOCKS5 support
- **SSL**: Verification toggle
- **Response parsing**: Auto-detect, JSON, text, raw
- **Save responses**: Optional file storage

---

## 📋 Parameters

### Required
- `method` (string): HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- `url` (string): Target URL (http:// or https://)

### Optional - Request
- `headers` (object): Custom HTTP headers
- `params` (object): Query string parameters
- `body` (string): Raw body (text/xml/etc.)
- `json` (object): JSON body (auto-serialized)
- `form_data` (object): Form data (application/x-www-form-urlencoded)

### Optional - Authentication
- `auth_type` (string): none, basic, bearer, api_key
- `auth_user` (string): Username for Basic Auth
- `auth_password` (string): Password for Basic Auth
- `auth_token` (string): Token for Bearer Auth
- `auth_api_key_name` (string): API Key header name
- `auth_api_key_value` (string): API Key value

### Optional - Behavior
- `timeout` (integer): Timeout in seconds (default: 30, min: 1, max: 300)
- `follow_redirects` (boolean): Follow redirects (default: true)
- `verify_ssl` (boolean): Verify SSL certificates (default: true)
- `proxy` (string): Proxy URL (http://proxy:port)
- `max_retries` (integer): Retry attempts (default: 0, max: 5)
- `retry_delay` (number): Delay between retries in seconds (default: 1.0)
- `response_format` (string): auto, json, text, raw (default: auto)
- `save_response` (boolean): Save response to files/http_responses/ (default: false)

---

## 📝 Examples

### Simple GET request
```json
{
  "method": "GET",
  "url": "https://api.github.com/users/octocat"
}
```

### GET with headers and query params
```json
{
  "method": "GET",
  "url": "https://api.example.com/search",
  "headers": {
    "Accept": "application/json",
    "User-Agent": "MyApp/1.0"
  },
  "params": {
    "q": "search term",
    "limit": "10"
  }
}
```

### POST with JSON body
```json
{
  "method": "POST",
  "url": "https://api.example.com/users",
  "json": {
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

### POST with form data
```json
{
  "method": "POST",
  "url": "https://api.example.com/login",
  "form_data": {
    "username": "user",
    "password": "pass"
  }
}
```

### Bearer Authentication
```json
{
  "method": "GET",
  "url": "https://api.example.com/protected",
  "auth_type": "bearer",
  "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Basic Authentication
```json
{
  "method": "GET",
  "url": "https://api.example.com/protected",
  "auth_type": "basic",
  "auth_user": "username",
  "auth_password": "password"
}
```

### API Key Authentication
```json
{
  "method": "GET",
  "url": "https://api.example.com/data",
  "auth_type": "api_key",
  "auth_api_key_name": "X-API-Key",
  "auth_api_key_value": "your_api_key_here"
}
```

### With retry logic
```json
{
  "method": "GET",
  "url": "https://api.example.com/unstable",
  "max_retries": 3,
  "retry_delay": 2.0,
  "timeout": 10
}
```

### With proxy
```json
{
  "method": "GET",
  "url": "https://api.example.com/data",
  "proxy": "http://proxy.company.com:8080"
}
```

### Save response to file
```json
{
  "method": "GET",
  "url": "https://api.example.com/large-data",
  "save_response": true
}
```

### Complex example (all options)
```json
{
  "method": "POST",
  "url": "https://api.example.com/orders",
  "headers": {
    "Content-Type": "application/json",
    "X-Request-ID": "12345"
  },
  "json": {
    "items": ["item1", "item2"],
    "total": 99.99
  },
  "auth_type": "bearer",
  "auth_token": "your_token",
  "timeout": 60,
  "max_retries": 2,
  "retry_delay": 1.5,
  "follow_redirects": true,
  "verify_ssl": true,
  "response_format": "json",
  "save_response": false
}
```

---

## 📊 Response Format

### Success response
```json
{
  "success": true,
  "status_code": 200,
  "headers": {
    "Content-Type": "application/json",
    "Content-Length": "1234"
  },
  "ok": true,
  "body": {"key": "value"},
  "body_length": 1234,
  "request": {
    "method": "GET",
    "url": "https://api.example.com/data"
  }
}
```

### Error response
```json
{
  "error": "Request timed out after 30 seconds",
  "error_type": "timeout"
}
```

**Error types:**
- `timeout`: Request exceeded timeout
- `connection`: Connection failed
- `ssl`: SSL certificate error
- `request`: General request error
- `unknown`: Unexpected error

---

## 🔒 Security

- **URL validation**: Only http:// and https:// allowed
- **Timeout enforcement**: Prevents infinite hangs (1-300s)
- **SSL verification**: Enabled by default
- **Auth masking**: Credentials not logged
- **Chroot saves**: Responses saved to `files/http_responses/`

---

## 🚀 Common Use Cases

### Testing an API
```json
{
  "method": "GET",
  "url": "https://jsonplaceholder.typicode.com/posts/1"
}
```

### Webhook callback
```json
{
  "method": "POST",
  "url": "https://webhook.site/unique-id",
  "json": {
    "event": "user.created",
    "user_id": 123
  }
}
```

### Health check with retry
```json
{
  "method": "HEAD",
  "url": "https://api.example.com/health",
  "max_retries": 5,
  "retry_delay": 1.0,
  "timeout": 5
}
```

### Download data
```json
{
  "method": "GET",
  "url": "https://api.example.com/reports/daily.json",
  "save_response": true,
  "timeout": 120
}
```

---

## 💡 Tips

1. **Always set timeout**: Prevents infinite waits
2. **Use retry for unreliable APIs**: `max_retries: 3` with exponential backoff
3. **Save large responses**: Enable `save_response` for big payloads
4. **Custom User-Agent**: Some APIs require it in headers
5. **API Keys in headers**: Use `api_key` auth type instead of manual headers
6. **SSL issues**: Disable `verify_ssl` only for trusted development endpoints

---

## 🐛 Troubleshooting

### Timeout errors
- Increase `timeout` value
- Check network connectivity
- Verify API is responsive

### Connection errors
- Check URL is correct
- Verify firewall/proxy settings
- Test with `curl` outside the tool

### SSL errors
- Verify certificate validity
- Update CA certificates
- Use `verify_ssl: false` for dev (not production!)

### Auth failures
- Double-check credentials
- Verify auth type matches API requirements
- Check token expiration

---

## 📦 Dependencies

- `requests` library (already in project dependencies)

---

## 🎯 Next Steps

- Batch requests (multiple URLs in one call)
- GraphQL support
- File upload (multipart/form-data)
- WebSocket connections
- Rate limiting
