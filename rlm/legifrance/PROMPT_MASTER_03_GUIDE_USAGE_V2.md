# GUIDE UTILISATION - Systeme Orchestrateur Juridique

Version: 3.0
Date: 2026-02-07

---

## OBJECTIF

Permettre a un LLM de repondre a des questions juridiques avec une garantie ZERO HALLUCINATION en s'appuyant EXCLUSIVEMENT sur le corpus Legifrance.

## ARCHITECTURE

### Vue Conceptuelle

```
User Question
     |
Master LLM (Orchestrateur)
     |
  Planner --> Researcher --> Evaluator
     |            |              |
     |        legifrance_consult |
     |            |              |
     |        Corpus LEGI        |
     |       (PostgreSQL)        |
```

### Schema Technique

```
User --> Master (tools=["chat_agent"])
           |
           +--> Planner (tools=[], system_prompt_ref="legal/planner/v1")
           |      retourne plan JSON avec code_id + instruction_recherche
           |
           +--> Researcher (tools=["legifrance_consult"], nouveau thread)
           |      suit le protocole anti-overload : depth=2 -> ciblage -> depth=4 -> get_articles
           |      retourne reponse + preuves + thread_id
           |
           +--> Evaluator (tools=[], MEME thread que Researcher)
                  accede aux retours bruts des tools (audit sur pieces)
                  retourne verdict JSON (VALIDE/REJETE)
```

**Points cles** :
- Le Master n'a QUE chat_agent (JAMAIS legifrance_consult)
- Le Planner n'a AUCUN tool (il planifie, le Master orchestre)
- L'Evaluator reutilise le thread du Researcher (mutation de thread)
- system_prompt_ref pour economie de tokens
- output_mode=minimal pour tous les agents

## LANCEMENT DU TEST

### Configuration MCP CRITIQUE

**ATTENTION : Le Master ne doit avoir QUE chat_agent dans ses tools !**

```json
{
  "tools": ["chat_agent"]
}
```

**ERREUR FATALE a eviter :**
```json
{
  "tools": ["chat_agent", "legifrance_consult"]
}
```
Le Master court-circuite l'orchestration et appelle Legifrance directement !

### OPTIMISATION : system_prompt_ref

Le Master utilise system_prompt_ref pour economiser 10,000+ tokens :

```
Phase 1 : chat_agent(system_prompt_ref="legal/planner/v1", tools=[])
Phase 2 : chat_agent(system_prompt_ref="legal/researcher/v1", tools=["legifrance_consult"])
Phase 3 : chat_agent(system_prompt_ref="legal/evaluator/v1", tools=[], thread_id=researcher_thread)
```

Les prompts sont charges automatiquement depuis prompts.db.

## METRIQUES ATTENDUES

### Question Simple 1 code 1-2 articles

- Iterations : Planner 1 + Researcher 5-6 + Evaluator 1 = ~8 total
- Duree : 30-60 secondes
- Appels tools :
  - 1x Planner
  - 1x Researcher (5-6 iterations internes : decouverte, ciblage, forage, lecture, synthese)
  - 1x Evaluator

### Cas Pratique Complexe 3 codes 10 articles

- Iterations : 20-30
- Duree : 3-5 minutes
- Appels tools :
  - 1x Planner (produit 2-4 taches)
  - 2-4x Researchers (1 par tache, ~6 iter chacun)
  - 2-4x Evaluators
  - 0-2x Corrections

### Tests valides (2026-02-07)

| Test | Resultat | Detail |
|------|----------|--------|
| Mariage Code civil (simple) | OK 5 iter | Code petit, passe toujours |
| SARL comptes Code commerce (moyen) | OK 6-8 iter | Fix critique anti-overload |
| Planner licenciement (complexe) | 3 taches + code_id + nav | Plan detaille |
| E2E Planner→Researcher→Evaluator | OK | Mutation thread fonctionne, audit sur pieces |

