# Transforms (Pur) — Règles & Catalogue

Ce dossier contient des transforms PURES (JSON in → JSON out), sans aucun appel système (réseau, disque, DB). Toute I/O est effectuée via des tools MCP (http_tool, sqlite_db, etc.). Seule exception I/O: `sleep` est un handler IO séparé (pas un transform).

Principes
- 1 fichier = 1 transform
- Aucune dépendance réseau/FS/DB (pas de `requests`, `sqlite3`, `subprocess`, etc.)
- Déterministes, rapides (<100ms typique), sans side effects
- Enregistrés automatiquement au démarrage via scan des packages `transforms/` et `transforms_domain/`

Arborescence
```
src/tools/_orchestrator/handlers/
├── transforms/                 # génériques
│   ├── increment.py
│   ├── decrement.py
│   ├── add.py
│   ├── multiply.py
│   └── set_value.py
└── transforms_domain/          # domaine/texte/LLM
    ├── sanitize_text.py
    ├── normalize_llm_output.py
    ├── extract_field.py
    ├── format_template.py
    ├── json_stringify.py
    ├── idempotency_guard.py
    ├── dedupe_by_url.py
    └── filter_by_date.py
```

Catalogue (résumé)
- increment: {value, step} → {result}
- decrement: {value, step} → {result}
- add: {a, b} → {result}
- multiply: {a, b} → {result}
- set_value: {value} → {result}
- sanitize_text: {text, max_length?} → {text, truncated, ...}
- normalize_llm_output: {content, expected_format} → {parsed, success}
- extract_field: {data, path|paths} → {value|...}
- format_template: {template, ...vars} → {text}
- json_stringify: {value} → {json_string, length}
- idempotency_guard: {action_id, completed_actions?} → {skip}
- dedupe_by_url: {new_items, prev_items?, key='url'} → {merged, removed_count}
- filter_by_date: {items, date_path, cutoff_iso, unix_seconds?} → {items_recent, kept, dropped}

Bonnes pratiques
- Préférez filtrer côté API (params MCP: from/to, time_filter…) pour limiter le volume d’entrée; utilisez `filter_by_date` en filet de sécurité moteur.
- Garder les transforms unitaires et testables; ajouter des tests fixtures JSON in/out.
- Toute logique d’accès services/DB va dans les tools (handlers IO) — pas ici.

Ajout d’un nouveau transform
1. Créer `transforms/.../your_transform.py` avec une classe `XxxHandler(AbstractHandler)` et une propriété `kind` unique.
2. Implémenter `run(**kwargs) → dict` (valider les entrées, pas d’I/O).
3. Au démarrage, le registre le chargera automatiquement (scan + register).
