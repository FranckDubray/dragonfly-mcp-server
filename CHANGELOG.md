# Changelog

## [1.50.0] - 2025-01-19

### 🎨 Orchestrator v6.2 — Architecture hiérarchique SSOT + Visualisation récursive

#### 🏗️ Architecture modulaire (SSOT strict)
- ✅ **5 subgraphs autonomes** (INIT → COLLECT → SCORE → VALIDATE → OUTPUT)
- ✅ **Pas de duplication** : chaque node/edge défini UNE SEULE FOIS
- ✅ **Tous fichiers < 7KB** (max: 4.8KB = 02_collect.subgraph.json)
- ✅ **Navigation hiérarchique** : vue macro → clic boîte → drill-down détail → récursif infini

#### 📦 Structure ai_curation worker
```
workers/ai_curation/
├── main.process.json         (1.8KB)  # Orchestration pure (subgraphs refs + edges inter-SG)
├── config/                           # worker_ctx + scopes
├── prompts/                          # Data lourdes (GPT/Sonar prompts)
├── subgraphs/                        # 5 phases autonomes (SSOT)
│   ├── 01_init.subgraph.json
│   ├── 02_collect.subgraph.json     # Fetch 5 sources + filter ≤72h
│   ├── 03_score.subgraph.json       # GPT-4o-mini top 10
│   ├── 04_validate.subgraph.json    # Sonar validation loop
│   └── 05_output.subgraph.json      # Format FR + save DB
└── visualization/                    # Mermaid avec emojis bien choisis
    ├── main_global.mmd              # Vue macro (5 boîtes)
    ├── subgraph_COLLECT.mmd         # Détail COLLECT
    └── subgraph_VALIDATE.mmd        # Détail VALIDATE
```

#### 🎨 Visualisation avec emojis contextuels
- **Vue globale** : 🚀 START → 🔧 INIT → 📦 COLLECT → 🎯 SCORE → ✅ VALIDATE → 💾 OUTPUT → 🏁 EXIT
- **Détail COLLECT** : 🌐 News, 💬 Reddit, 📄 arXiv, 🏆 PWC, 🔍 Sonar, ⏱️ Filters, 📊 Count
- **Détail VALIDATE** : 🤖 LLM, ⚖️ Decisions, 🗄️ DB logs, 🔄 Retry loop, ➕ Increment
- **Légende couleurs** : Bleu (init), Vert (collect), Orange (score), Violet (validate), Gris (output)

#### 🔧 Corrections P0/P1 (audit complet)
1. **Transforms normalisés** → Tous lèvent `HandlerError` (pas `ValueError`)
   - increment, decrement, add, multiply, set_value, json_stringify
   - normalize_llm_output, extract_field, format_template, filter_by_date
2. **Prompts Sonar** → User-only (pas de system prompt)
3. **JSON stringify** → Avant INSERT SQLite (fix v5.5.2)
4. **Scopes lifecycle** → Reset END + enter/leave triggers (complet)
5. **Retry logging** → log_retry_attempt() en DB
6. **Crash logs** → Table crash_logs avec worker_ctx + cycle_ctx + stack_trace complet

#### 🎯 Viewer récursif (design validé)
- Frontend appelle `GET /orchestrator/status?worker=ai_curation`
- Identifie subgraph du `current_node`
- Charge subgraph JSON → affiche vue détail
- Highlight boîte macro + node détail
- Trail animé (CSS classes `running`/`visited`/`active` sur SVG)
- Récursion infinie (si node = subgraph → drill-down niveau N+1)

#### 🗑️ Nettoyage code mort
- ❌ Supprimé `workers/ai_curation/nodes/` (dupliqué dans subgraphs)
- ❌ Supprimé `workers/ai_curation/edges/` (edges intra-SG dans subgraphs)
- ❌ Supprimé 20 anciens process JSON monolithiques (15-23KB chacun)

#### 📊 Métriques
- **Avant** : 1 fichier monolithe 23KB
- **Après** : 15 fichiers modulaires, max 4.8KB
- **Couverture specs** : 16/18 features (89%)
- **Total worker** : ~30KB (config + prompts + subgraphs + viz)

---

## [1.40.0] - 2025-01-19

### 🎯 Orchestrator v1.4 — Audit complet + Fixes P0/P1 (couverture 56% → 90%)

#### 🔴 P0 Critiques (TERMINÉS)
- ✅ **v1.3.1** : Fix api.py `_validate_process_logic(process_data)` variable name
- ✅ **v1.3.2** : Crash logging avec contextes complets (table crash_logs)
- ✅ **v1.4.0** : Scopes lifecycle complet (reset END, enter/leave triggers)
- ✅ **v1.4.1** : Traceback Python enrichi (frame-by-frame + locals vars)

#### 🟡 P1 Features manquantes (TERMINÉS)
- ✅ **v1.4.2** : Retry logging (log_retry_attempt en DB)
- ✅ **v1.4.3** : Transforms errors normalisés (HandlerError partout)

#### 📊 Couverture specs membank
- **Avant** : 10/18 features (56%)
- **Après** : 16/18 features (89%)

#### 🚀 Nouvelles features production
1. **Crash logs complets**
   - Table crash_logs avec worker_ctx + cycle_ctx + stack_trace
   - Traceback Python frame-by-frame avec variables locales
   - print_crash_report() pour debug rapide

