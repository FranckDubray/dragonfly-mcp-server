# Python Orchestrator — Guide ultra‑concis pour LLM (worker parfait)

Objectif
- Écrire des workers Python lisibles, traçables et robustes, sans code d’infrastructure.
- L’orchestrateur gère: validation AST, logs riches, erreurs, graphe Mermaid, debug step‑by‑step, audit DB.

Sommaire
- 0) Pré‑tests tools (obligatoire)
- 1) Structure minimale (DSL)
- 2) Règles absolues (AST)
- 3) I/O et transforms utiles
- 4) Graphe Mermaid (rendu propre)
- 5) Debug & Observabilité (TOP pour LLM)
- 6) Patterns et pièges courants (fixes concrets)
- 7) Checklist avant run

---

## 0) Pré‑tests tools (obligatoire)
Avant d’écrire le process, valider les tools appelés (en vrai):
- Appelle chaque tool avec des paramètres réels (petits volumes, `limit` raisonnable).
- Note la forme exacte des sorties (chemins JSON stables), des erreurs et contraintes (formats de date, types, etc.).
- Exemple: Guardian via `news_aggregator` exige `from_date`/`to_date` au format `YYYY-MM-DD` (pas d’heure!).
- Utilise ces I/O confirmées pour choisir les transforms (ou en créer si besoin).

Découvrir les transforms disponibles (via le tool orchestrator)
- Le tool `py_orchestrator` expose l’opération `transforms` qui liste les transforms disponibles avec leur contrat I/O (parfait pour un LLM):
```json
{
  "tool": "py_orchestrator",
  "params": { "operation": "transforms", "limit": 100 }
}
```
Réponse (extrait):
```json
{
  "accepted": true,
  "status": "ok",
  "total": 18,
  "returned": 18,
  "transforms": [
    {
      "kind": "array_ops",
      "io_type": "list->list",
      "description": "Parametric list operations (filter, map, ...)",
      "inputs": ["- op: string ...", "- items: list[any]", ...],
      "outputs": ["- items: list[any]"]
    },
    { "kind": "json_ops", ... },
    { "kind": "coerce_number", ... },
    { "kind": "normalize_llm_output", ... }
  ]
}
```
- Un LLM peut s’auto‑documenter en lisant `io_type`, `description`, `inputs`, `outputs` pour choisir la bonne transform.

Tester les tools dans le contexte MCP (exemples prêts à l’emploi)
- Toujours fixer un `limit` raisonnable et vérifier les erreurs.
- `date.now` (garantir une string utilisable):
```json
{"tool":"date","params":{"operation":"now","format":"%Y-%m-%dT%H:%M:%S","tz":"UTC"}}
```
- `news_aggregator.search_news` (Guardian attend `YYYY-MM-DD`):
```json
{
  "tool":"news_aggregator",
  "params":{
    "operation":"search_news",
    "providers":["guardian"],
    "query":"AI OR LLM",
    "from_date":"2025-10-23",
    "to_date":"2025-10-26",
    "limit":10
  }
}
```
- `reddit_intelligence.multi_search`:
```json
{
  "tool":"reddit_intelligence",
  "params":{
    "operation":"multi_search",
    "subreddits":["MachineLearning","LocalLLaMA"],
    "query":"AI OR LLM",
    "limit_per_sub":5,
    "time_filter":"week"
  }
}
```
- `academic_research_super.search_papers`:
```json
{
  "tool":"academic_research_super",
  "params":{
    "operation":"search_papers",
    "sources":["arxiv"],
    "query":"large language model",
    "include_abstracts":false,
    "max_results":10
  }
}
```

Tips rapides
- `py_orchestrator.transforms` → liste les transforms (contrats I/O).
- Tool `date`: si tu veux une string sûre → donne un `format` explicite (ex: `%Y-%m-%dT%H:%M:%S`).

---

## 1) Structure minimale (DSL)
- process.py:
  ```python
  from py_orch import Process, SubGraphRef
  PROCESS = Process(
    name="...", entry="INIT",
    parts=[SubGraphRef("INIT", module="subgraphs.init", next={"success":"COLLECT"}), ...],
    metadata={"db_file":"worker_...db", "llm_model":"...", ...}
  )
  ```
