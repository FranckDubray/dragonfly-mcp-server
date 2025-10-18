# 🧩 Orchestrator — Transforms & Decisions Reference

**Orchestrateur v1.1** — Référence complète des handlers et decisions disponibles.

---

## 🔢 Transforms Arithmétiques

### `increment`
**Description** : Incrémente une valeur de 1  
**Inputs** : `value` (int/float)  
**Outputs** : `result` (int si pas de décimale, sinon float)  
**Use case** : Compteurs de retry, itérations de boucle

**Exemple** :
```json
{
  "name": "increment_retry",
  "type": "transform",
  "handler": "increment",
  "inputs": {"value": "${cycle.meta.retry_count}"},
  "outputs": {"result": "cycle.meta.retry_count"}
}
```

---

### `decrement`
**Description** : Décrémente une valeur de 1  
**Inputs** : `value` (int/float)  
**Outputs** : `result` (int si pas de décimale, sinon float)  
**Use case** : Compteurs descendants, backoff

**Exemple** :
```json
{
  "name": "decrement_remaining",
  "type": "transform",
  "handler": "decrement",
  "inputs": {"value": "${cycle.remaining_items}"},
  "outputs": {"result": "cycle.remaining_items"}
}
```

---

### `add`
**Description** : Additionne deux valeurs  
**Inputs** : `value` (int/float), `amount` (int/float)  
**Outputs** : `result` (int si pas de décimale, sinon float)  
**Use case** : Calculs de scores, budgets

**Exemple** :
```json
{
  "name": "add_bonus",
  "type": "transform",
  "handler": "add",
  "inputs": {"value": "${cycle.score}", "amount": 10},
  "outputs": {"result": "cycle.final_score"}
}
```

---

### `multiply`
**Description** : Multiplie deux valeurs  
**Inputs** : `value` (int/float), `factor` (int/float)  
**Outputs** : `result` (int si pas de décimale, sinon float)  
**Use case** : Pondération, scaling

**Exemple** :
```json
{
  "name": "apply_weight",
  "type": "transform",
  "handler": "multiply",
  "inputs": {"value": "${cycle.raw_score}", "factor": 1.5},
  "outputs": {"result": "cycle.weighted_score"}
}
```

---

### `set_value`
**Description** : Affecte une valeur constante  
**Inputs** : `value` (any)  
**Outputs** : `result` (any)  
**Use case** : Initialisation de flags, constantes, marqueurs de phase

**Exemple** :
```json
{
  "name": "mark_phase",
  "type": "transform",
  "handler": "set_value",
  "inputs": {"value": "scoring"},
  "outputs": {"result": "cycle.meta.phase"}
}
```

---

## 📄 Transforms Domain (Texte, LLM, Données)

### `sanitize_text`
**Description** : Nettoie le texte (HTML, whitespace, truncate)  
**Inputs** :
- `text` (string, required)
- `max_length` (int, default: 10000)
- `remove_html` (bool, default: true)
- `normalize_whitespace` (bool, default: true)

**Outputs** :
- `text` (string) — texte nettoyé
- `truncated` (bool)
- `original_length` (int)
- `final_length` (int)

**Use case** : Nettoyage emails, scraping web, préparation prompts LLM

**Exemple** :
```json
{
  "name": "clean_email_body",
  "type": "transform",
  "handler": "sanitize_text",
  "inputs": {
    "text": "${cycle.msg.body}",
    "max_length": 5000,
    "remove_html": true
  },
  "outputs": {
    "text": "cycle.msg.clean_body",
    "truncated": "cycle.msg.truncated"
  }
}
```

---

### `normalize_llm_output`
**Description** : Parse la sortie LLM (JSON, lignes, texte)  
**Inputs** :
- `content` (string, required) — sortie LLM brute
- `expected_format` (string, default: "json") — "json" | "text" | "lines"
- `fallback_value` (any, default: null) — valeur si parse fail

**Outputs** :
- `parsed` (any) — valeur parsée
- `success` (bool)
- `error` (string, si échec)

**Use case** : Extraction JSON depuis markdown LLM, fallback graceful

