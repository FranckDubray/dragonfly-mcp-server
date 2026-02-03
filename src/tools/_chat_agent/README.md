# Chat Agent (Threaded Conversations)

**Agent conversationnel persistant avec exécution d'outils et stockage serveur via Platform Threading API.**

---

## 🎯 Objectif

`chat_agent` permet de mener des conversations longues et persistantes avec un LLM, tout en lui donnant accès à des outils (MCP). Contrairement à `call_agent` (client-side state), `chat_agent` stocke **tout l'historique côté serveur** via l'API Platform Threads.

### Cas d'usage typiques

✅ **Chatbots persistants** : L'utilisateur peut quitter et revenir, la conversation reprend où elle s'était arrêtée  
✅ **Assistants longue durée** : Accumulation de contexte sur plusieurs heures/jours  
✅ **Multi-device** : Accès au même thread depuis différents clients  
✅ **Workflows interactifs** : L'agent utilise des outils pour accomplir des tâches complexes en plusieurs étapes

---

## 📊 Différences avec l'existant

| Feature | `call_llm` | `call_agent` (v1) | `chat_agent` (v2) |
|---------|-----------|-------------------|-------------------|
| **Tours** | 1 (tool use unique) | N (multi-turn) | N (multi-turn) |
| **Persistance** | ❌ Aucune | Client-side (`state`) | ✅ Server-side (`thread_id`) |
| **API** | Stateless | Stateless | Stateful (Threads API) |
| **Contexte** | Manuel | Manuel (`resume_from`) | ✅ Automatique (chargement) |
| **Output** | Verbeux | Verbeux | 🎚️ 3 modes (minimal/intermediate/debug) |

---

## 🚀 Usage Rapide

### Nouvelle conversation

```python
result = chat_agent(
    message="Bonjour, aide-moi à analyser des données SQL",
    model="gpt-5.2",
    tools=["sqlite_db", "date", "math"],
    output_mode="minimal"
)

# result:
# {
#   "success": true,
#   "response": "Bonjour ! Je suis prêt à vous aider...",
#   "tools_used": []
# }

# Extraire le thread_id pour la suite
thread_id = result.get("thread_id")  # (présent en mode intermediate/debug)
```

### Continuation (même conversation)

```python
result2 = chat_agent(
    message="Crée une table 'produits' avec 5 colonnes",
    model="gpt-5.2",
    tools=["sqlite_db"],
    thread_id=thread_id,  # ← Reprise du contexte
    output_mode="intermediate"
)

# result2:
# {
#   "success": true,
#   "response": "J'ai créé la table 'produits' avec...",
#   "tools_used": ["sqlite_db"],
#   "thread_id": "thread_stream_...",
#   "operations_summary": [...],
#   "context_info": {"message_count": 4, "total_iterations": 2}
# }
```

---

## 📋 Paramètres

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `message` | string | ✅ | - | Message utilisateur |
| `model` | string | ✅ | - | Nom du modèle (ex: `gpt-5.2`, `qwen3-next:80b`) |
| `tools` | array | ❌ | `[]` | Outils MCP disponibles (si vide = conversation pure) |
| `thread_id` | string | ❌ | - | ID du thread pour continuer une conversation |
| `output_mode` | enum | ❌ | `intermediate` | Niveau de détail (`minimal`, `intermediate`, `debug`) |
| `max_iterations` | integer | ❌ | 10 | Limite d'itérations (anti-boucle infinie) |
| `timeout` | integer | ❌ | 300 | Timeout global en secondes |
| `temperature` | float | ❌ | 0.5 | Température LLM (0.0-2.0) |
| `system_prompt` | string | ❌ | (défaut) | Prompt système custom |
| `parallel_execution` | boolean | ❌ | `true` | Exécuter tools indépendants en parallèle |

---

## 🎚️ Modes de Sortie

### Mode `minimal` (pour chatbots)

Retour le plus simple possible :

```json
{
  "success": true,
  "response": "Voici ma réponse...",
  "tools_used": ["date", "math"]
}
```

**Usage** : UI chatbot où seule la réponse finale compte.

---

### Mode `intermediate` (pour production)

Ajoute contexte utile pour debug/logs :

```json
{
  "success": true,
  "response": "Voici ma réponse...",
  "tools_used": ["sqlite_db"],
  "thread_id": "thread_stream_ABC123",
  "operations_summary": [
    {"iteration": 1, "tools": ["sqlite_db"], "count": 1},
    {"iteration": 2, "tools": [], "count": 0}
  ],
  "context_info": {
    "message_count": 6,
    "total_iterations": 2
  }
}
```

**Usage** : Applications production avec besoin de traçabilité.

---

### Mode `debug` (pour développement)

Détails complets (arguments, résultats, usage) :

