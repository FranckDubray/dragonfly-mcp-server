# Changelog

## [1.28.0] - 2025-10-18

### 🚀 Orchestrator v1.1 — Features Avancées (CRITIQUE + IMPORTANT)

**Orchestrator générique JSON-driven FSM pour workflows long-running, avec features avancées de production.**

#### ✨ Nouvelles Features CRITIQUES

##### 🔴 **Scopes Lifecycle** (Déclaratif)
- **Scopes persistants** : `reset_on: []` pour variables qui survivent aux back-edges
- **Seed automatique** : initialisation déclarative au START via `seed: {retry_count: 0}`
- **Déclaratif vs Impératif** : plus besoin de nodes `init_*`, tout dans le JSON
- Application automatique par l'engine au START node
- Support namespace utilisateur (`_meta`, `dates`, `sources`, etc.)

##### 🔥 **Retry Loop avec Validation Qualité**
- Pattern complet : fetch → score → validate → retry si < seuil
- Decision `compare` pour validation numérique (score >= 7)
- Transform `increment` pour compteurs de retry
- Guard 100 nodes/cycle (sécurité boucles infinies)
- Exemple production : AI Curation avec validation Perplexity Sonar

#### ✨ Nouvelles Features IMPORTANTES

##### 🟡 **Hot-Reload** (Runtime)
- Check `process_uid` (hash SHA256) avant chaque cycle
- Reload automatique du process JSON si changé
- Update engine, worker_ctx, graph à chaud
- Flag `hot_reload: true` (default)
- Zero downtime pour updates de graph

##### 🟡 **Decision Kinds Étendus**
- `compare` : opérateurs `>=`, `<=`, `==`, `!=`, `>`, `<` (numeric + string fallback)
- `regex_match` : pattern matching avec flags (i, m, s)
- `in_list` : membership test (valeur in array)
- `has_key` : check présence clé dans object
- Total : 6 decision kinds (truthy, enum_from_field, compare, regex_match, in_list, has_key)

##### 🟡 **Transforms Arithmétiques**
- `increment` : value → value + 1 (compteurs)
- `decrement` : value → value - 1
- `add` : value + amount (addition paramétrée)
- `multiply` : value × factor (multiplication)
- `set_value` : affectation constante
- Tous retournent int si pas de décimale

##### 🟡 **Transforms Domain** (Réutilisables)
- `sanitize_text` : nettoyage HTML, whitespace, truncate (max_length)
- `normalize_llm_output` : parse JSON LLM, extraction markdown code blocks, fallback
- `extract_field` : JSONPath-like extraction (dotted path)
- `format_template` : string templating (style Python format)
- `idempotency_guard` : prévention actions dupliquées (skip si déjà fait)

#### 📦 Fichiers Ajoutés/Modifiés

**Handlers** :
- `src/tools/_orchestrator/handlers/transforms.py` (3.2 KB) — arithmétique ✨ NEW
- `src/tools/_orchestrator/handlers/transforms_domain.py` (5.8 KB) — domain-specific ✨ NEW
- `src/tools/_orchestrator/handlers/mock_score.py` (1.2 KB) — test helper ✨ NEW
- `src/tools/_orchestrator/handlers/__init__.py` — registry updated (2.2 KB)

**Engine** :
- `src/tools/_orchestrator/engine/orchestrator.py` — scopes + guard 100 nodes (11.9 KB) ✅ UPDATED
- `src/tools/_orchestrator/engine/decisions.py` — 4 nouveaux kinds (6.9 KB) ✅ UPDATED

**Runner** :
- `src/tools/_orchestrator/runner.py` — hot-reload check (9.6 KB) ✅ UPDATED

**Process Examples** :
- `workers/test_retry_loop.process.json` (4.5 KB) — test complet retry loop ✨ NEW
- `workers/ai_curation_production.process.json` (9.8 KB) — curation AI production ✨ NEW
- `workers/ai_curation_sonar.process.json` (15.2 KB) — avec Perplexity Sonar validation ✨ NEW
- `workers/ai_curation_sonar_logged.process.json` (15.8 KB) — avec logging feedback ✨ NEW

**Tests** :
- `tests/orchestrator_retry_loop_test.py` (3.8 KB) — validation retry loop ✨ NEW

#### 🧪 Tests Validés (Production)