**Exemple** :
```json
{
  "name": "parse_llm_response",
  "type": "transform",
  "handler": "normalize_llm_output",
  "inputs": {
    "content": "${cycle.llm_raw_output}",
    "expected_format": "json",
    "fallback_value": []
  },
  "outputs": {
    "parsed": "cycle.parsed_data",
    "success": "cycle.parse_ok"
  }
}
```

**Note** : Supporte extraction depuis markdown code blocks (```json ... ```)

---

### `json_stringify`
**Description** : Convertit objet Python en string JSON  
**Inputs** :
- `value` (any, required) — objet à stringifier
- `ensure_ascii` (bool, default: false) — escape non-ASCII
- `indent` (int, optional) — pretty-print

**Outputs** :
- `json_string` (string) — JSON stringifié
- `length` (int) — longueur string

**Use case** : Sauvegarde objets en SQLite TEXT, préparation payloads

**Exemple** :
```json
{
  "name": "stringify_results",
  "type": "transform",
  "handler": "json_stringify",
  "inputs": {"value": "${cycle.results}"},
  "outputs": {"json_string": "cycle.results_json"}
}
```

---

### `extract_field` ⭐ (Multi-Capable)
**Description** : Extrait un ou plusieurs champs depuis objet nested (JSONPath-like)  
**Modes** :
- **Simple** : `path` → extrait 1 champ
- **Multi** : `paths` → extrait N champs en 1 appel

**Inputs** :
- `data` (dict/list, required)
- `path` (string, optional) — chemin pointé simple (ex: "user.name")
- `paths` (dict, optional) — map {output_key: path} pour multi-extraction
- `default` (any, default: null) — valeur par défaut si absent

**Outputs** :
- **Mode simple** : `value` (any) — valeur extraite
- **Mode multi** : `{output_key1: val1, output_key2: val2, ...}`

**Use case** : Extraction champs depuis réponses API/LLM complexes

#### Exemple Mode Simple (backward compatible)
```json
{
  "name": "extract_score",
  "type": "transform",
  "handler": "extract_field",
  "inputs": {
    "data": "${cycle.validation_result}",
    "path": "score",
    "default": 0
  },
  "outputs": {"value": "cycle.validation_score"}
}
```

#### Exemple Mode Multi (optimisé) ⭐
```json
{
  "name": "extract_validation_fields",
  "type": "transform",
  "handler": "extract_field",
  "inputs": {
    "data": "${cycle.validation_result}",
    "paths": {
      "score": "score",
      "feedback": "feedback",
      "confidence": "confidence"
    },
    "default": null
  },
  "outputs": {
    "score": "cycle.validation_score",
    "feedback": "cycle.validation_feedback",
    "confidence": "cycle.validation_confidence"
  }
}
```

**Gains mode multi** : 
- ✅ **1 node** au lieu de N nodes
- ✅ Intent plus clair dans les logs
- ✅ Moins de clutter

**Quand utiliser multi** :
- ✅ Plusieurs champs depuis même objet
- ✅ Même `default` pour tous les champs
- ❌ Si defaults différents → garder mode simple × N

---

### `format_template`
**Description** : Formatage template string (Python .format() style)  
**Inputs** :
- `template` (string, required) — template avec {placeholders}
- `**kwargs` — paires clé-valeur pour substitution

**Outputs** :
- `text` (string) — texte formaté

**Use case** : Génération prompts, messages, logs structurés

**Exemple** :
```json
{
  "name": "format_log_message",
  "type": "transform",
  "handler": "format_template",
  "inputs": {
    "template": "VALIDATION [{timestamp}] Score: {score}/10 - {feedback}",
    "timestamp": "${cycle.meta.validation_time}",
    "score": "${cycle.validation.score}",
    "feedback": "${cycle.validation.feedback}"
  },
  "outputs": {"text": "cycle.log_message"}
}
```

---

### `idempotency_guard`
**Description** : Vérifie si action déjà effectuée (prévention duplicates)  
**Inputs** :
- `action_id` (string, required) — ID unique action
- `completed_actions` (list, default: []) — liste IDs complétés

**Outputs** :
- `skip` (bool) — true si action déjà faite
- `action_id` (string) — ID action

**Use case** : Prévenir déplacements emails dupliqués, envois notifs

