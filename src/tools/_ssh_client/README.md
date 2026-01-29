# SSH Client Module

Universal SSH/SFTP client for remote command execution and file transfers.

## Features

- **Command Execution**: Run commands on remote servers with full stdout/stderr capture
- **File Upload**: Transfer files to remote servers via SFTP
- **File Download**: Retrieve files from remote servers via SFTP
- **Status Check**: Verify SSH connectivity and get server info
- **Authentication**: Password, SSH key, or SSH agent
- **Security**: Input validation, command injection prevention, secret masking
- **Logging**: INFO for operations, WARNING for errors, ERROR for failures

## Architecture

```
_ssh_client/
├── __init__.py       # Spec loader
├── api.py            # Operation routing (946 B)
├── core.py           # Command execution + status (9.1 KB)
├── auth.py           # Authentication (3.3 KB)
├── validators.py     # Input validation (6.9 KB)
├── sftp.py           # File transfers (9.8 KB)
├── utils.py          # Helpers (2.4 KB)
└── README.md         # This file
```

**Note**: `core.py` and `sftp.py` are slightly above 7KB but kept together for logical cohesion. If needed, can be split into `core_exec.py` + `core_status.py` and `sftp_upload.py` + `sftp_download.py`.

## Usage Examples

### 1. Execute Command (Password Auth)

```json
{
  "tool": "ssh_client",
  "params": {
    "operation": "exec",
    "host": "188.245.151.223",
    "username": "root",
    "auth_type": "password",
    "password": "your_password",
    "command": "ls -lah /var/www"
  }
}
```

**Response:**
```json
{
  "operation": "exec",
  "exit_code": 0,
  "stdout": "total 48K\ndrwxr-xr-x 12 root root 4.0K Jan 25 10:00 .\n...",
  "stderr": "",
  "duration_ms": 234,
  "host": "188.245.151.223",
  "username": "root",
  "command": "ls -lah /var/www",
  "truncated": false
}
```

---

### 2. Execute Command with Working Directory

```json
{
  "tool": "ssh_client",
  "params": {
    "operation": "exec",
    "host": "188.245.151.223",
    "username": "root",
    "auth_type": "password",
    "password": "...",
    "command": "python3 download_archives.py --status",
    "cwd": "/root/scripts"
  }
}
```

**Equivalent command executed:**
```bash
cd /root/scripts && python3 download_archives.py --status
```

---

### 3. Execute Command with Environment Variables

```json
{
  "tool": "ssh_client",
  "params": {
    "operation": "exec",
    "host": "188.245.151.223",
    "username": "root",
    "auth_type": "password",
    "password": "...",
    "command": "apt-get install -y python3-pip",
    "env": {"DEBIAN_FRONTEND": "noninteractive"},
    "sudo": true
  }
}
```

---

### 4. Execute Command with SSH Key

```json
{
  "tool": "ssh_client",
  "params": {
    "operation": "exec",
    "host": "server.example.com",
    "username": "ubuntu",
    "auth_type": "key",
    "key_file": "~/.ssh/id_rsa",
    "command": "systemctl status nginx"
  }
}
```

---

### 5. Upload File

```json
{
  "tool": "ssh_client",
  "params": {
    "operation": "upload",
    "host": "188.245.151.223",
    "username": "root",
    "auth_type": "password",
    "password": "...",
    "local_path": "files/scripts/download_archives.py",
    "remote_path": "/root/scripts/download_archives.py",
    "create_dirs": true
  }
}
```

**Response:**
```json
{
  "operation": "upload",
  "local_path": "files/scripts/download_archives.py",
  "remote_path": "/root/scripts/download_archives.py",
  "size_bytes": 15234,
  "transferred": true,
  "duration_ms": 456,
  "host": "188.245.151.223",
  "username": "root"
}
```

---

### 6. Download File

```json
{
  "tool": "ssh_client",
  "params": {
    "operation": "download",
    "host": "188.245.151.223",
    "username": "root",
    "auth_type": "password",
    "password": "...",
    "remote_path": "/var/log/app.log",
    "local_path": "files/logs/app.log"
  }
}
```

---

### 7. Check Connection Status

```json
{
  "tool": "ssh_client",
  "params": {
    "operation": "status",
    "host": "188.245.151.223",
    "username": "root",
    "auth_type": "password",
    "password": "..."
  }
}
```

**Response:**
```json
{
  "operation": "status",
  "connected": true,
  "host": "188.245.151.223",
  "port": 22,
  "username": "root",
  "os_info": "Linux legifrance-indexer 5.15.0-91-generic #101-Ubuntu SMP",
  "uptime": "up 2 hours, 34 minutes"
}
```

---

## Authentication Methods

### 1. Password (Simple)
```json
{
  "auth_type": "password",
  "password": "your_password"
}
```

