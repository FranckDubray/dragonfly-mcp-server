# Index Memory Bank — Système Multi-Agents Juridique

## Fichiers actifs

| Fichier | Rôle |
|---------|------|
| `PROMPT_MASTER_01_ORCHESTRATEUR_V2.md` | System prompt du Master (orchestrateur) |
| `PROMPT_MASTER_02_AGENTS_V2.md` | Prompts des 3 agents (Planner, Researcher, Evaluator) |
| `PROMPT_MASTER_03_GUIDE_USAGE_V2.md` | Guide utilisation, tests, troubleshooting |
| `PROMPTS_DATABASE_SCHEMA.sql` | Schéma SQLite prompts.db |
| `PROMPTS_INIT_GUIDE_V2.md` | Guide insertion/vérification prompts |

## Pour reprendre le travail

1. Charger `PROMPT_MASTER_01_ORCHESTRATEUR_V2.md` (architecture)
2. Charger `PROMPT_MASTER_02_AGENTS_V2.md` (prompts agents)
3. Charger `PROMPT_MASTER_03_GUIDE_USAGE_V2.md` (guide + troubleshooting)

## Documentation serveur (séparée)

La documentation infra/scripts est dans `server_legifrance/memory_bank/` :
- `ARCHITECTURE.md` : Vue d'ensemble système
- `SCRIPTS_REFERENCE.md` : Documentation scripts serveur
- `MCP_TOOLS.md` : Documentation tools MCP