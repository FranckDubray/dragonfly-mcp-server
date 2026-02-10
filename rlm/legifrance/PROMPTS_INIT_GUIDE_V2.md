# Guide Initialisation Base Prompts

## Etat actuel (2026-02-07)

Les 3 prompts sont inseres et actifs dans `prompts.db` :
- `legal/planner/v1` — enrichi avec code_id et connaissance tool
- `legal/researcher/v1` — protocole anti-overload
- `legal/evaluator/v1` — audit sur pieces via mutation thread (méthode 3 étapes)

NOTE : La colonne `version` reste 'v1' pour compatibilite avec system_prompt_ref.

## Commandes SQLite

### Verifier les prompts actifs

```sql
SELECT id, domain, agent_type, version, length(prompt) as size,
       substr(prompt, 1, 80) as preview
FROM prompts
WHERE is_active = 1;
```

### Queries pour le Master

#### Recuperer le prompt Planner

```sql
SELECT prompt 
FROM prompts 
WHERE domain = 'legal' 
  AND agent_type = 'planner' 
  AND is_active = 1 
  AND version = 'v1' 
LIMIT 1;
```

#### Recuperer le prompt Researcher

```sql
SELECT prompt 
FROM prompts 
WHERE domain = 'legal' 
  AND agent_type = 'researcher' 
  AND is_active = 1 
  AND version = 'v1' 
LIMIT 1;
```

#### Recuperer le prompt Evaluator

```sql
SELECT prompt 
FROM prompts 
WHERE domain = 'legal' 
  AND agent_type = 'evaluator' 
  AND is_active = 1 
  AND version = 'v1' 
LIMIT 1;
```

## Integration Master

Le Master appelle chat_agent avec system_prompt_ref :

```
Phase 1 : chat_agent(system_prompt_ref="legal/planner/v1", tools=[])
Phase 2 : chat_agent(system_prompt_ref="legal/researcher/v1", tools=["legifrance_consult"])
Phase 3 : chat_agent(system_prompt_ref="legal/evaluator/v1", tools=[], thread_id=researcher_thread)
```

## Notes techniques

- Les prompts echappent les apostrophes ('' au lieu de ' dans SQLite)
- La colonne prompt est TEXT illimite
- Le cache SQLite accelere les lectures repetees
- Table prompt_usage_logs disponible pour analytics (non utilisee)