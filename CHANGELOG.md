# Changelog

## [1.40.0] - 2025-01-19

### 🎯 Orchestrator v1.4 — Audit complet + Fixes P0/P1 (couverture 56% → 90%)

#### 🔴 P0 Critiques (TERMINÉS)
- ✅ **v1.3.1** : Fix api.py `_validate_process_logic(process_data)` variable name
- ✅ **v1.3.2** : Crash logging avec contextes complets (table crash_logs)
- ✅ **v1.4.0** : Scopes lifecycle complet (reset END, enter/leave triggers)
- ✅ **v1.4.1** : Traceback Python enrichi (frame-by-frame + locals vars)

#### 🟡 P1 Features manquantes (TERMINÉS)
- ✅ **v1.4.2** : Retry logging (log_retry_attempt en DB)
- ✅ **v1.4.3** : Transforms errors normalisés (HandlerError partout)

#### 📊 Couverture specs membank
- **Avant** : 10/18 features (56%)
- **Après** : 16/18 features (89%)

#### 🚀 Nouvelles features production
1. **Crash logs complets**
   - Table crash_logs avec worker_ctx + cycle_ctx + stack_trace
   - Traceback Python frame-by-frame avec variables locales
   - print_crash_report() pour debug rapide

2. **Scopes lifecycle complet**
   - reset_on: ["END"] fonctionnel
   - reset_on: ["node_name"] fonctionnel
   - scope_trigger: {action: "enter|leave", scope: "name"} sur edges

3. **Retry logging**
   - log_retry_attempt() log chaque tentative
   - Query: `SELECT * FROM job_steps WHERE node LIKE '%_retry_%'`

4. **Transforms robustes**
   - Tous les transforms lèvent HandlerError
   - Retry policy s'applique correctement

---

## [1.31.0] - 2025-10-19

### 🛡️ Orchestrator v1.3 — Validation Schema + Error Messages

- ✅ **P1: JSON Schema Validation**
  - Création `schemas/process.schema.json` (complet, 6 decision kinds, retry limits)
  - api.py : validation automatique au start avec jsonschema (optional dependency)
  - Détection erreurs : worker_ctx type, handler manquant, edges invalides, duplicate nodes/edges
  - Messages clairs : path + schema_path pour localiser erreurs
  - Custom validation : START unique, edges vers nodes existants, no duplicate signatures

- 📝 **P2: Process Loader Error Messages**
  - Messages enrichis : chemins candidats affichés (base_dir + nodes/)
  - Erreurs JSON : ligne + colonne + conseil syntaxe
  - Circular imports : affiche chaîne complète
  - File not found : liste tous les chemins testés + tips organisation

---

## [1.30.0] - 2025-10-19

### 🔧 Orchestrator v1.2 — Audit & Cleanup

- 🔴 **FIX CRITIQUE**: api.py utilise maintenant `load_process_with_imports` (support $import au démarrage)
- 🗑️ **Cleanup**: Suppression handlers/transforms.py (dupliqué, handlers splittés dans transforms/*.py)
- 🧹 **Refactor**: handlers/__init__.py charge dynamiquement depuis transforms/ et transforms_domain/
- ✅ **Validation**: Process loader avec $import fonctionnel en API start + runner hot-reload

---

## [1.29.0] - 2025-10-19

### 🚀 Orchestrator v1.2 — Robustesse & Curation AI (72h) 

- 🧰 Runner (prod): redirection stdout/stderr → `logs/worker_<name>.log` (aucune synchro Git)
- 🧱 Résilience: process loader avec $import sous `nodes/` (anti-cycles, erreurs courtes)
- 🧩 Transforms (pur, 1 fichier = 1 transform): refactor + nouveaux
- 🧭 Process `ai_curation` (v6.0.5):
  - Dates centralisées
  - Filtre fraîcheur multi-source (<72h)
  - Fusion/dédoublonnage du rapport
- 🧹 .gitignore élargi (logs/, docs/, sqlite3/, *.db)
