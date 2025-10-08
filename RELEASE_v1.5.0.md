# 🚀 Dragonfly MCP Server v1.5.0 — Vélib' Métropole Tool

**Release Date:** October 8, 2025

---

## 🎯 Key Highlights

This release introduces the **Vélib' Métropole tool** for Paris bike-sharing data with SQLite cache management and real-time availability API integration.

### ⭐ What's New

#### 🚲 Vélib' Métropole Tool
- **Manage Vélib' station data** for the Paris metropolitan area (~1494 stations)
- **SQLite cache** for fast local queries on static data
- **Real-time availability** for bikes (mechanical/electric) and free docks
- **Seamless integration** with existing `sqlite_db` tool for complex searches
- **Zero authentication** required (Open Data API)

---

## 📦 What's Included

### Vélib' Tool Features

**3 Operations:**
1. `refresh_stations` — Download and cache static station data
2. `get_availability` — Get real-time availability for one station
3. `check_cache` — Check cache metadata (last update, station count)

**Database Schema:**
```sql
CREATE TABLE stations (
    station_code TEXT PRIMARY KEY,      -- "16107"
    station_id INTEGER,                 -- 213688169 (system ID)
    name TEXT NOT NULL,                 -- "Benjamin Godard - Victor Hugo"
    lat REAL NOT NULL,                  -- 48.865983
    lon REAL NOT NULL,                  -- 2.275725
    capacity INTEGER,                   -- 35
    station_opening_hours TEXT          -- null (mostly)
);
```

**Security:**
- 🔒 SQLite chroot to `sqlite3/velib.db`
- 🔒 Input validation (station_code: alphanumeric, max 20 chars)
- 🔒 Parameterized queries (SQL injection protection)
- 🔒 HTTP timeout: 30s
- 🔒 No secrets required (public API)

---

## 🚀 Quick Start

### 1. Initialize Cache
```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "velib",
    "params": {
      "operation": "refresh_stations"
    }
  }'
```

### 2. Search Stations (via sqlite_db)
```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "sqlite_db",
    "params": {
      "db_name": "velib",
      "query": "SELECT station_code, name, capacity FROM stations WHERE name LIKE '\''%Bastille%'\'' ORDER BY capacity DESC LIMIT 3"
    }
  }'
```

### 3. Get Real-Time Availability
```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "velib",
    "params": {
      "operation": "get_availability",
      "station_code": "12001"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "station_code": "12001",
  "bikes": {
    "total": 52,
    "mechanical": 52,
    "ebike": 0
  },
  "docks_available": 7,
  "status": {
    "is_installed": true,
    "is_renting": true,
    "is_returning": true
  }
}
```

---

## 📚 Documentation

- **Main README**: [/README.md](./README.md) — Complete overview (17 tools)
- **Vélib' Details**: [/src/tools/_velib/README.md](./src/tools/_velib/README.md) — Setup & usage
- **API Reference**: [/src/README.md](./src/README.md) — Endpoints & configuration
- **Tool Specs**: [/src/tool_specs/velib.json](./src/tool_specs/velib.json) — Canonical spec

---

## 🔄 Migration Guide

### For New Users

**No setup required!** The tool uses Open Data API (no authentication).

**Quick workflow:**
```javascript
// 1. Initialize cache
velib({operation: "refresh_stations"})

// 2. Search stations (sqlite_db)
sqlite_db({
  db_name: "velib",
  query: "SELECT * FROM stations WHERE name LIKE '%République%'"
})

// 3. Get real-time availability
velib({operation: "get_availability", station_code: "11018"})
```

### For Existing Users

**No breaking changes!** This is a new feature that:
- ✅ Adds a 17th tool to the server
- ✅ Uses existing `sqlite_db` infrastructure
- ✅ Follows the same security patterns
- ✅ Works immediately without configuration

---

## ⚠️ Breaking Changes

**None!** This is a backward-compatible release.

---

## 🐛 Bug Fixes

- No bug fixes in this release (new feature only)

---

## 🎯 What's Next (v1.6.0)

- 🌍 **Geolocation search** for Vélib' (find nearest stations by lat/lon)
- 📊 **Advanced analytics** (usage patterns, historical data)
- 🚴 **Multi-city support** (extend to other bike-sharing systems)
- 🔔 **Availability alerts** (notify when bikes/docks available)

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

**Happy biking! 🚲**
