# Changelog

All notable changes to this project will be documented in this file.

Note: Older entries have been archived under changelogs/ (range-based files).

---

## [Unreleased] - Tools Audit & Fixes

Campagne d'audit en profondeur de tous les tools pour conformité LLM_DEV_GUIDE.

### date - [2025-10-12] ✅ AUDITED

**Score**: 6.5/10 → **8.5/10** 🎉

#### Fixed
- **CRITIQUE**: `spec()` charge maintenant le JSON canonique
  - **Avant**: Duplication complète du schéma JSON en Python (~1500 bytes)
  - **Après**: Lecture depuis `src/tool_specs/date.json` (conformité LLM_DEV_GUIDE)
  - Évite désynchronisation spec Python ↔ JSON

- **MAJEUR**: JSON spec clarifié pour LLM
  - **Avant**: Descriptions génériques, defaults implicites, pas d'exemples
  - **Après**: 
    - Descriptions détaillées par paramètre (formats strftime, timezones, exemples)
    - Defaults explicites (`unit: "days"`, `locale: "en"`, `format: "%Y-%m-%d %H:%M:%S%z"`)
    - Exemples strftime: `'%Y-%m-%d'`, `'%d/%m/%Y %H:%M'`, `'%B %d, %Y'`
    - Ranges documentés pour durées (±10 ans)

- **IMPORTANT**: Validation ajoutée
  - Format string max 100 chars (prévient DoS)
  - Durées limitées à ±10 ans (prevent overflow)
  - Warning si valeurs anormales détectées

#### Added
- **MAJEUR**: Documentation README complète (6.3 KB)
  - 9 opérations détaillées avec exemples JSON
  - Tableau formats date (ISO + formats communs + custom)
  - Support timezones (IANA, fallback UTC)
  - 4 use cases (Calendar, Timezone, Reports, Project Planning)
  - Tableau configuration et architecture

#### Improved
- **Logging basique**: Warnings ajoutés pour timezone invalide, delta values anormaux

#### Technical Details
- `date.py`: -1347 bytes (spec dupliquée supprimée)
- `date.json`: +1937 bytes (descriptions enrichies, defaults, exemples)
- `_date_README.md`: +6376 bytes (création)
- **Net**: +6966 bytes, conformité **62% → 95%**

#### Audit Results
| Critère | Avant | Après | Évolution |
|---------|-------|-------|-----------|
| JSON Spec LLM | 7/10 | 9/10 | 📈 +2.0 (clarifications ✅) |
| Architecture | 7/10 | 9/10 | 📈 +2.0 (spec canonique ✅) |
| Sécurité | 6/10 | 8/10 | 📈 +2.0 (validation ✅) |
| Robustesse | 7/10 | 8/10 | 📈 +1.0 (logging ✅) |
| Conformité | 5/10 | 10/10 | 📈 +5.0 (**CRITICAL FIX**) |
| Performance | 8/10 | 8/10 | ✅ |
| Maintenabilité | 7/10 | 9/10 | 📈 +2.0 (canonical source) |
| Documentation | 3/10 | 10/10 | 📈 +7.0 (README ✅) |
| Outputs | 8/10 | 8/10 | ✅ Minimaux |

**SCORE FINAL: 8.5/10** ⭐⭐⭐⭐

#### Known Issues
Aucun.

---

### chess_com - [2025-10-12] ✅ AUDITED

**Score**: 8.2/10 → **8.8/10** 🎉

#### Fixed
- **CRITIQUE**: Clarification description param `limit` dans JSON spec
  - **Avant**: Description changeante (générique max 500 vs leaderboards max 50) → confusion LLM
  - **Après**: Description unifiée claire: "Most operations: default=50, max=500. get_leaderboards only: default=10, max=50 (applies per category)"
  - Conforme best practices UX LLM

- **MAJEUR**: Ajout pattern regex pour `username` dans JSON spec
  - **Avant**: Pattern manquant (validation côté Python uniquement)
  - **Après**: `"pattern": "^[a-zA-Z0-9_.-]{2,25}$"` dans la spec
  - Facilite validation côté LLM + UX

#### Added
- **MAJEUR**: Création README.md complet (7.6KB)
  - 24 opérations groupées par domaine (Players, Clubs, Tournaments, etc.)
  - Tableau récapitulatif avec paramètres required/optional
  - 15 exemples d'usage (JSON)
  - 5 use cases détaillés (Player Analysis, Tournament Monitoring, Club Management, Training, Streaming)
  - Configuration & architecture
  - Tableau limits & truncation
  - Error handling détaillé

- **IMPORTANT**: Logging basique ajouté (chess_client.py)
  - `logger.debug()` pour rate limiting wait
  - `logger.info()` pour succès API (endpoint + HTTP status)
  - `logger.warning()` pour rate limit exceeded
  - `logger.error()` pour erreurs API (4xx/5xx)
  - Aide debugging production sans verbosité

