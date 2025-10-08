# Vélib' Métropole Tool

Tool de gestion du cache des stations Vélib' Métropole (Paris) avec accès temps réel.

## 🎯 Objectif

Gérer un cache SQLite des données **statiques** des stations Vélib' et fournir un accès **temps réel** à la disponibilité des vélos. Les recherches complexes se font via le tool `sqlite_db`.

---

## 📊 Architecture

### Fichiers
```
velib.py                    # Bootstrap (run + spec)
_velib/                     # Package implémentation
  __init__.py               # spec()
  api.py                    # Routing
  core.py                   # Business logic
  db.py                     # SQLite operations (chroot)
  fetcher.py                # HTTP Open Data fetcher
  validators.py             # Input validation
  utils.py                  # Pure helpers
  README.md                 # This file
```

### Base de données
**Emplacement :** `sqlite3/velib.db` (chroot projet)

**Tables :**
- `stations` : données statiques (lat, lon, name, capacity, etc.)
- `metadata` : cache metadata (last_refresh, station_count)

---

## 🔧 Opérations

### 1. `refresh_stations`
Télécharge les données statiques depuis l'API Open Data et **écrase** la table `stations`.

**Exemple :**
```json
{
  "tool": "velib",
  "params": {
    "operation": "refresh_stations"
  }
}
```

**Retour :**
```json
{
  "success": true,
  "operation": "refresh_stations",
  "stations_imported": 1450,
  "last_update": "2025-10-08T19:30:00Z",
  "message": "1450 stations imported successfully"
}
```

---

### 2. `get_availability`
Récupère la disponibilité **temps réel** d'une station (vélos mécaniques, électriques, places libres).

**Exemple :**
```json
{
  "tool": "velib",
  "params": {
    "operation": "get_availability",
    "station_code": "16107"
  }
}
```

**Retour :**
```json
{
  "success": true,
  "operation": "get_availability",
  "station_code": "16107",
  "bikes": {
    "total": 7,
    "mechanical": 4,
    "ebike": 3
  },
  "docks_available": 5,
  "status": {
    "is_installed": true,
    "is_renting": true,
    "is_returning": true
  },
  "last_reported": 1696745280,
  "last_update_time": "2025-10-08T16:00:00Z"
}
```

---

### 3. `check_cache`
Vérifie l'état du cache (dernière mise à jour, nombre de stations).

**Exemple :**
```json
{
  "tool": "velib",
  "params": {
    "operation": "check_cache"
  }
}
```

**Retour :**
```json
{
  "success": true,
  "operation": "check_cache",
  "cache": {
    "last_refresh": "2025-10-08T19:30:00Z",
    "station_count": 1450,
    "db_path": "/path/to/project/sqlite3/velib.db"
  }
}
```

---

## 🔍 Recherches complexes (via sqlite_db)

Les recherches se font directement avec le tool `sqlite_db` :

### Exemple 1 : Stations par arrondissement
```json
{
  "tool": "sqlite_db",
  "params": {
    "db_name": "velib",
    "query": "SELECT station_code, name, address, lat, lon, capacity FROM stations WHERE post_code = '75003' LIMIT 20"
  }
}
```

### Exemple 2 : Stations à grande capacité
```json
{
  "tool": "sqlite_db",
  "params": {
    "db_name": "velib",
    "query": "SELECT station_code, name, capacity FROM stations WHERE capacity > 40 ORDER BY capacity DESC LIMIT 10"
  }
}
```

### Exemple 3 : Toutes les stations (export)
```json
{
  "tool": "sqlite_db",
  "params": {
    "db_name": "velib",
    "query": "SELECT * FROM stations ORDER BY name"
  }
}
```

---

## 🌐 API Open Data

**URLs utilisées** (pas d'authentification requise) :
```
https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json
https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json
```

**Configuration possible** (`.env`) :
```bash
VELIB_STATION_INFO_URL=https://...
VELIB_STATION_STATUS_URL=https://...
```

---

## 🔐 Sécurité

✅ **SQLite chroot** : `sqlite3/velib.db`  
✅ **Validation** : station_code (alphanum, max 20 chars)  
✅ **Pas de secrets** : API publique  
✅ **Timeout HTTP** : 30s  
✅ **Parameterized queries** : protection injection SQL  

---

## 📊 Schéma de la base

```sql
CREATE TABLE stations (
    station_code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    capacity INTEGER,
    station_type TEXT,
    rental_methods TEXT,
    post_code TEXT,
    region TEXT,
    is_virtual_station INTEGER DEFAULT 0
);

CREATE INDEX idx_stations_coords ON stations(lat, lon);
CREATE INDEX idx_stations_postcode ON stations(post_code);
```

---

## 💡 Workflow typique

```bash
# 1. Initialiser le cache
velib({operation: "refresh_stations"})
# → 1450 stations imported

# 2. Vérifier le cache
velib({operation: "check_cache"})
# → last_refresh: 2025-10-08T19:30:00Z

# 3. Chercher stations (via sqlite_db)
sqlite_db({
  db_name: "velib",
  query: "SELECT * FROM stations WHERE post_code = '75011' LIMIT 5"
})

# 4. Obtenir dispo temps réel
velib({operation: "get_availability", station_code: "16107"})
# → mechanical: 4, ebike: 3, docks: 5
```

---

## 🐛 Gestion d'erreurs

Toutes les opérations retournent un objet avec `success` :
```json
{
  "success": false,
  "error": "Station code '99999' not found in real-time data"
}
```

**Erreurs courantes :**
- `station_code` manquant → `"station_code is required"`
- Station introuvable → `"Station code 'XXX' not found"`
- API indisponible → `"Failed to fetch station status: ..."`
- Cache vide → `"Cache is empty. Run 'refresh_stations'"`

---

## 📝 Notes

- Les données **statiques** changent rarement (nouvelles stations = quelques fois par an)
- Les données **temps réel** changent **constamment** (jamais cachées)
- Le schéma SQLite est conçu pour des recherches géographiques efficaces (index lat/lon)
- ~1450 stations = base légère (~200-300 KB)
