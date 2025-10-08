# Tool Vélib' - Résumé pour mise à jour des README

## 📊 Informations clés

**Nom du tool :** `velib`  
**Nombre total de tools :** 17 (était 16 avant)  
**Catégorie :** 🚲 Transport & Mobilité (nouvelle catégorie)

---

## 📝 Description courte (pour README principal)

**velib** — Gestionnaire de cache Vélib' Métropole (Paris). Rafraîchit les données statiques des stations (SQLite), récupère la disponibilité temps réel (vélos mécaniques/électriques, places libres). Recherches via `sqlite_db` (db_name: 'velib').

---

## 🎯 Architecture

- **Bootstrap** : `src/tools/velib.py`
- **Package** : `src/tools/_velib/` (api, core, db, fetcher, validators, utils)
- **Spec canonique** : `src/tool_specs/velib.json`
- **Base SQLite** : `sqlite3/velib.db` (chroot projet)

---

## 📊 Schéma de la base

```sql
CREATE TABLE stations (
    station_code TEXT PRIMARY KEY,      -- Ex: "16107"
    station_id INTEGER,                 -- Ex: 213688169
    name TEXT NOT NULL,                 -- Ex: "Benjamin Godard - Victor Hugo"
    lat REAL NOT NULL,                  -- Ex: 48.865983
    lon REAL NOT NULL,                  -- Ex: 2.275725
    capacity INTEGER,                   -- Ex: 35
    station_opening_hours TEXT          -- Ex: null (souvent)
);
```

**Indexes :**
- `idx_stations_coords` sur (lat, lon)
- `idx_stations_name` sur (name)

---

## 🔧 Opérations

### 1. `refresh_stations`
Télécharge les données statiques depuis l'API Open Data et écrase la table.
```json
{"operation": "refresh_stations"}
```

### 2. `get_availability`
Récupère la disponibilité temps réel d'une station (vélos mécaniques/électriques, places libres).
```json
{"operation": "get_availability", "station_code": "16107"}
```

### 3. `check_cache`
Vérifie l'état du cache (dernière MAJ, nombre de stations).
```json
{"operation": "check_cache"}
```

---

## 💡 Workflow typique

```javascript
// 1. Initialiser le cache
velib({operation: "refresh_stations"})
// → 1494 stations importées

// 2. Rechercher stations (via sqlite_db)
sqlite_db({
  db_name: "velib",
  query: "SELECT station_code, name, capacity FROM stations WHERE name LIKE '%Bastille%' ORDER BY capacity DESC LIMIT 3"
})
// → Liste des stations Bastille

// 3. Obtenir disponibilité temps réel
velib({operation: "get_availability", station_code: "12001"})
// → 52 vélos mécaniques, 0 électrique, 7 places libres
```

---

## 🌐 API Open Data utilisée

**URLs (sans authentification) :**
- Station information : `https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json`
- Station status : `https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json`

**Configuration possible (.env) :**
```bash
VELIB_STATION_INFO_URL=https://...
VELIB_STATION_STATUS_URL=https://...
```

---

## 🔐 Sécurité

✅ SQLite chroot : `sqlite3/velib.db`  
✅ Validation station_code (alphanum, max 20 chars)  
✅ Parameterized queries (anti-injection)  
✅ Timeout HTTP : 30s  
✅ Pas de secrets requis (API publique)  

---

## 📈 Statistiques

- **~1494 stations** dans la métropole parisienne
- **Base légère** : ~200-300 KB
- **Refresh recommandé** : tous les 7 jours (stations statiques changent rarement)
- **Temps réel** : jamais caché, toujours fetch API

---

## 🎨 Section README à ajouter

### Pour `/README.md` (section Outils)

Ajouter dans la catégorie appropriée :

```markdown
### 🚲 Transport & Mobilité

#### **velib**
- Gestionnaire de cache Vélib' Métropole (Paris)
- **3 opérations** : refresh_stations, get_availability, check_cache
- Cache SQLite des stations (~1494)
- Données temps réel : vélos mécaniques/électriques, places libres
- Recherches via `sqlite_db` (db_name: 'velib')
- Architecture : `_velib/` (api, core, db, fetcher, validators, utils)
```

---

### Pour `/src/tools/README.md`

Ajouter :

```markdown
#### **velib**
- Cache manager pour Vélib' Métropole (Paris)
- Opérations : refresh_stations, get_availability, check_cache
- API Open Data (pas d'auth requise)
- Base SQLite : station_code, station_id, name, lat, lon, capacity
- Recherches via sqlite_db tool
- Architecture : `_velib/` (api, core, db, fetcher, validators, utils)
```

---

## ✅ Checklist

- [x] Tool créé et fonctionnel
- [x] Spec JSON validée (parameters = object, pas de champs inexistants)
- [x] Schéma DB propre (uniquement les vrais champs de l'API)
- [x] Tests manuels réussis (refresh, availability, recherches)
- [x] Sécurité validée (chroot, validation, pas de secrets)
- [ ] README racine mis à jour
- [ ] README src/tools mis à jour
- [ ] README src mis à jour (si pertinent)
- [ ] CHANGELOG.md mis à jour

---

**Tool production-ready ! 🚲🐉**
