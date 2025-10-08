# 🚀 Dragonfly MCP Server v1.3.0 — IMAP Multi-Account & Enhanced Git

**Release Date:** October 8, 2025

---

## 🎯 Key Highlights

This release introduces **universal email access** via IMAP with multi-account support and enhances the Git tool with complete workflow capabilities.

### ⭐ What's New

#### 📧 IMAP Multi-Account Email Tool
- **Manage multiple email accounts simultaneously** from one interface
- **6 providers supported**: Gmail, Outlook, Yahoo, iCloud, **Infomaniak** (new), and Custom servers
- **13 powerful operations** for complete email workflow automation
- **5-minute setup** (vs 30+ minutes for OAuth/GCP)
- **Zero credentials in API calls** — all authentication via `.env`

#### 🔧 Enhanced Git Tool
- **New operations**: `fetch`, `pull`, `rebase`, `log`, `remote_info`
- **Conflict detection** with actionable error messages
- **Complete workflow** from clone to push without leaving the tool

---

## 📦 What's Included

### IMAP Tool Features

**Supported Providers:**
- ✅ Gmail (imap.gmail.com)
- ✅ Outlook / Office365 (outlook.office365.com)
- ✅ Yahoo Mail (imap.mail.yahoo.com)
- ✅ iCloud Mail (imap.mail.me.com)
- ✅ Infomaniak (mail.infomaniak.com) — **NEW**
- ✅ Custom IMAP servers

**Operations Available:**
1. `connect` — Test connection & get account info
2. `list_folders` — List all IMAP folders
3. `search_messages` — Advanced search (date, sender, subject, flags)
4. `get_message` — Retrieve full message with body & attachments
5. `download_attachments` — Save attachments to disk
6. `mark_read` / `mark_unread` — Single message
7. `mark_read_batch` / `mark_unread_batch` — Bulk operations
8. `move_message` / `move_messages_batch` — Move to another folder
9. `mark_spam` — Move to spam/junk
10. `delete_message` / `delete_messages_batch` — Delete with expunge

**Security:**
- 🔒 SSL by default (port 993)
- 🔒 Credentials only in `.env`, never in API parameters
- 🔒 Project-chroot for attachments
- 🔒 Passwords masked in logs

---

## 🚀 Quick Start

### IMAP Setup (5 minutes)

**1. Configure `.env`:**
```bash
# Gmail
IMAP_GMAIL_EMAIL=your.email@gmail.com
IMAP_GMAIL_PASSWORD=your_app_password

# Infomaniak
IMAP_INFOMANIAK_EMAIL=contact@yourdomain.com
IMAP_INFOMANIAK_PASSWORD=your_password
```

**2. Restart server:**
```bash
./scripts/dev.sh  # or scripts\dev.ps1 on Windows
```

**3. Test connection:**
```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "tool":"imap",
    "params":{
      "provider":"gmail",
      "operation":"connect"
    }
  }'
```

**4. Search unread emails:**
```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "tool":"imap",
    "params":{
      "provider":"gmail",
      "operation":"search_messages",
      "folder":"inbox",
      "query":{"unseen":true},
      "max_results":20
    }
  }'
```

---

## 📚 Documentation

- **Main README**: [/README.md](./README.md) — Complete overview
- **IMAP Guide**: [/src/tools/_imap/README.md](./src/tools/_imap/README.md) — Detailed setup & usage
- **API Reference**: [/src/README.md](./src/README.md) — Endpoints & configuration
- **Tools Catalog**: [/src/tools/README.md](./src/tools/README.md) — All 15 tools documented

---

## 🔄 Migration Guide

### For IMAP Users

**Old approach** (if you were using custom scripts):
```python
# Manual IMAP connection per account
import imaplib
mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('user@gmail.com', 'password')
# ... manual folder/message handling
```

**New approach** (v1.3.0):
```bash
# Configure once in .env
IMAP_GMAIL_EMAIL=user@gmail.com
IMAP_GMAIL_PASSWORD=app_password

# Use the tool
{
  "tool": "imap",
  "params": {
    "provider": "gmail",
    "operation": "search_messages",
    "folder": "inbox",
    "query": {"unseen": true}
  }
}
```

**Benefits:**
- ✅ Multi-account ready (Gmail + Infomaniak + Outlook simultaneously)
- ✅ Automatic SSL/TLS configuration
- ✅ Folder name normalization
- ✅ MIME parsing handled
- ✅ No credential leaks in code

### For Git Users

**New operations available:**
```json
// Fetch from remote
{"operation": "fetch", "remote": "origin", "prune": true}

// Pull with rebase
{"operation": "pull", "remote": "origin", "branch": "main", "rebase": true}

// View commit history
{"operation": "log", "max_count": 10, "one_line": true}
```

---

## ⚠️ Breaking Changes

**None!** This is a backward-compatible release.

Existing tools and APIs remain unchanged.

---

## 🐛 Bug Fixes

- Git tool now properly handles pull/rebase conflicts with actionable hints
- IMAP folder normalization works correctly across all providers (Gmail's `[Gmail]/` syntax, etc.)

---

## 🎯 What's Next (v1.4.0)

- 📤 **SMTP tool** for email sending
- 🔐 **OAuth2 support** for Gmail/Outlook (alternative to App Passwords)
- 🤖 **Email automation rules** engine
- 📊 **Email analytics** dashboard

---

## 📝 Full Changelog

See [CHANGELOG.md](./CHANGELOG.md) for detailed changes.

---

## 🙏 Contributors

- **Franck Dubray** — Lead Developer
- **Community** — Testing & feedback

---

## 📄 License

MIT License — see [LICENSE](./LICENSE)

---

## 🔗 Links

- **GitHub**: https://github.com/FranckDubray/dragonfly-mcp-server
- **Issues**: https://github.com/FranckDubray/dragonfly-mcp-server/issues
- **Discussions**: https://github.com/FranckDubray/dragonfly-mcp-server/discussions

---

**Happy emailing! 📧**