##### ✅ **Test Retry Loop**
- **Scénario** : Mock scoring progressif (4.0 → 5.5 → 7.0)
- **Résultat** : 3 iterations, 2 increments, success à tentative 3
- **Nodes** : 16 traversés (bien < 100)
- **Timing** : ~200ms

##### ✅ **AI Curation Production**
- **Sources** : News (NYT/Guardian) + Reddit + arXiv
- **LLM** : GPT-4o-mini scoring + formatting
- **Validation** : Score >= 7 (1er coup : 8.5/10)
- **Timing** : 20 secondes
- **DB** : Sauvegarde propre dans `ai_curation_reports.db`

##### ✅ **AI Curation avec Sonar**
- **Dual scoring** : GPT-4o-mini + Perplexity Sonar top 10
- **Validation Sonar** : Score qualité 1-10 avec feedback textuel
- **Retry loop** : Jusqu'à 3 tentatives si score < 7
- **Timing** : 70 secondes (4 appels LLM)
- **Production-ready** : Logging complet, retry fonctionnel

#### 📊 Métriques & Performance

**Scopes** :
- Initialisation : ~2ms au START
- Overhead par scope : négligeable (<1ms)
- Scope persistent : 0 reset entre back-edges ✅

**Hot-Reload** :
- Check process_uid : ~5ms par cycle
- Reload complet : ~50ms (lecture + parse JSON + update engine)
- Zero downtime ✅

**Decisions** :
- compare (numeric) : ~0.1ms
- regex_match : ~0.5ms (dépend du pattern)
- in_list : O(n), ~0.1ms pour listes <100 items

**Transforms** :
- Arithmétiques : <0.1ms (pure Python)
- Domain (sanitize_text) : ~2ms pour 10KB texte
- normalize_llm_output : ~1ms (JSON parse)

**Guard 100 nodes** :
- Overhead : ~0.01ms par node (simple counter)
- Déclenché : jamais en production (graphs bien conçus)

#### 🎯 Use Cases Production

##### **Retry Loop Générique**
```
START → init (retry=0) → fetch → validate (score >= 7?)
  [score >= 7] → success → EXIT
  [score < 7] → retry_check (retry < 3?)
    [retry < 3] → increment → BACK TO fetch
    [retry >= 3] → failure → EXIT
```

##### **AI Curation Multi-Source**
- Aggregation : News + Reddit + arXiv + Papers With Code
- Scoring dual : GPT-4o-mini + Perplexity Sonar
- Validation : Sonar score >= 7 avec retry
- Output : Markdown report + SQLite persistence

#### 🔧 Breaking Changes

**Scopes location** :
- ❌ **Avant** : `"scopes": [...]` au niveau top (root)
- ✅ **Après** : `"graph": {"nodes": [...], "edges": [...], "scopes": [...]}`
- Migration : déplacer scopes dans graph

**Context resolution** :
- Variables numériques : utiliser valeur directe, pas `"${...}"` pour literals
- Exemple : `"value": 7` (pas `"value": "${worker.threshold}"` si literal)

#### 📚 Documentation

**Membank updated** :
- `orchestrator_process_schema.md` — scopes dans graph
- `orchestrator_contexts.md` — scopes lifecycle
- `orchestrator_decisions.md` — 4 nouveaux kinds
- `orchestrator_implementation.md` — status v1.1

**README updated** :
- `src/tools/_orchestrator/README.md` — exemples retry loop, scopes, transforms

#### 🎓 Exemples Clés

**Scopes déclaratifs** :
```json
"graph": {
  "scopes": [
    {"name": "_meta", "reset_on": [], "seed": {"retry_count": 0}},
    {"name": "data", "reset_on": ["START"], "seed": {}}
  ]
}
```

**Decision compare** :
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

**Transform increment** :
```json
{
  "type": "transform",
  "handler": "increment",
  "inputs": {"value": "${cycle.retry_count}"},
  "outputs": {"result": "cycle.retry_count"}
}
```

---

### 🚀 Orchestrator v1.0 — Production-Ready (précédent)

**Generic JSON-driven FSM orchestrator for long-running workflows.**