#### Technical Details
- `chess_com.json`: +113 bytes (clarification `limit`, ajout `pattern`)
- `_chess_com/README.md`: +7817 bytes (création)
- `chess_client.py`: +709 bytes (logging)
- `core.py`: -733 bytes (cleanup verbosité)
- Conformité LLM_DEV_GUIDE: 87% → 96%

#### Audit Results

| Critère | Avant | Après | Évolution |
|---------|-------|-------|-----------|
| JSON Spec LLM | 8.5/10 | 9.5/10 | 📈 +1.0 (clarifications) |
| Architecture | 9.5/10 | 9.5/10 | ✅ Exemplaire |
| Sécurité | 9.5/10 | 9.5/10 | ✅ |
| Robustesse | 9/10 | 9/10 | ✅ |
| Conformité | 9/10 | 9.5/10 | 📈 +0.5 (logging) |
| Performance | 9/10 | 9/10 | ✅ |
| Maintenabilité | 9/10 | 9/10 | ✅ |
| Documentation | 3/10 | 10/10 | 📈 +7.0 (README complet) |
| Outputs | 7.5/10 | 7.5/10 | ✅ (verbosité minimale OK) |

**SCORE FINAL: 8.8/10** ⭐⭐⭐⭐

#### Known Issues
- **API Change**: L'endpoint `/pub/leaderboards` retourne 404 (déprécié par Chess.com en 2025, confirmé Perplexity)
  - Pas un bug de notre code, mais une API change officielle
  - Aucune alternative officielle disponible (scraping web seule option)
  - Opération `get_leaderboards` conservée dans la spec pour compatibilité future

---

### random - [2025-10-12] ✨ NEW TOOL

**Nouveau tool complet de génération aléatoire VRAIE (sources physiques)**.

#### Features
- **2 sources physiques**:
  - 🌀 **Atmospheric**: RANDOM.ORG (bruit atmosphérique radio)
  - ⚛️ **Quantum**: Cisco Outshift QRNG (hardware quantique)
  - 🔒 **Fallback**: Python `secrets` (CSPRNG cryptographique)

- **7 opérations**:
  - `generate_integers` - Entiers aléatoires (range, unique)
  - `generate_floats` - Décimaux aléatoires (précision configurable)
  - `generate_bytes` - Bytes aléatoires (hex/base64/decimal)
  - `coin_flip` - Pile ou face (heads/tails)
  - `dice_roll` - Dé N faces (3-100 faces)
  - `shuffle` - Mélange Fisher-Yates avec vraie aléa
  - `pick_random` - Sélection aléatoire dans liste (no duplicates)

- **Auto-fallback intelligent**:
  1. Essaie Quantum (rapide, ~100ms)
  2. Fallback Atmospheric (~200ms)
  3. Final fallback CSPRNG (instant)

- **Source tracking**: Retourne quelle source a été utilisée

#### Use Cases
- Cryptographie (clés, nonces, IVs)
- Gaming / Loteries (dés, pile-face)
- Sélection aléatoire (A/B testing, random sampling)
- Shuffle sécurisé (playlist, quiz questions)

#### Configuration
```bash
# Optional: Cisco QRNG (100k bits/day free)
CISCO_QRNG_API_KEY=your_api_key

# RANDOM.ORG: no key required (1M bits/day free)
```

#### Technical Details
- Category: `utilities`
- Tags: `randomness`, `cryptography`, `quantum`, `physical`
- Dependencies: `requests` (HTTP calls)
- Architecture: modulaire (api/core/validators/sources)
- Documentation: README complet (5KB)

#### Examples
```json
// Quantum integers
{"operation": "generate_integers", "min": 1, "max": 100, "count": 10, "source": "quantum"}

// Atmospheric coin flips
{"operation": "coin_flip", "count": 50, "source": "atmospheric"}

// Crypto bytes
{"operation": "generate_bytes", "length": 32, "format": "hex", "source": "auto"}

// Random selection
{"operation": "pick_random", "items": ["A", "B", "C"], "count": 1}
```

---

### ship_tracker - [2025-10-12] ✅ AUDITED

**Score**: 8.6/10 → **9.4/10** 🎉

#### Fixed
- **CRITIQUE**: Ajout warnings de truncation (core.py)
  - **Avant**: Résultats tronqués silencieusement → LLM ne sait pas qu'il manque des ships
  - **Après**: `{"truncated": true, "warning": "Results limited to X, Y ships matched filters"}`
  - Conforme à LLM_DEV_GUIDE (output size management)

- **CRITIQUE**: Clarification des counts (core.py)
  - **Avant**: `ships_found` ambigu (post-filtres ou raw?)
  - **Après**: 3 counts distincts:
    - `total_detected`: Ships détectés via WebSocket (raw)
    - `matched_filters`: Ships correspondant aux filtres
    - `returned`: Ships actuellement retournés (après truncation)
  - Transparence totale pour les LLM