**Exemple** :
```json
{
  "name": "check_already_moved",
  "type": "transform",
  "handler": "idempotency_guard",
  "inputs": {
    "action_id": "move_${cycle.msg.uid}",
    "completed_actions": "${cycle.completed_moves}"
  },
  "outputs": {"skip": "cycle.msg.skip_move"}
}
```

---

## 🔀 Decisions (Conditional Routing)

### `truthy`
**Description** : Route selon la véracité d'une valeur  
**Routes** : `"true"` | `"false"`  
**Falsy values** : null, false, 0, "", [], {}  
**Truthy values** : tout le reste

**Spec** :
```json
{
  "type": "decision",
  "decision": {
    "kind": "truthy",
    "input": "${cycle.items}"
  }
}
```

**Edges requis** :
```json
{"from": "check_items", "to": "process", "when": "true"},
{"from": "check_items", "to": "skip", "when": "false"}
```

**Use case** : Vérifier si liste non vide, flag boolean, valeur présente

---

### `enum_from_field`
**Description** : Route selon valeur string (classification, labels)  
**Routes** : labels custom (ex: "SPAM", "HAM", "UNSURE")  
**Options** :
- `normalize` : "upper" | "lower" | "trim"
- `fallback` : route par défaut si pas de match

**Spec** :
```json
{
  "type": "decision",
  "decision": {
    "kind": "enum_from_field",
    "input": "${cycle.classification}",
    "normalize": "upper",
    "fallback": "default"
  }
}
```

**Edges requis** :
```json
{"from": "classify", "to": "handle_spam", "when": "SPAM"},
{"from": "classify", "to": "handle_ham", "when": "HAM"},
{"from": "classify", "to": "handle_default", "when": "default"}
```

**Use case** : Routing classification LLM, gestion multi-catégories

---

### `compare`
**Description** : Comparaison numérique/string  
**Routes** : `"true"` | `"false"`  
**Operators** : `==`, `!=`, `>`, `>=`, `<`, `<=`

**Spec** :
```json
{
  "type": "decision",
  "decision": {
    "kind": "compare",
    "input": "${cycle.score}",
    "operator": ">=",
    "value": 7
  }
}
```

**Edges requis** :
```json
{"from": "check_quality", "to": "accept", "when": "true"},
{"from": "check_quality", "to": "retry", "when": "false"}
```

**Use case** : Validation scores, seuils, budgets

**Note** : Essaie numeric d'abord, fallback string si conversion fail

---

### `regex_match`
**Description** : Pattern matching regex  
**Routes** : `"match"` | `"no_match"`  
**Options** :
- `pattern` (string, required)
- `flags` (string, optional) : "i" (case-insensitive), "m" (multiline), "s" (dotall)

**Spec** :
```json
{
  "type": "decision",
  "decision": {
    "kind": "regex_match",
    "input": "${cycle.email_subject}",
    "pattern": "^RE:",
    "flags": "i"
  }
}
```

**Edges requis** :
```json
{"from": "check_reply", "to": "handle_reply", "when": "match"},
{"from": "check_reply", "to": "handle_new", "when": "no_match"}
```

**Use case** : Détection patterns emails, URLs, formats

---

### `in_list`
**Description** : Test d'appartenance à une liste  
**Routes** : `"true"` | `"false"`

**Spec** :
```json
{
  "type": "decision",
  "decision": {
    "kind": "in_list",
    "input": "${cycle.category}",
    "list": ["AI", "ML", "LLM", "GPT"]
  }
}
```

**Edges requis** :
```json
{"from": "check_category", "to": "process", "when": "true"},
{"from": "check_category", "to": "skip", "when": "false"}
```

**Use case** : Whitelist/blacklist, catégories autorisées

---

### `has_key`
**Description** : Vérifie présence d'une clé dans un objet  
**Routes** : `"true"` | `"false"`

**Spec** :
```json
{
  "type": "decision",
  "decision": {
    "kind": "has_key",
    "input": "${cycle.data}",
    "key": "score"
  }
}
```

**Edges requis** :
```json
{"from": "check_field", "to": "use_score", "when": "true"},
{"from": "check_field", "to": "calculate", "when": "false"}
```