#### ✨ Core Features
- [x] Graph execution (START → nodes → edges → END/EXIT)
- [x] Node types: start, end, exit, io, transform, decision
- [x] Context resolution recursive (${worker.*}, ${cycle.*})
- [x] Handlers registry (extensible)
- [x] Retry policies (expo backoff, node-level)
- [x] Decisions: truthy, enum_from_field
- [x] Transforms: sleep
- [x] Logging (job_steps, UTC microseconds)
- [x] Detached runner (spawn, signals SIGTERM/INT/SIGBREAK)
- [x] Cooperative cancel (check every 0.5s)
- [x] Tool controller (start/stop/status API)
- [x] Chroot security (workers/ strict)
- [x] Conflict detection (TTL heartbeat)

#### Handlers
- [x] http_tool (generic MCP client)
- [x] sleep (cooperative)

#### Error Handling
- [x] 3-level retry (transport, HTTP, node)
- [x] HandlerError normalized
- [x] RetryExhaustedError

---

## [1.27.5] - 2025-10-15

### 🧩 Nouveaux tools
- Lichess (Public API, read‑only): profils, perfs, équipes, parties, tournois, leaderboards, puzzles (sans authentification).
- Stockfish (Auto‑75): évaluation de position et analyse de partie avec auto‑configuration (~75% des ressources), MultiPV, budget‑temps global (LLM 1 min par sonde typique).

### 📦 Divers
- Catalog/tools: specs chargées dans le registre (JSON canoniques disponibles sous src/tool_specs/).
- Docs: README racine mis à jour.

---

## [1.27.4] - 2025-10-15

### 🛠 Workers Realtime — Correctifs UI/UX & Mermaid (compléments)
- Time Machine:
  - Contrôles "magnétophone" (⏮ ⏪ ▶︎/⏸ ⏩ ⏭) pour rejouer pas‑à‑pas ou en auto.
  - Surlignage synchronisé: clic nœud Mermaid → sélection/scroll de l'étape dans la timeline; nœud courant surligné.
  - Timeline chargée jusqu'à 200 événements, ~15 lignes visibles (scroll dédié), horodatage FR (date+heure).
  - Alerte claire si incohérence logs ↔ schéma (nœuds inconnus) avec détails (id + date/heure), échantillons limités.
  - Cache du code Mermaid pendant le replay (perf): plus de requêtes DB par step.
- Galerie/Lightbox:
  - Galerie fermée par défaut; ouverture/fermeture via l'icône seulement.
  - Scroll horizontal accéléré dans la galerie; lightbox uniquement pour vignettes/data‑full (jamais l'avatar).
- VU Ring:
  - Anneau vert/jaune/rouge plus visible, lissage EMA + boost non linéaire, compat APIs legacy.
- CSS/Thème:
  - Thème clair confirmé; avatar 64×64 rond, recadrage; timeline ~15 lignes visibles.
- Prompt système / Contexte:
  - DB complétée (timezone, working_hours, bio) puis nettoyage (email/tags retirés) conformément aux demandes.

### 🔔 Sonnerie & Audio
- Sonnerie "Skype-like" par défaut (≈400/450 Hz), cadence tu‑tu‑tuu tu‑tu‑tu, agréable et familière pour 2–10 s.
- Volume par défaut 50% et curseur unique pilotant à la fois la sonnerie et la voix IA (setVolume partagé).
- Préchargement de Mermaid au chargement de page (/workers) pour supprimer la latence (fallback + retry garantis côté JS si CDN lent).

### 🧠 VAD & Interruption IA
- Détection rapide: dès que l'utilisateur parle, arrêt immédiat du haut-parleur IA et cancel de la réponse courante.
- Reprise rapide au silence stable; option d'accentuation (<200ms) possible.

### 📊 KPIs Process (overlay)
- Nouveau panneau "Activité (dernière heure)" dans l'overlay Process: 
  - Tâches (succeeded/failed), Appels call_llm, Cycles (sleep_interval ou fallback finish_mailbox_db)
  - Recalcul à chaque refresh (10 s) pendant l'overlay.

### 🎨 Couleur cartes selon activité (1h)
- 0–15 → vert, 16–40 → orange, >40 → rouge (classes activity-*)

### 🐛 Corrections Mermaid
- Chargeur Mermaid robuste (retry) + fallback "Diagramme indisponible" avec message explicite.
- Normalisation du source Mermaid (quotes, backslashes) + surlignage du nœud courant.

### 🗄 Données & Seeds de test
- Injection de cycles cohérents (nomail + mail occasionnels), durées réalistes: sleep 10 min, LLM 1 min, enchaînement strict des nœuds.
- Lot par ~50 lignes, répété pour couvrir une plage temporelle jusqu'à atteindre des tests denses.

---
