# LLM Agent (Multi-turn Tool Orchestration)

**Orchestrateur LLM avec enchaînement automatique de tools en séquence.**

Le LLM peut appeler plusieurs tools en séquence, en utilisant les résultats précédents pour décider des prochains appels. S'arrête naturellement quand `finish_reason="stop"`.

---

## 🚀 Fonctionnalités

- ✅ **Boucle multi-tours** : Le LLM continue jusqu'à avoir toutes les infos
- ✅ **Exécution parallèle** : Tools indépendants exécutés simultanément (gain latence)
- ✅ **Gestion d'erreurs** : Le LLM peut adapter sa stratégie si un tool échoue
- ✅ **Timeout global** : Sécurité anti-blocage (défaut: 300s)
- ✅ **Cost breakdown** : Tracking détaillé des coûts par itération
- ✅ **Debug détaillé** : Trace complète de chaque tour

---

## 📋 Paramètres

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `message` | string | ✅ | - | Question ou instruction utilisateur |
| `model` | string | ✅ | - | Nom du modèle LLM (ex: `qwen3-next:80b`) |
| `tool_names` | array | ✅ | - | Liste des tools MCP disponibles |
| `max_iterations` | integer | ❌ | 20 | Limite de sécurité (anti-boucle infinie) |
| `agent_prompt` | string | ❌ | (défaut) | Prompt system custom pour guider l'agent |
| `temperature` | number | ❌ | 0.5 | Température échantillonnage (0.1-1.0) |
| `timeout_seconds` | integer | ❌ | 300 | Timeout global en secondes (max: 600) |
| `parallel_execution` | boolean | ❌ | true | Exécuter tools indépendants en parallèle |
| `early_stop_on_error` | boolean | ❌ | false | Arrêter au 1er tool qui échoue |
| `debug` | boolean | ❌ | false | Debug détaillé (track chaque itération) |
| `include_cost_breakdown` | boolean | ❌ | true | Inclure analyse coûts |

---

## 🎯 Cas d'usage : Recherche Legifrance

### Problème

Le workflow nécessite **plusieurs appels séquentiels dépendants** :

1. `list_codes()` → Obtenir la liste des codes
2. `get_tree(code="Code civil")` → Obtenir l'arborescence (nécessite résultat étape 1)
3. `get_articles(section="Titre V")` → Obtenir articles (nécessite résultat étape 2)

