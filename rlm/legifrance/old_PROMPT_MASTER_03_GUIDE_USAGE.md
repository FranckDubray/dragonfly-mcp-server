# GUIDE UTILISATION - Systeme Orchestrateur Juridique

Version: 2.0
Date: 2026-02-05

---

## OBJECTIF

Permettre a un LLM de repondre a des questions juridiques avec une garantie ZERO HALLUCINATION en s&#39;appuyant EXCLUSIVEMENT sur le corpus Legifrance.

## ARCHITECTURE

### Vue Conceptuelle

```
User Question
     ↓
Master LLM (Orchestrateur)
     ↓
┌────┴────┬────────┬──────────┐
│         │        │          │
Planner  Researcher  Evaluator
│         │        │          │
└─────────┴────────┴──────────┘
     ↓
Tool: legifrance_consult
     ↓
Corpus Legifrance (PostgreSQL)
```

### Schema Technique Detaille

```mermaid
graph TD
    User[Utilisateur]
    
    subgraph Master [Thread Master]
        M1[Master LLM]
        M2[System Prompt Master]
    end
    
    subgraph Planner [Thread Planner]
        P1[Planner LLM]
        P2[System Prompt Planner]
    end
    
    subgraph Researcher [Thread Researcher]
        R1[Researcher LLM]
        R2[System Prompt Researcher]
        R3[Historique 5 iterations]
    end
    
    subgraph Evaluator [MEME Thread Researcher]
        E1[Evaluator LLM]
        E2[System Prompt Evaluator]
        E3[REUTILISE Historique]
    end
    
    subgraph Tools [Outils MCP]
        ChatAgent[Tool chat agent]
        Legi[Tool legifrance consult]
    end

    User --&gt;|Question| M1
    M2 -.-&gt;|Guide| M1
    
    M1 --&gt;|Tool call chat agent| ChatAgent
    ChatAgent --&gt;|Cree thread planner| P1
    P2 -.-&gt;|Guide| P1
    
    P1 --&gt;|Tool call chat agent| ChatAgent
    ChatAgent --&gt;|Cree thread researcher| R1
    R2 -.-&gt;|Guide| R1
    
    R1 --&gt;|5x Tool call| Legi
    Legi --&gt;|Textes bruts| R1
    R1 --&gt;|Reponse finale| R3
    
    P1 --&gt;|Mutation thread researcher| ChatAgent
    ChatAgent --&gt;|Injecte nouveau prompt| E1
    E2 -.-&gt;|Ecrase R2| E1
    E3 -.-&gt;|Lit R3| E1
    
    E1 --&gt;|Verdict| Check{Conforme}
    
    Check --&gt;|NON| P1
    P1 --&gt;|Relance Researcher| ChatAgent
    
    Check --&gt;|OUI| P1
    P1 --&gt;|Retourne a Master| M1
    M1 --&gt;|Reponse finale| User

    style M1 fill:#e1f5ff,stroke:#333,stroke-width:3px
    style P1 fill:#fff3cd,stroke:#333,stroke-width:2px
    style R1 fill:#d1ecf1,stroke:#333,stroke-width:2px
    style E1 fill:#f8d7da,stroke:#333,stroke-width:2px
    style E3 fill:#ffe6e6,stroke:#f00,stroke-width:2px,stroke-dasharray:5
```

**Legende** :
- Ligne pleine : Nouveaux threads
- Ligne pointillee rouge : Reutilisation du thread Researcher avec nouveau prompt
- Les styles de couleur indiquent les differents agents

## LANCEMENT DU TEST

### Configuration MCP CRITIQUE

**ATTENTION : Le Master ne doit avoir QUE chat agent dans ses tools !**

```json
{
  &quot;tools&quot;: [&quot;chat_agent&quot;]
}
```

**ERREUR FATALE a eviter :**
```json
{
  &quot;tools&quot;: [&quot;chat_agent&quot;, &quot;legifrance_consult&quot;]
}
```
Le Master court-circuite l&#39;orchestration et appelle Legifrance directement !

