# PROMPTS DES AGENTS

Version: 3.0
Date: 2026-02-07

---

## PROMPT_PLANNER

**Enrichi avec connaissance Legifrance**

Stocké dans `prompts.db` : `domain=legal, agent_type=planner, version=v1`

Points clés :
- **15 codes principaux avec code_id** : mapping titre → LEGITEXT... intégré dans le prompt
- **Connaissance du tool legifrance_consult** : 4 opérations documentées (list_codes, search_sections, get_section_tree, get_articles)
- **Avertissement overload** : tailles réelles des codes (Travail=128MB, Santé=122MB, Commerce=39MB)
- **Format enrichi** : chaque tâche inclut code_id, instruction_recherche détaillée, mots_clés_fallback, conseil_navigation
- **Fallback list_codes** : si code pas dans les 15 connus, le Researcher utilise list_codes

Format de sortie par tâche :

```json
{
  "id": 1,
  "code": "Code de commerce",
  "code_id": "LEGITEXT000005634379",
  "question": "...",
  "instruction_recherche": "Navigue le Code de commerce. Découverte : get_section_tree(code_id, max_depth=2, include_articles=false, max_size_kb=300). Cible le Livre II > Titre III...",
  "mots_cles_fallback": ["gérant", "comptes annuels"],
  "conseil_navigation": "Les SARL sont dans Livre II > Titre III"
}
```

## PROMPT_RESEARCHER

**Anti-overload + format preuves**

Stocké dans `prompts.db` : `domain=legal, agent_type=researcher, version=v1`

Points clés :
- **PROTOCOLE ANTI-OVERLOAD obligatoire** : depth=2 découverte → ciblage section_id → depth=4 forage → get_articles
- **Interdictions absolues** : jamais depth>2 sans section_id, jamais depth>4 sans section ciblée, toujours max_size_kb
- **Protection côté tool** : le tool `legifrance_consult` refuse automatiquement depth>2 sans section_id (validators.py)
- **Justification des contraintes** : explique POURQUOI (Code du travail=128MB, Santé=122MB)
- **Format preuves structuré** : Article ID, texte intégral, état, dates — pour audit Evaluator
- **Fallback search_sections** : accents obligatoires, bascule après 2 échecs
- **Max 20 articles par get_articles** (pas 50)

Séquence type d'un Researcher :

```
1. get_section_tree(code_id=X, max_depth=2, include_articles=false, max_size_kb=300)
2. Identifier section_id pertinent
3. get_section_tree(section_id=X, max_depth=4, include_articles=true, max_size_kb=500)
4. get_articles([IDs], include_links=false)  — max 20 IDs
5. Synthèse avec Sources + Preuves
```

Format de réponse du Researcher :

```
## Sources trouvées
**Article [Numéro] du [Code]** (VIGUEUR)
Texte : "[Citation exacte ou paraphrase fidèle]"

## Réponse à la question
[Réponse directe basée sur les sources ci-dessus]

## Preuves (pour validation)
Article ID: [LEGIARTI...]
Texte intégral: [...]
État: VIGUEUR
Date début: [...]
Date fin: [...]
```

## PROMPT_EVALUATOR

**Audit sur pièces via mutation de thread**

Stocké dans `prompts.db` : `domain=legal, agent_type=evaluator, version=v1`

Points clés :
- **Contexte explicite** : l'Evaluator sait qu'il reprend un thread du Researcher, pas le sien
- **Méthode d'audit en 3 étapes** :
  - ÉTAPE 1 : Identifier la réponse du Researcher (dernier message assistant avant lui)
  - ÉTAPE 2 : Identifier les retours bruts des tools dans le thread (messages de type "tool" = retours legifrance_consult)
  - ÉTAPE 3 : Confronter chaque article cité avec les retours bruts (5 critères)
- **Checklist 5 points** : EXISTENCE (article dans un retour get_articles ?), VIGUEUR, FIDÉLITÉ (texte cité vs texte brut), PERTINENCE, HALLUCINATION (affirmation sans source dans le thread)
- **Seuil** : score >= 90 ET aucune CRITIQUE → VALIDE, sinon REJETE avec feedback

Format de sortie :

```json
{
  "status": "VALIDE ou REJETE",
  "violations": [
    {
      "regle": "EXISTENCE",
      "gravite": "CRITIQUE",
      "details": "Article L123-4 cité mais absent des retours get_articles du thread"
    }
  ],
  "feedback_correction": "Recherche à nouveau l'article L123-4 ou supprime-le de ta réponse",
  "score_conformite": 85,
  "articles_valides": ["LEGIARTI000027431990"],
  "articles_problematiques": ["L123-4"]
}
```

## NOTES TECHNIQUES

### Mutation de Thread (validée)

Le Master réutilise le thread_id du Researcher pour l'Evaluator :
- L'Evaluator a accès à TOUT l'historique (appels tools + retours bruts)
- Le nouveau system_prompt ÉCRASE l'ancien mais l'historique factuel reste
- Les retours des tools (messages de type "tool") sont visibles dans le thread
- L'Evaluator audite sur pièces en comparant retours bruts vs réponse
- Pas besoin de donner legifrance_consult à l'Evaluator

### Gestion des Prompts

- Prompts stockés dans SQLite (`prompts.db`)
- Références par `system_prompt_ref` format `legal/{agent_type}/v1`
- Le Master utilise `system_prompt_ref` (pas `system_prompt`) pour économie tokens
- output_mode=minimal pour tous les agents

### Architecture

- Le Master est un LLM dans un portail utilisateur, il a UNIQUEMENT `tools=["chat_agent"]`
- Le Planner a `tools=[]` (pas chat_agent — il planifie, pas d'orchestration)
- Le Researcher a `tools=["legifrance_consult"]`
- L'Evaluator a `tools=[]` et réutilise le thread du Researcher