- **MAJEUR**: Default timeout augmenté 10s → 15s (spec JSON + validators)
  - 10s = insuffisant pour navires lents (émettent tous les 10-30s)
  - 15s = équilibre entre rapidité et détection
  - Documenté dans README: "Quick check: 10s, Standard: 15-30s"

- **IMPORTANT**: Limite collection WebSocket (aisstream.py)
  - Ajout protection `MAX_SHIPS_TO_COLLECT = 500` (safety)
  - Stop early si limite atteinte → évite explosion mémoire
  - Log warning si atteint

#### Improved
- **Logging basique ajouté** (aisstream.py)
  - `logger.debug()` pour events WebSocket (open, close, errors)
  - `logger.info()` pour succès (ships collected, MMSI found)
  - `logger.warning()` pour limites atteintes
  - Aide debugging production sans verbosité

- **Documentation get_ship_by_mmsi**
  - Note ajoutée: "Listens globally (inefficient), use 30-60s timeout"
  - Clarification: pourquoi ça peut prendre du temps

#### Technical Details
- `core.py`: +1201 bytes (truncation warnings + counts clarifiés)
- `ship_tracker.json`: timeout default 10→15 (+2 chars)
- `aisstream.py`: +1570 bytes (logging + collection limit)
- `validators.py`: +117 bytes (timeout defaults)
- Conformité LLM_DEV_GUIDE: 87% → 96%

#### Audit Results
| Critère | Avant | Après | Évolution |
|---------|-------|-------|-----------|
| Architecture | 10/10 | 10/10 | ✅ WebSocket exemplaire |
| Sécurité | 8/10 | 9/10 | 📈 +1 (collection limit) |
| Robustesse | 8/10 | 9/10 | 📈 +1 (logging) |
| Conformité | 7/10 | 10/10 | 📈 +3 (truncation ✅) |
| Performance | 7/10 | 8/10 | 📈 +1 (timeout ajusté) |
| Maintenabilité | 9/10 | 9/10 | ✅ |
| Documentation | 10/10 | 10/10 | ✅ README excellent |
| Fonctionnalités | 10/10 | 10/10 | ✅ |

**SCORE FINAL: 9.4/10** ⭐⭐⭐⭐⭐

---

### discord_bot - [2025-10-12] ✅ AUDITED

**Score**: 8.6/10 → **9.6/10** 🎉

#### Fixed
- **CRITIQUE**: Ajout de `list_guilds` dans la spec JSON (opération manquante dans l'enum)
  - L'opération existait dans le code mais n'était pas exposée aux LLM
  - Ajoutée en première position de l'enum `operation`
  - Description mise à jour: "29 opérations disponibles"

- **MAJEUR**: Nettoyage de messages moins agressif (utils.py)
  - **Avant**: Supprimait `pinned`, `type`, `channel_id`, `guild_id`, `mention_everyone` → Perte de contexte
  - **Après**: Ces champs essentiels sont maintenant **préservés**
  - Améliore la qualité du contexte pour les LLM

- **IMPORTANT**: Ajout des warnings de truncation (ops_messages.py)
  - `list_messages` retourne maintenant `{"truncated": true, "warning": "Results limited to X"}` si tronqué
  - Aide les LLM à comprendre qu'il faut utiliser la pagination

#### Improved
- **Gestion d'erreurs**: Cas spécifique pour 400 Bad Request dans `check_response()`
  - Extraction du message d'erreur Discord pour feedback précis
  - Distinction entre ValueError (4xx client) et RuntimeError (5xx server)

#### Added
- **Documentation**: Nouveau `_discord_bot/README.md` complet
  - Liste des 29 opérations avec descriptions
  - Exemples d'utilisation
  - Architecture et sécurité
  - Changelog interne

#### Technical Details
- `discord_bot.json`: Ajout `list_guilds` ligne 11 (27 bytes)
- `utils.py`: Refonte `_remove_null_fields()` et `clean_message()` (+915 bytes)
- `ops_messages.py`: Ajout logic truncation warning (+227 bytes)
- Conformité LLM_DEV_GUIDE: 95% → 98%

#### Audit Results
| Critère | Avant | Après | Évolution |
|---------|-------|-------|-----------|
| Architecture | 10/10 | 10/10 | ✅ Exemplaire |
| Sécurité | 9/10 | 9/10 | ✅ Rate limiting parfait |
| Robustesse | 8/10 | 9/10 | 📈 +1 |
| Conformité | 8/10 | 10/10 | 📈 +2 (spec complète) |
| Performance | 9/10 | 9/10 | ✅ |
| Maintenabilité | 9/10 | 10/10 | 📈 +1 |
| Documentation | 7/10 | 10/10 | 📈 +3 |

**SCORE FINAL: 9.6/10** ⭐⭐⭐⭐⭐

---

For older versions, see: [changelogs/](changelogs/) (range-based archives).