### Commande Test Question Simple

```json
{
  &quot;tool&quot;: &quot;chat_agent&quot;,
  &quot;params&quot;: {
    &quot;message&quot;: &quot;Quel est l&#39;age minimum pour se marier en France ?&quot;,
    &quot;model&quot;: &quot;gpt-5.2&quot;,
    &quot;tools&quot;: [&quot;chat_agent&quot;],
    &quot;system_prompt&quot;: &quot;[CONTENU COMPLET DU FICHIER PROMPT_MASTER_01_ORCHESTRATEUR.md]&quot;,
    &quot;output_mode&quot;: &quot;intermediate&quot;,
    &quot;temperature&quot;: 0.3,
    &quot;max_iterations&quot;: 20
  }
}
```

### Commande Test Cas Pratique Complexe

```json
{
  &quot;tool&quot;: &quot;chat_agent&quot;,
  &quot;params&quot;: {
    &quot;message&quot;: &quot;Compare les differents regimes de retraite prevus par le Code de la securite sociale&quot;,
    &quot;model&quot;: &quot;gpt-5.2&quot;,
    &quot;tools&quot;: [&quot;chat_agent&quot;],
    &quot;system_prompt&quot;: &quot;[CONTENU COMPLET DU FICHIER PROMPT_MASTER_01_ORCHESTRATEUR.md]&quot;,
    &quot;output_mode&quot;: &quot;intermediate&quot;,
    &quot;temperature&quot;: 0.3,
    &quot;max_iterations&quot;: 50
  }
}
```

### OPTIMISATION v2.0 : system_prompt_ref

Le Master utilise desormais system_prompt_ref pour economiser 10,000+ tokens :

```
Phase 1 : chat_agent(system_prompt_ref=&quot;legal/planner/v1&quot;)
Phase 2 : chat_agent(system_prompt_ref=&quot;legal/researcher/v1&quot;)
Phase 3 : chat_agent(system_prompt_ref=&quot;legal/evaluator/v1&quot;)
```

Les prompts sont charges automatiquement depuis prompts.db.
Le Master n&#39;a jamais les prompts dans son contexte.

## INTERPRETATION DES RESULTATS

### Mode Minimal (nouveau defaut)

```json
{
  &quot;success&quot;: true,
  &quot;response&quot;: &quot;L&#39;age minimum pour se marier en France est 18 ans revolus selon l&#39;article 144 du Code civil...&quot;,
  &quot;tools_used&quot;: [&quot;legifrance_consult&quot;],
  &quot;thread_id&quot;: &quot;thread_stream_ABC123&quot;
}
```

Economie : 80% de tokens vs mode debug.

### Mode Intermediate (pour monitoring)

Vous verrez :
- `tools_used`: [&quot;chat_agent&quot;] (recursion)
- `operations_summary`: Nombre d&#39;appels a chaque agent
- `context_info`: Nombre de messages et iterations

### Mode Debug (developpement uniquement)

Vous aurez acces a :
- `operations`: Detail complet de chaque appel (Planner → Researcher → Evaluator)
- `transcript_snapshot`: Historique des 10 derniers messages
- `usage`: Tokens consommes

## INDICATEURS DE QUALITE

### Reponse VALIDE

```
Reponse a votre question juridique

L&#39;age minimum pour se marier en France est 18 ans revolus.

Sources juridiques citees
- Article 144 du Code civil (VIGUEUR)

Methodologie appliquee
- Verification conformite sources
- Validation textes en vigueur
- Audit anti-hallucination

Fiabilite : 100 pourcent (Sources verifiees)
```

### Reponse REJETEE Exemple

```
Erreur de conformite detectee lors de l&#39;audit.

Violations :
- CRITIQUE : Article L123-4 cite mais absent des preuves Legifrance
- MAJEURE : Citation de l&#39;article 144 infidele au texte original

Nouvelle tentative de recherche en cours...
```

## METRIQUES ATTENDUES

### Question Simple 1 code 1 article

