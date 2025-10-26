

## 1.6.4 — 2025-10-26

Improvements (Py Orchestrator + Workers LLM)
- Config directory-only (workers/<name>/config/) généralisée
  - Runner: merge config/config.json (deep) + config/prompts/*.md (injectés dans metadata.prompts) + CONFIG_DOC.json; hot‑reload.
  - Suppression complète des fichiers de config à la racine des workers.
- API config (py_orchestrator.operation=config)
  - key_path générique (dot + [index] + ["clé.avec.points"]) pour éditer n’importe quel élément JSON à n niveaux.
  - storage:"file": prompts.<name> → config/prompts/<name>.md (auto), sinon deep‑set dans config/config.json; storage:"inline": KV only.
  - set.file: écriture directe de fichiers sous config/ (chroot).
  - remove:true: suppression ciblée (chemin imbriqué) dans metadata et config.json.
- ai_curation_v2
  - Migration complète vers config/ directory‑only; prompts externalisés (fichiers .md).
  - Recâblage steps → worker["prompts"].
  - Purge des vestiges (primary_sites) et pilotage depuis primary_site_caps.
- Refactor tool
  - api_router.py + api_config.py (<7KB) + api.py (alias mince); pas de code mort.

Docs
- README: guide “Workers LLM — meilleures pratiques (config/ dir + prompts fichiers + API config)”, exemples d’édition (key_path, storage, set.file), checklist.

Notes
- Rétro‑compatibilité: les workers existants doivent migrer leur config vers config/ (prompt fichiers + config.json). L’API supporte désormais l’édition fine et la persistance fichier.