2. **Scopes lifecycle complet**
   - reset_on: ["END"] fonctionnel
   - reset_on: ["node_name"] fonctionnel
   - scope_trigger: {action: "enter|leave", scope: "name"} sur edges

3. **Retry logging**
   - log_retry_attempt() log chaque tentative
   - Query: `SELECT * FROM job_steps WHERE node LIKE '%_retry_%'`

4. **Transforms robustes**
   - Tous les transforms lèvent HandlerError
   - Retry policy s'applique correctement

---

## [1.31.0] - 2025-10-19

### 🛡️ Orchestrator v1.3 — Validation Schema + Error Messages

- ✅ **P1: JSON Schema Validation**
  - Création `schemas/process.schema.json` (complet, 6 decision kinds, retry limits)
  - api.py : validation automatique au start avec jsonschema (optional dependency)
  - Détection erreurs : worker_ctx type, handler manquant, edges invalides, duplicate nodes/edges
  - Messages clairs : path + schema_path pour localiser erreurs
  - Custom validation : START unique, edges vers nodes existants, no duplicate signatures

- 📝 **P2: Process Loader Error Messages**
  - Messages enrichis : chemins candidats affichés (base_dir + nodes/)
  - Erreurs JSON : ligne + colonne + conseil syntaxe
  - Circular imports : affiche chaîne complète
  - File not found : liste tous les chemins testés + tips organisation

---

## [1.30.0] - 2025-10-19

### 🔧 Orchestrator v1.2 — Audit & Cleanup

- 🔴 **FIX CRITIQUE**: api.py utilise maintenant `load_process_with_imports` (support $import au démarrage)
- 🗑️ **Cleanup**: Suppression handlers/transforms.py (dupliqué, handlers splittés dans transforms/*.py)
- 🧹 **Refactor**: handlers/__init__.py charge dynamiquement depuis transforms/ et transforms_domain/
- ✅ **Validation**: Process loader avec $import fonctionnel en API start + runner hot-reload

---

## [1.29.0] - 2025-10-19

### 🚀 Orchestrator v1.2 — Robustesse & Curation AI (72h) 

- 🧰 Runner (prod): redirection stdout/stderr → `logs/worker_<name>.log` (aucune synchro Git)
- 🧱 Résilience: process loader avec $import sous `nodes/` (anti-cycles, erreurs courtes)
- 🧩 Transforms (pur, 1 fichier = 1 transform): refactor + nouveaux
- 🧭 Process `ai_curation` (v6.0.5):
  - Dates centralisées
  - Filtre fraîcheur multi-source (<72h)
  - Fusion/dédoublonnage du rapport
- 🧹 .gitignore élargi (logs/, docs/, sqlite3/, *.db)

## [1.50.1] - 2025-10-20

### 🚑 Orchestrator v6.2.1 — Hotfix debug + stabilité

- ✅ FIX: process_loader._resolve_imports — mauvais nom de paramètre (Any → data) causant NameError
- ✅ FIX: Runner debug handshake — écrit maintenant debug.response_id lors du pause, évite les "in_progress" vides
- ✅ FEAT: Engine live fields — écrit current_node et debug.executing_node au begin_step (effacé au finally)
- ✅ FIX: VALIDATE template — remplace ${score}|${retry_count}|${feedback} par {{score}}|{{retry_count}}|{{feedback}} pour éviter la double-résolution
- 🧩 LOGS: step summaries plus lisibles (durations, attempts); ctx diff dispo via debug (redaction/truncation)
- 📝 NOTE: En mode step-by-step, cycle_id s’incrémente (effet de bord connu). À investiguer pour une future version (pause intra-cycle sans ++).

#### Impact
- Debug pas-à-pas exploitable (paused_at/next_node/cycle_id stables, step + ctx_diff visibles)
- Disparition de l’erreur "Invalid path … score" après 1 cycle OK (ancien last_error conservé jusqu’à succès)

#### Upgrade notes
- Aucun breaking change
- Redémarrer le worker pour prendre en compte les templates corrigés

## [1.50.2] - 2025-10-20

### ♻️ Orchestrator Runner — Refactor + Debug-first + I/O Preview (10KB)

- ✂️ Split runner into small modules (<7KB each):
  - runner.py (entrypoint thin)
  - runner_main.py (signals + bootstrap)
  - runner_loop.py (execution loop + debug integration)
  - runner_helpers.py (state/debug/process helpers)
  - debug_loop.py (pause/wait loop)
- 🧭 Debug invariance:
  - Pause immédiate possible au START: start(..., debug={"enable_on_start": true})
  - Reprise dans le même cycle_id (pas de retour à START ni reset inattendu)
  - Fallback in-progress: executing_node = next_node
- 🔎 I/O instrumentation (debug only):
  - step.summary.debug_preview:
    - inputs: {tool, model, temperature}
    - messages: prompt résolu (aperçu 10KB, PII masquée)
    - output: début de réponse tool (aperçu 10KB)
- 🧹 Suppression SLEEP_end (scorie historique). END reboucle vers START dans l’engine; EXIT termine.
- 🧱 Sans breaking change pour les process JSON existants.

#### Notes
- En mode in_progress, previous_node peut rester vide tant que la pause n’est pas encore atteinte. Dès ready, paused_at/next_node/step/ctx_diff sont complets.
- Recommandé: utiliser enable_on_start pour un debug step-by-step déterministe dès le début du cycle.