**Pros**: Simple, works everywhere  
**Cons**: Less secure, password in plaintext

---

### 2. SSH Key (Recommended)
```json
{
  "auth_type": "key",
  "key_file": "~/.ssh/id_rsa",
  "key_passphrase": "optional_passphrase"
}
```

**Pros**: More secure, no password in params  
**Cons**: Requires key setup on server

---

### 3. SSH Agent (Most Secure)
```json
{
  "auth_type": "agent"
}
```

**Pros**: Most secure, keys managed by agent  
**Cons**: Requires SSH agent running

---

## Error Handling

### Error Types

- **`validation`**: Invalid input (host, port, path, command)
- **`authentication`**: Auth failed (wrong password/key)
- **`ssh`**: SSH protocol error
- **`timeout`**: Command/connection timed out
- **`file`**: File operation failed (not found, permission)
- **`connection`**: Network/connection error
- **`unknown`**: Unexpected error

### Error Response Example

```json
{
  "error": "Authentication failed: Invalid credentials",
  "error_type": "authentication",
  "host": "188.245.151.223",
  "username": "root"
}
```

---

## Security

### Input Validation

- **Host**: Only alphanumeric, dots, hyphens (prevents injection)
- **Port**: 1-65535
- **Command**: Detects dangerous patterns (`rm -rf /`, fork bombs, `mkfs.`)
- **Paths**: 
  - Local: Chrooted to `files/` (unless absolute)
  - Remote: No shell injection characters

### Secret Masking

- Passwords are logged as `****`
- SSH keys not logged
- Passphrases not logged

### Host Key Verification

- `strict`: Refuse if host key unknown (production)
- `auto_add`: Add unknown keys automatically (dev, default)
- `disabled`: No verification (dangerous)

---

## Performance

- **No event loop blocking**: Uses paramiko (sync) but called in thread via `/execute` endpoint
- **Configurable timeouts**: Default 30s, max 600s
- **Large output handling**: Warns if stdout/stderr > 100 KB
- **Connection pooling**: Not implemented (each call = new connection)

---

## Truncation Warnings

**Large outputs** (> 100 KB) trigger a warning:

```json
{
  "operation": "exec",
  "exit_code": 0,
  "stdout": "...",
  "stdout_length": 256789,
  "truncation_warning": "stdout is large: 250.8 KB",
  "truncated": false
}
```

**Note**: Currently not truncated, only warned. To add truncation, use `utils.truncate_output()`.

---

## Logging

### INFO Level

- Command start: `🔧 SSH exec: root@188.245.151.223:22 (auth=password, timeout=30s)`
- Command detail: `📝 Command: ls -lah`
- Upload: `📤 Uploading: file.txt → root@host:/path (1234 bytes)`
- Download: `📥 Downloading: root@host:/path → file.txt`
- Success: `✅ Command succeeded (exit_code=0, 234ms)`
- Status check: `🔍 Checking SSH status: root@host:22`

### WARNING Level

- Validation errors: `❌ Invalid host: ...`
- Command failure: `⚠️ Command failed (exit_code=1, 456ms)`
- Large output: `⚠️ Large stdout: 256789 bytes (250.8 KB)`

### ERROR Level

- Auth failed: `🔒 Authentication failed: ...`
- SSH error: `❌ SSH error: ...`
- Timeout: `⏱️ Timeout: ...`
- File error: `💾 File error: ...`
- Unexpected: `💥 Unexpected error: ...`

---

## Dependencies

```bash
pip install paramiko  # SSH/SFTP library
```

---

## Known Limitations

1. **No session persistence**: Each call opens a new connection (no connection pooling)
2. **No streaming**: Command output buffered entirely in memory
3. **No port forwarding**: Not implemented (could be added in v2)
4. **No X11 forwarding**: Not supported
5. **Interactive commands**: May hang (use `env` with `DEBIAN_FRONTEND=noninteractive`)
6. **Large file uploads**: No progress callback (blocking until complete)

---

## Maintainer Notes

- **Keep files < 7KB**: `core.py` (9KB) and `sftp.py` (10KB) can be split if needed
- **No code duplication**: Shared validation in `validators.py`
- **Validate everything**: Fail fast with clear errors
- **Log important events**: INFO for flow, WARNING for issues, ERROR for failures
- **Test edge cases**: Timeouts, auth failures, large outputs, dangerous commands
- **Mask secrets**: Never log passwords/keys

---

## Future Improvements (v2)

- **Connection pooling**: Reuse SSH connections for multiple commands
- **Port forwarding**: Add `operation=tunnel`
- **Batch commands**: Execute multiple commands in one call
- **Progress callbacks**: For large file transfers
- **Streaming output**: For long-running commands
- **Host key management**: Add/remove/list known hosts