- subgraphs/*:
  ```python
  from py_orch import SubGraph, step, cond, Next, Exit
  SUBGRAPH = SubGraph(name="...", entry="STEP_A", exits={"success":"...", "fail":"..."})
  @step
def STEP_A(worker, cycle, env):
      out = env.tool("date", operation="now", format="%Y-%m-%dT%H:%M:%S", tz="UTC")
      cycle.setdefault("dates",{})["now"] = out.get("result")
      return Next("STEP_B")
  @cond
def STEP_OK(worker, cycle, env):
      return Exit("success") if cycle.get("ok") else Exit("fail")
  ```

---

## 2) Règles absolues (AST)
- 1 appel par step: exactement un `env.tool(...)` OU un `env.transform(...)`.
- 0 appel dans un cond: `@cond` décide et retourne `Exit('label')` ou `Next('STEP')`.
- Interdits dans steps/conds: `import`, `for`, `while`, `with`, `try`, `open/eval/exec/__import__`.
- Transitions obligatoires: chaque fonction retourne `Next(...)` ou `Exit(...)`.
- Lisibilité: ≤ 20 steps par sous‑graphe (sinon scinder).

---

## 3) I/O et transforms utiles
- Listes → `array_ops` (filter/map/sort_by/unique_by/take/skip), `array_concat` (fusion)
- Objets → `json_ops` (get/set/merge/rename/remove), `json_stringify` (to string)
- Numérique → `coerce_number` (tolérant, %), `arithmetic`
- Texte → `sanitize_text`, `normalize_llm_output` (parser JSON LLM robuste)
- Date → `date_ops` (format/add/diff) ou tool `date` (with format)
- Utilitaires → `set_value` (setter scalaire), `sleep` (coop)

Bonnes pratiques I/O
- Tolerant extraction: si une step lit un résultat tool, gère `result|content|iso|datetime` et objets imbriqués.
- Provider‑specific: adapte le format (ex: Guardian `YYYY-MM-DD`).

---

## 4) Graphe Mermaid (rendu propre)
- Obtenir le graphe processus:
  ```json
  {
    "tool":"py_orchestrator",
    "params":{ "operation":"graph", "worker_name":"<name>",
      "graph":{ "kind":"process", "include":{"shapes":true,"emojis":true,"labels":true},
                 "render":{ "mermaid":true } }
    }
  }
  ```
- Convention de rendu:
  - Transforms: engrenage ⚙️ (toujours), rectangle bleu.
  - Tools: emoji selon catégorie (📊 intelligence, 🗄️ data, 📄 documents, 🎮 entertainment, 🔢 utilities, …), rectangle vert.
  - Conditionnelles: diamant `{Label}`; flèches sortantes labellisées (`success`, `fail`, `retry`, …).
  - START/END: stylés en vert (fond #d9fdd3, bord #2e7d32).
  - IDs d’arêtes qualifiés `SG::STEP` (pas de doublon “liste sans flèches”).

---

## 5) Debug & Observabilité (TOP pour LLM)
Démarrer en debug (pause immédiate)
```json
{"tool":"py_orchestrator","params":{
  "operation":"start","worker_name":"<name>","worker_file":"workers/<name>/process.py",
  "hot_reload":true,
  "debug":{"enable_on_start":true,"pause_at_start":true,"action":"enable_now"}
}}
```
Pilotage
- `debug.step`, `debug.continue`, `debug.run_until` (avec `timeout_sec`).
- `status` retourne la position courante, la timeline et le snapshot debug.

Logs riches (fail & success)
- En cas d’erreur step: l’orchestrateur persiste automatiquement:
  - KV: `py.last_call`, `py.last_result_preview`
  - DB: `job_steps.details_json` = `{ error, call, last_result_preview }`
- En succès (debug activé): mêmes aperçus persistés.
- Audit de run: table `run_audit` (run_id, durée, last_error, last_node, last_call_json, last_result_preview…)

---

## 6) Patterns et pièges courants (fixes concrets)
- Dates Guardian: passer `YYYY-MM-DD`. Ex: dériver `from_ymd/to_ymd` via `date_ops` ou `[:10]` si déjà en ISO.
- `date.now`: garantir une string → passer `format="%Y-%m-%dT%H:%M:%S"` (et `tz="UTC"` si souhaité).
- Normalisation LLM: `normalize_llm_output` pour tolérer les JSON encodés, balisés, ou semi‑valides.
- Dédoublonnage: `array_ops` (`unique_by`), ou `dedupe_by_url` si besoin spécifique.
- “1 call/step”: si tu as extraction+traitement, scinde en deux steps.

---

## 7) Checklist avant run
- [ ] 1 appel par step / 0 appel dans les conds.
- [ ] Règles AST respectées (pas de `import/for/while/with/try`, etc.).
- [ ] Formats provider‑specific gérés (ex: dates `YYYY-MM-DD`).
- [ ] Transforms & tools testés (petits volumes, `limit`).
- [ ] `validate` OK (≤ 20 steps/sous‑graphe):
  ```json
  {"tool":"py_orchestrator","params":{"operation":"validate","worker_name":"<name>"}}
  ```
- [ ] Graphe Mermaid propre (diamants, labels, emojis, START/END verts): `operation=graph` + `render.mermaid=true`.
- [ ] Debug prêt: démarrage avec pause, `debug.step` OK.
- [ ] Observabilité: en cas d’échec, vérifier `py.last_call`, `py.last_result_preview`, `job_steps.details_json`.

Résumé
- Teste d’abord les tools (formats exacts).
- Code des steps atomiques, tolérants côté parsing.
- Utilise les transforms pour mapper/filtrer/nettoyer.
- Appuie‑toi sur le graphe Mermaid (propre) et sur les logs enrichis du runner.
- Le LLM peut diagnostiquer tout seul: chaque erreur expose l’appel et un aperçu du résultat.