## PROTECTIONS ANTI-OVERLOAD

### Côté tool (automatique)

Le tool `legifrance_consult` refuse automatiquement :
- `get_section_tree` avec `max_depth > 2` sans `section_id` → erreur explicite
- Si `max_size_kb` non fourni → forcé automatiquement (300 racine, 500 section)

Code : `src/tools/_legifrance_consult/validators.py`

### Côté prompt Researcher (comportemental)

Le prompt impose le protocole anti-overload en 5 étapes :
1. depth=2, include_articles=false, max_size_kb=300 (decouverte)
2. Cibler un section_id
3. depth=4, include_articles=true, max_size_kb=500 (forage)
4. get_articles max 20 IDs
5. Synthese

### Tailles réelles des gros codes (arbre depth=10)

- Code du travail : 128 MB
- Code monetaire et financier : 127 MB
- Code de la sante publique : 122 MB
- Code rural : 95 MB
- Code de la securite sociale : 73 MB
- Code de l'environnement : 49 MB
- Code de commerce : 39 MB

## TROUBLESHOOTING

### Probleme Le Master ne delegue pas

**Symptome** : Le Master repond directement sans appeler chat_agent.
**Cause** : Le prompt n'est pas assez strict.
**Solution** : Ajouter en debut de prompt :
"INTERDICTION ABSOLUE DE REPONDRE DIRECTEMENT. TU DOIS UTILISER chat_agent POUR CHAQUE PHASE."

### Probleme Le Researcher hallucine

**Symptome** : L'Evaluator rejette systematiquement avec "Article absent des preuves".
**Cause** : Le Researcher cite de memoire au lieu de lire les textes.
**Solution** : Verifier que le Researcher suit le protocole anti-overload et appelle get_articles.

### Probleme Boucle infinie Researcher-Evaluator

**Symptome** : Le systeme depasse max_iterations.
**Cause** : L'Evaluator est trop strict ou le feedback est ambigu.
**Solution** : Limite a 2 tentatives de correction (deja dans PHASE 4).

### Probleme ContextTooLarge sur legifrance_consult

**Symptome** : Erreur "ContextTooLarge" ou timeout.
**Cause** : get_section_tree sur racine d'un gros code sans protection.
**Solution** : La protection côté tool refuse desormais depth>2 sans section_id automatiquement. Si le probleme persiste, verifier que le Researcher utilise max_size_kb.

### Probleme Le Master utilise legifrance_consult directement

**Symptome** : Le Master appelle legifrance_consult au lieu de deleguer.
**Cause** : Le Master a les 2 tools disponibles.
**Solution** : NE DONNER QUE tools=["chat_agent"] au Master. JAMAIS ["chat_agent", "legifrance_consult"].

### Probleme output_mode=debug explose le contexte

**Symptome** : Erreur "prompt too long" apres un appel Researcher.
**Cause** : Le mode debug inclut les retours complets des tools (arbres, articles) dans la reponse.
**Solution** : JAMAIS output_mode="debug" en production sur les gros codes. Utiliser "minimal" partout.

## EVOLUTION FUTURE

### Phase 2 Memoire Longue Duree

Ajouter un tool memory_bank pour stocker :
- Jurisprudence constante (articles souvent consultes)
- Historique des cas pratiques traites
- Cache des plans Planner (patterns recurrents)

### Phase 3 Agent Correcteur Autonome

Si Evaluator rejette 2 fois, passer a un Agent Correcteur specialise qui :
- Reformule la question initiale
- Suggere des codes alternatifs
- Propose une recherche par mots-cles elargie

### Phase 4 Multi-Modeles

- Master : gpt-5.2 (orchestration)
- Planner : claude-sonnet-4-5 (analyse structurelle)
- Researcher : qwen3-next:80b (recherche exhaustive)
- Evaluator : gpt-5.2 (rigueur maximale)