- Iterations : 5-10
- Tokens : 8,000-12,000 (vs 20,000-30,000 avant v2.0)
- Duree : 30-60 secondes
- Appels tools :
  - 1x Planner
  - 1x Researcher (5-6 iterations internes)
  - 1x Evaluator

### Cas Pratique Complexe 3 codes 10 articles

- Iterations : 20-40
- Tokens : 30,000-50,000 (vs 80,000-150,000 avant v2.0)
- Duree : 3-5 minutes
- Appels tools :
  - 1x Planner
  - 3-5x Researchers (1 par domaine)
  - 3-5x Evaluators
  - 0-2x Corrections

## TROUBLESHOOTING

### Probleme Le Master ne delegue pas

**Symptome** : Le Master repond directement sans appeler chat_agent.

**Cause** : Le prompt n&#39;est pas assez strict.

**Solution** : Ajouter en debut de prompt :
&quot;INTERDICTION ABSOLUE DE REPONDRE DIRECTEMENT. TU DOIS UTILISER chat_agent POUR CHAQUE PHASE.&quot;

### Probleme Le Researcher hallucine

**Symptome** : L&#39;Evaluator rejette systematiquement avec &quot;Article absent des preuves&quot;.

**Cause** : Le Researcher cite de memoire au lieu de lire les textes.

**Solution** : Verifier que output_mode=minimal pour le Researcher (force tracabilite).

### Probleme Boucle infinie Researcher-Evaluator

**Symptome** : Le systeme depasse max_iterations.

**Cause** : L&#39;Evaluator est trop strict ou le feedback est ambigu.

**Solution** : Limite a 2 tentatives de correction (deja dans PHASE 4).

### Probleme Timeout legifrance consult

**Symptome** : Erreur &quot;legifrance_consult timeout&quot;.

**Cause** : Requete trop lourde (depth=10 sur code complet).

**Solution** : Le Researcher doit utiliser depth progressif (2→4→6).

### Probleme Le Master utilise legifrance consult directement

**Symptome** : Le Master appelle legifrance_consult au lieu de deleguer.

**Cause** : Le Master a les 2 tools disponibles.

**Solution** : NE DONNER QUE `tools=[&quot;chat_agent&quot;]` au Master. JAMAIS `[&quot;chat_agent&quot;, &quot;legifrance_consult&quot;]`.

### Probleme Explosion tokens

**Symptome** : Erreur &quot;prompt too long&quot;.

**Cause** : Le Master charge les prompts dans son contexte au lieu d&#39;utiliser system_prompt_ref.

**Solution** : Verifier que le Master utilise system_prompt_ref=&quot;legal/planner/v1&quot; (PAS system_prompt).

## EVOLUTION FUTURE

### Phase 2 Memoire Longue Duree

Ajouter un tool `memory_bank` pour stocker :
- Jurisprudence constante (articles souvent consultes)
- Historique des cas pratiques traites
- Cache des plans Planner (patterns recurrents)

### Phase 3 Agent Cur Autonome

Si Evaluator rejette 2 fois, passer a un Agent Correcteur specialise qui :
- Reformule la question initiale
- Suggere des codes alternatifs
- Propose une recherche par mots-cles elargie

### Phase 4 Multi-Modeles

- Master : gpt-5.2 (orchestration)
- Planner : claude-sonnet-4-5 (analyse structurelle)
- Researcher : qwen3-next:80b (recherche exhaustive)
- Evaluator : gpt-5.2 (rigueur maximale)

## CHANGELOG

### v2.0 (2026-02-05)
- BREAKING : system_prompt_ref remplace system_prompt (economie 10k+ tokens)
- BREAKING : Mode minimal obligatoire partout (economie 5k+ tokens)
- Architecture Master + Planner separee validee
- Prompts stockes dans SQLite (prompts.db)
- Tool get_prompt SQLite-based

### v1.0 (2026-02-04)
- Creation architecture Planner/Researcher/Evaluator
- Prompts embarques dans Master
- Mutation de thread pour economie tokens
- Tests valides sur questions simples
