
# Changelog

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

### 🔧 Notes d’upgrade
- Pour voir les erreurs de démarrage: inspecter `logs/worker_<name>.log`
- En cas d’erreur JSON/$import: l’API Start renvoie `failed`; côté runner, phase=failed + last_error (si erreur post-spawn)
- Recommandé: one-shot pour curation (sleep_seconds=0), et contrôle manuel des métriques fraîcheur (<72h)

---