Le tool `call_llm` classique ne peut pas gérer ça (tous les tool_calls sont décidés d'avance).

### Solution avec `call_llm_agent`

```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_reg": "call_llm_agent",
    "params": {
      "message": "Trouve-moi les articles du Code civil sur le mariage",
      "model": "qwen3-next:80b",
      "tool_names": ["legifrance_list_codes", "legifrance_get_tree", "legifrance_get_articles"],
      "max_iterations": 10,
      "temperature": 0.3,
      "debug": true
    }
  }'
```

### Déroulement automatique

```
┌─────────────────────────────────────────────────────────────┐
│ Tour 1 : Découverte                                         │
├─────────────────────────────────────────────────────────────┤
│ LLM → "Je dois d'abord voir les codes disponibles"         │
│ Tool call: list_codes()                                     │
│ Résultat: ["Code civil", "Code pénal", ...]                │
│ finish_reason: "tool_calls" → CONTINUE                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Tour 2 : Navigation                                         │
├─────────────────────────────────────────────────────────────┤
│ LLM voit le résultat du tour 1                              │
│ LLM → "Maintenant je récupère l'arborescence du Code civil"│
│ Tool call: get_tree(code="Code civil")                     │
│ Résultat: {arborescence avec "Titre V: Du mariage"}        │
│ finish_reason: "tool_calls" → CONTINUE                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Tour 3 : Extraction                                         │
├─────────────────────────────────────────────────────────────┤
│ LLM voit l'arborescence complète                            │
│ LLM → "Je récupère les articles de la section mariage"     │
│ Tool call: get_articles(section="Titre V")                 │
│ Résultat: [Article 143, Article 144, ...]                  │
│ finish_reason: "tool_calls" → CONTINUE                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Tour 4 : Synthèse finale                                    │
├─────────────────────────────────────────────────────────────┤
│ LLM a tous les articles                                     │
│ LLM → Pas de tool_calls, répond directement                │
│ Réponse: "Voici les articles du Code civil sur le mariage: │
│           Article 143: Le mariage est contracté..."        │
│ finish_reason: "stop" → ARRÊT                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Réponse détaillée

```json
{
  "success": true,
  "content": "Voici les articles du Code civil concernant le mariage:\n\nArticle 143: Le mariage est contracté...\nArticle 144: ...",
  "finish_reason": "stop",
  "iterations": 3,
  "usage": {
    "prompt_tokens": 4850,
    "completion_tokens": 425,
    "total_tokens": 5275,
    "total_token_cost": 6065.5
  },
  "cost_breakdown": {
    "total_iterations": 3,
    "cumulative": {...},
    "per_iteration": [
      {"iteration": 1, "usage": {"prompt_tokens": 500, "completion_tokens": 20}},
      {"iteration": 2, "usage": {"prompt_tokens": 800, "completion_tokens": 30}},
      {"iteration": 3, "usage": {"prompt_tokens": 1200, "completion_tokens": 50}}
    ]
  },
  "debug": {
    "meta": {
      "model": "qwen3-next:80b",
      "tool_names": ["legifrance_list_codes", "legifrance_get_tree", "legifrance_get_articles"],
      "total_iterations": 3
    },
    "iterations": [
      {
        "iteration": 1,
        "finish_reason": "tool_calls",
        "tool_calls_count": 1,
        "tool_calls": [
          {
            "name": "legifrance_list_codes",
            "arguments": "{}",
            "result_preview": "[\"Code civil\", \"Code pénal\", ...]"
          }
        ]
      },
      {
        "iteration": 2,
        "finish_reason": "tool_calls",
        "tool_calls_count": 1,
        "tool_calls": [
          {
            "name": "legifrance_get_tree",
            "arguments": "{\"code\":\"Code civil\"}",
            "result_preview": "{\"Livre I\": \"Des personnes\", \"Titre V\": \"Du mariage\", ...}"
          }
        ]
      },
      {
        "iteration": 3,
        "finish_reason": "tool_calls",
        "tool_calls_count": 1,
        "tool_calls": [
          {
            "name": "legifrance_get_articles",
            "arguments": "{\"section\":\"Titre V\"}",
            "result_preview": "[{\"article\": \"143\", \"text\": \"Le mariage est contracté...\"}, ...]"
          }
        ]
      }
    ]
  }
}
```

---

## ⚙️ Architecture interne

```
core.py (orchestrateur)
  ↓
  while iteration < max_iterations:
    ↓
    loop.py (une itération)
      ↓
      1. Appel LLM avec tools
      2. Si tool_calls:
         ↓
         executor.py (exécution)
           ↓
           Parallèle (asyncio.gather) OU Séquentiel
         ↓
         Ajouter résultats aux messages
      3. Retour finish_reason
    ↓
    Si finish_reason == "tool_calls": CONTINUE
    Si finish_reason == "stop": ARRÊT
```

**Modules** :
- `core.py` : Boucle principale
- `loop.py` : Logique d'une itération
- `executor.py` : Exécution parallèle/séquentielle des tools
- `prompts.py` : Prompt system par défaut
- `debug_builder.py` : Construction debug détaillé
- `cost_calculator.py` : Calcul coûts cumulatifs
- `timeout_manager.py` : Gestion timeout global

---

## 🛡️ Sécurités

1. **`max_iterations`** : Limite à 20 tours par défaut (évite boucles infinies)
2. **`timeout_seconds`** : Timeout global à 300s (évite blocages)
3. **`early_stop_on_error`** : Option pour arrêter au 1er tool qui échoue
4. **Gestion des erreurs** : Les tools qui échouent retournent `{"error": "..."}`, le LLM peut adapter sa stratégie

---

## 📈 Performance & coûts

### Estimation tokens (3 tours)

| Tour | Prompt | Completion | Total |
|------|--------|------------|-------|
| 1 | 500 | 20 | 520 |
| 2 | 800 | 30 | 830 |
| 3 | 1200 | 50 | 1250 |
| **Synthèse** | 3000 | 300 | 3300 |
| **TOTAL** | **5500** | **400** | **5900** |

**Coût estimé** : ~5,3€ (avec model qwen3-next:80b @ 0.9/4 cts pour in/out)

**Ratio vs `call_llm` simple** : ~2x plus coûteux, mais **nécessaire** pour workflows séquentiels.

---

## 🎓 Bonnes pratiques

### ✅ À FAIRE

1. **Questions explicites** : "Trouve les articles du Code civil sur le mariage" (clair)
2. **Temperature basse** : 0.3-0.5 pour workflows déterministes
3. **Tools pertinents** : Ne fournir que les tools nécessaires (< 10)
4. **Debug activé** : Pour comprendre l'orchestration en dev

### ⚠️ À ÉVITER

1. **Questions vagues** : "Aide-moi avec Legifrance" (le LLM ne saura pas quoi faire)
2. **Trop de tools** : > 15 tools complique la décision du LLM
3. **`max_iterations` trop bas** : Si workflow complexe nécessite 7 tours, mettre max=5 échouera

---

## 🔧 Dépannage

### Problème : "Max iterations reached"

**Cause** : Le LLM continue d'appeler des tools sans s'arrêter  
**Solution** :
- Augmenter `max_iterations` (ex: 30)
- Simplifier la question
- Vérifier que les tools retournent des résultats complets

### Problème : "Global timeout reached"

**Cause** : Les tools sont trop lents ou nombreux  
**Solution** :
- Augmenter `timeout_seconds` (max: 600)
- Activer `parallel_execution=true`
- Optimiser les tools lents

### Problème : Coûts élevés

**Solution** :
- Réduire `max_iterations`
- Utiliser un modèle plus petit (ex: `qwen3:30b-a3b`)
- Désactiver `include_cost_breakdown` (léger gain)

---

## 🧪 Tests

### Test 1 : Workflow simple (2 tours)

```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_reg": "call_llm_agent",
    "params": {
      "message": "Quelle heure à Paris ? Calcule 25×47",
      "model": "qwen3-next:80b",
      "tool_names": ["date", "math"],
      "debug": true
    }
  }'
```

**Attendu** : 2 tours (date + math), réponse finale

### Test 2 : Workflow complexe (4 tours)

```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_reg": "call_llm_agent",
    "params": {
      "message": "Trouve les articles du Code du travail sur les congés payés",
      "model": "qwen3-next:80b",
      "tool_names": ["legifrance_list_codes", "legifrance_get_tree", "legifrance_get_articles"],
      "max_iterations": 10,
      "debug": true
    }
  }'
```

**Attendu** : 3-4 tours, arborescence complète récupérée

---

## 📚 Différences avec `call_llm`

| Critère | `call_llm` | `call_llm_agent` |
|---------|-----------|------------------|
| **Nombre de tours** | 2 (fixe) | N (dynamique) |
| **Dépendances tools** | ❌ Tous décidés d'avance | ✅ Séquentiels avec résultats |
| **Coût** | 1x | ~2-3x |
| **Latence** | Rapide | Variable (N tours) |
| **Use case** | Tools indépendants | Workflows séquentiels |

---

## 🔗 Voir aussi

- Tool `call_llm` (orchestration simple)
- Guide MCP tools : `LLM_DEV_GUIDE.md`
- Spec JSON : `src/tool_specs/call_llm_agent.json`