**Use case** : Validation structure réponses API, champs optionnels

---

## 🧪 Mock Handlers (Testing)

### `mock_score_progressive`
**Description** : Simule scoring progressif pour tests retry loop  
**Inputs** : `attempt` (int)  
**Outputs** : `score` (float) — 4.0 → 5.5 → 7.0 → 8.0  
**Use case** : Tests validation qualité avec retry

---

## 📚 Exemples Complets

### Retry Loop avec Validation Qualité
```json
{
  "nodes": [
    {"name": "SCORING_LOOP", "type": "transform", "handler": "set_value", "inputs": {"value": "scoring"}, "outputs": {"result": "cycle.phase"}},
    {"name": "score_items", "type": "io", "handler": "http_tool", "inputs": {"tool": "call_llm", ...}, "outputs": {"content": "cycle.score_raw"}},
    {"name": "normalize_score", "type": "transform", "handler": "normalize_llm_output", "inputs": {"content": "${cycle.score_raw}"}, "outputs": {"parsed": "cycle.score_obj"}},
    {"name": "extract_fields", "type": "transform", "handler": "extract_field", "inputs": {"data": "${cycle.score_obj}", "paths": {"score": "score", "feedback": "feedback"}}, "outputs": {"score": "cycle.score", "feedback": "cycle.feedback"}},
    {"name": "check_quality", "type": "decision", "decision": {"kind": "compare", "input": "${cycle.score}", "operator": ">=", "value": 7}},
    {"name": "check_retry", "type": "decision", "decision": {"kind": "compare", "input": "${cycle.retry_count}", "operator": "<", "value": 3}},
    {"name": "increment", "type": "transform", "handler": "increment", "inputs": {"value": "${cycle.retry_count}"}, "outputs": {"result": "cycle.retry_count"}}
  ],
  "edges": [
    {"from": "SCORING_LOOP", "to": "score_items"},
    {"from": "score_items", "to": "normalize_score"},
    {"from": "normalize_score", "to": "extract_fields"},
    {"from": "extract_fields", "to": "check_quality"},
    {"from": "check_quality", "to": "success", "when": "true"},
    {"from": "check_quality", "to": "check_retry", "when": "false"},
    {"from": "check_retry", "to": "increment", "when": "true"},
    {"from": "check_retry", "to": "failure", "when": "false"},
    {"from": "increment", "to": "SCORING_LOOP"}
  ]
}
```

---

## 📊 Résumé des Transforms

| Handler | Type | Générique | Multi | Performance |
|---------|------|-----------|-------|-------------|
| `increment` | Math | ✅ | ❌ | <0.1ms |
| `decrement` | Math | ✅ | ❌ | <0.1ms |
| `add` | Math | ✅ | ❌ | <0.1ms |
| `multiply` | Math | ✅ | ❌ | <0.1ms |
| `set_value` | Data | ✅ | ❌ | <0.1ms |
| `sanitize_text` | Text | ✅ | ❌ | ~2ms |
| `normalize_llm_output` | LLM | ✅ | ❌ | ~1ms |
| `json_stringify` | Data | ✅ | ❌ | ~0.5ms |
| `extract_field` | Data | ✅ | ✅ | ~0.5ms |
| `format_template` | Text | ✅ | ❌ | ~0.2ms |
| `idempotency_guard` | Logic | ✅ | ❌ | <0.1ms |

---

## 🎯 Bonnes Pratiques

### ✅ Préférer
- Transforms génériques composables
- Mode multi pour extractions multiples depuis même objet
- Intent clair par node (nom descriptif)
- Réutilisabilité maximale

### ❌ Éviter
- Handlers spécifiques à un use case
- "God handlers" qui font trop de choses
- Optimisations prématurées sur gains < 5ms
- Duplication de logic (créer transform réutilisable)

---

## 🔗 Références

- **Orchestrator README** : `src/tools/_orchestrator/README.md`
- **Process Schema** : Membank `orchestrator_process_schema.md`
- **Decisions** : Membank `orchestrator_decisions.md`
- **Handlers** : Membank `orchestrator_handlers.md`
- **Code Source** : `src/tools/_orchestrator/handlers/transforms*.py`
