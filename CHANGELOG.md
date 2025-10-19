# Changelog

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

### 🔧 Notes techniques
- jsonschema optionnel (si absent, validation skippée sans crash)
- Schema strict : retry max 10, timeout max 2h, decision kinds enum
- Custom validation après schema : edges/nodes coherence, START unique
- Effort total : ~1h20 (P1: 1h, P2: 20min)

---

## [1.30.0] - 2025-10-19

### 🔧 Orchestrator v1.2 — Audit & Cleanup

- 🔴 **FIX CRITIQUE**: api.py utilise maintenant `load_process_with_imports` (support $import au démarrage)
- 🗑️ **Cleanup**: Suppression handlers/transforms.py (dupliqué, handlers splittés dans transforms/*.py)
- 🧹 **Refactor**: handlers/__init__.py charge dynamiquement depuis transforms/ et transforms_domain/
- ✅ **Validation**: Process loader avec $import fonctionnel en API start + runner hot-reload

### 🔧 Notes techniques
- Process avec `$import` supportés partout (API start + runner reload)
- Bootstrap handlers automatique depuis sous-packages transforms/
- Pas de régression: tous les transforms existants (5 math + 6 domain + 1 mock)

---

## [1.29.0] - 2025-10-19

### 🚀 Orchestrator v1.2 — Robustesse & Curation AI (72h) 

- 🧰 Runner (prod): redirection stdout/stderr → `logs/worker_<name>.log` (aucune synchro Git)
- 🧱 Résilience: process loader avec $import sous `nodes/` (anti-cycles, erreurs courtes)
- 🧩 Transforms (pur, 1 fichier = 1 transform): refactor + nouveaux
  - `filter_by_date`, `filter_multi_by_date` (72h, déterministes)
  - `dedupe_by_url` (filet hors LLM)
- 🧭 Process `ai_curation` (v6.0.5):
  - Dates centralisées (une capture au début, réutilisée partout)
  - Filtre fraîcheur multi-source (<72h) + filtres API côté MCP
  - Fusion/dédoublonnage du rapport avec le précédent (LLM JSON strict)
  - README worker mis à jour
- 🧹 .gitignore élargi (logs/, docs/, script_executor/, .dgy_backup/, sqlite3/, *.db, egg-info/, .env)

### 🔧 Notes d'upgrade
- Pour voir les erreurs de démarrage: inspecter `logs/worker_<name>.log`
- En cas d'erreur JSON/$import: l'API Start renvoie `failed`; côté runner, phase=failed + last_error (si erreur post-spawn)
- Recommandé: one-shot pour curation (sleep_seconds=0), et contrôle manuel des métriques fraîcheur (<72h)

---