```json
{
  "success": true,
  "response": "...",
  "tools_used": ["sqlite_db"],
  "thread_id": "thread_stream_ABC123",
  "iterations": 2,
  "operations": [
    {
      "iteration": 1,
      "tool_calls": [
        {
          "name": "sqlite_db",
          "arguments": "{\"operation\":\"create_db\",\"name\":\"test.db\"}",
          "result": {"success": true, "path": "sqlite3/test.db"}
        }
      ]
    }
  ],
  "usage": {
    "prompt_tokens": 1500,
    "completion_tokens": 200,
    "total_tokens": 1700
  },
  "context_info": {...},
  "transcript_snapshot": [...]  // 10 derniers messages
}
```

**Usage** : Debug, tests, analyse de performance.

---

## 🛡️ Gestion du Contexte

### Vérification préventive

Avant chaque appel LLM, `chat_agent` **estime le nombre de tokens** de l'historique et compare à la limite du modèle.

```python
# Si contexte > 90% de la limite du modèle
{
  "error": "ContextTooLarge",
  "message": "Conversation too long for model gpt-5.2 (estimated: 95000 tokens, limit: 100000)",
  "hint": "Please start a new thread",
  "estimated_tokens": 95000,
  "context_limit": 100000
}
```

**Action** : L'utilisateur doit créer un nouveau thread (impossible de truncate automatiquement car perte de cohérence).

---

## 🔧 Architecture Technique

```
agent.py (entry point)
  ↓
  [Validation] (validators.py, model_validator.py)
  ↓
  [Thread Loading] (platform_api.py → GET /user/threads/{id})
  ↓
  [Context Check] (thread_utils.py → estimate_tokens)
  ↓
  loop.py (multi-turn)
    ↓
    1. Call LLM (platform_api.py → streaming.py)
    2. If tool_calls:
       ↓
       executor.py (parallel/sequential)
       ↓
       Add tool results to transcript (thread_chain.py)
    3. Repeat until finish_reason == "stop"
  ↓
  [Output Formatting] (output_builder.py)
```

**Composants critiques** :

- `thread_chain.py` : Gestion des IDs (`id`, `parentId`, `level`) pour éviter les branches
- `streaming.py` : Parsing SSE pour extraction `tool_calls`, `thread_id`, `usage`
- `thread_utils.py` : Conversion historique Platform → messages OpenAI

---

## ⚠️ Limitations & Bonnes Pratiques

### ✅ À FAIRE

1. **Stocker le `thread_id`** : Indispensable pour reprendre la conversation
2. **Mode `minimal` pour chatbots** : Évite overhead inutile
3. **Surveillance du contexte** : Surveiller `context_info.message_count`
4. **Température basse pour workflows** : 0.3-0.5 pour tâches déterministes

### ⚠️ À ÉVITER

1. **Perdre le `thread_id`** : Impossible de reprendre sans
2. **Conversations infinies** : Au-delà de 50-100 messages, créer un nouveau thread
3. **Tools inutiles** : Ne fournir que les tools nécessaires (< 10 idéalement)
4. **Mode `debug` en production** : Coûteux en bande passante

---

## 🧪 Tests

### Test 1 : Conversation simple (sans tools)

```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "chat_agent",
    "params": {
      "message": "Bonjour, quelle heure est-il ?",
      "model": "gpt-4o-mini",
      "tools": [],
      "output_mode": "minimal"
    }
  }'
```

**Attendu** : Réponse directe (pas de tool use).

---

### Test 2 : Workflow avec tools

```bash
# Tour 1 : Créer une DB
curl -X POST http://127.0.0.1:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "chat_agent",
    "params": {
      "message": "Crée une DB SQLite nommée test.db",
      "model": "gpt-5.2",
      "tools": ["sqlite_db"],
      "output_mode": "intermediate"
    }
  }'

# Extraire thread_id de la réponse

# Tour 2 : Insérer des données
curl -X POST http://127.0.0.1:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "chat_agent",
    "params": {
      "message": "Insère 3 lignes dans une table users",
      "model": "gpt-5.2",
      "tools": ["sqlite_db"],
      "thread_id": "thread_stream_...",
      "output_mode": "intermediate"
    }
  }'
```

**Attendu** : Le LLM se souvient de `test.db` et l'utilise.

---

### Test 3 : Erreur contexte trop grand

```python
# Simuler un thread avec 1000+ messages (via boucle)
for i in range(200):
    result = chat_agent(
        message=f"Message {i}",
        model="gpt-4o-mini",
        thread_id=thread_id,
        tools=[]
    )

# Après ~150-200 messages (selon modèle)
# result["error"] == "ContextTooLarge"
```

---

## 📚 Voir Aussi

- **Spécification complète** : `docs/chat_agent/SPECIFICATION.md`
- **Spec JSON** : `src/tool_specs/chat_agent.json`
- **Ancienne version** : `src/tools/_call_llm_agent/` (pour comparaison)
- **Guide Threading API** : `docs/chat-completion-threading-guide.md`
