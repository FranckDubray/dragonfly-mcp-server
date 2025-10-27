# Python Orchestrator — Guide LLM pour développer des workers (à jour)

Objectif
- Écrire des workers Python lisibles, traçables et robustes, sans code d’infrastructure.
- L’orchestrateur gère: validation AST, logs riches, erreurs, graphe Mermaid, debug step‑by‑step, audit DB, hot‑reload, config dossier.

Sommaire
- 0) Pré‑tests Tools (obligatoire)
- 1) DSL minimale (Process/SubGraphs/Steps)
- 2) Règles ABSOLUES (AST) + erreurs fréquentes (E2xx/E24x)
- 3) Cookbook “sans if en step” (patterns tolérants)
- 4) Transforms & Tools utiles (sur étagère)
- 5) Graphe & Mermaid (process/subgraph/overview)
- 6) Debug/Observe & Observabilité
- 7) Config worker (config/)
- 8) Validation & Checklist

---

## 0) Pré‑tests Tools (obligatoire)
Avant d’écrire le process, appelle réellement chaque tool avec de petits volumes pour connaître:
- les entrées/erreurs exactes, les sorties stables (chemins JSON), :
- formats attendus (dates, identifiants…), limites (`limit`, `max_results`).

Lister les transforms disponibles (auto‑doc I/O)
```json
{"tool":"py_orchestrator","params":{"operation":"transforms","limit":100}}
```
Chaque transform expose: kind, io_type, description, inputs, outputs.

Exemples d’appels de tools
```json
{ "tool":"date", "params": {"operation":"now","format":"%Y-%m-%dT%H:%M:%S","tz":"UTC"} }
{ "tool":"news_aggregator", "params": {"operation":"search_news","providers":["guardian"],"query":"AI","from_date":"2025-10-23","to_date":"2025-10-26","limit":10} }
{ "tool":"reddit_intelligence", "params": {"operation":"multi_search","subreddits":["MachineLearning"],"query":"LLM","limit_per_sub":5,"time_filter":"week"} }
{ "tool":"academic_research_super", "params": {"operation":"search_papers","sources":["arxiv"],"query":"large language model","include_abstracts":false,"max_results":10} }
```

---

## 1) DSL minimale (Process/SubGraphs/Steps)
- process.py:
```python
from py_orch import Process, SubGraphRef
PROCESS = Process(
  name="...", entry="INIT",
  parts=[SubGraphRef("INIT", module="subgraphs.init", next={"success":"COLLECT"}), ...],
  metadata={"db_file":"worker_x.db","llm_model":"..."}
)
```
- subgraphs/*:
```python
from py_orch import SubGraph, step, cond, Next, Exit
SUBGRAPH = SubGraph(name="...", entry="STEP_A", exits={"success":"...","fail":"..."})
@step
def STEP_A(worker, cycle, env):
    out = env.tool("date", operation="now", format="%Y-%m-%dT%H:%M:%S", tz="UTC")
    cycle.setdefault("dates",{})["now"] = out.get("result")
    return Next("STEP_B")
@cond
def DECIDE(worker, cycle, env):
    return Exit("success") if cycle.get("ok") else Exit("fail")
```

---

## 2) Règles ABSOLUES (AST) + erreurs fréquentes
- Dans un @step:
  - EXACTEMENT 1 appel à env.tool OU env.transform (E230 si ≠ 1).
  - AUCUN conditionnel (pas de if/elif/else, ni ternaire) (E204).
  - Retour OBLIGATOIRE: Next("...") ou Exit("...") (E240 si absent).
- Dans un @cond:
  - 0 appel à env.tool/env.transform (E231 si >0).
  - Libre de brancher (Next/Exit). Toujours retourner explicitement (E240 sinon).
- Importations interdites en steps/conds (sauf py_orch/typing) (E110/E111).
- Pas de boucles/try/with/eval/open… en step/cond (E200–E220).

Erreurs fréquentes et fixes
- E204 “Forbidden conditional in step”: déplace la décision dans un @cond ou utilise un pattern tolérant (cf. §3).
- E240 “Must return Next/Exit”: assure un return explicite dans chaque @cond/@step.

---

## 3) Cookbook “sans if en step” (patterns tolérants)
Principe: en step, pas d’if/ternaire. Utilise des fallback tolérants + déporte la décision sur un @cond dédié.

- Sélectionner la 1re ligne ou valeur par défaut
```python
rows = q.get("rows") or []
row = (rows[:1] or [{}])[0]
cycle.setdefault("ctx", {})["row"] = row
return Next("COND_HAS_ROW")
```

- @cond qui branche
```python
@cond
def COND_HAS_ROW(worker, cycle, env):
    return Exit("success") if not (cycle.get("ctx") or {}).get("row") else Next("STEP_NEXT")
```

- Fallback pour scalaires
```python
uid = ((rows[:1] or [{}])[0]).get("email_uid") or ""
number = (out or {}).get("number") or 60
result = ((out or {}).get("result")) or (idx + 1)
```

- Interdiction du ternaire en step — variante sans IfExp
```python
# Mauvais (E204)
cycle["ctx"]["row"] = rows[0] if rows else {}
# Bon
cycle["ctx"]["row"] = (rows[:1] or [{}])[0]
```

- Compteurs (COUNT/…) en 1 call/step, sans if
```python
q = env.tool("sqlite_db", operation="query", db=worker.get("db_file"), query="SELECT COUNT(*) AS n FROM t WHERE ...")
rows = q.get("rows") or []
r0 = dict((rows[:1] or [{}])[0])
n = int((r0.get("n") or 0))
```

- Incrément
```python
out = env.transform("arithmetic", op="inc", a=idx, step=1)
imap["idx"] = ((out or {}).get("result")) or (idx + 1)
```

- Chaînage step→cond systématique
```python
# step écrit les données et Next("COND_X") ; cond décide Next/Exit.
```

---

## 4) Transforms & Tools utiles
Transforms (extraits) et usages typiques:
- array_concat: fusionne des listes.
- json_ops: get/pick/set/rename/remove/merge.
- json_stringify: JSON → string.
- set_value: retour direct d’un scalaire/objet (pattern de persistance sans if).
- arithmetic: add/sub/mul/div/inc/dec avec fallback.
- date_ops: from_datetime_to_ymd_rfc, today_ymd_rfc.
- format_template: template {{KEY}} et {KEY}.
- template_map: mappe un template sur une liste → commands.
- normalize_llm_output: parsing JSON robuste depuis contenu LLM (code fences, échappements…).
- json_schema_validate: sous‑ensemble JSON Schema (type, properties, required, enum, min/max, items).
- objects_lookup: normalise une clé et mappe via dictionnaire (synonymes/domains → nom société). 
- sleep: pause coopérative (respecte cancel flag).

Découvrir la liste complète:
```json
{"tool":"py_orchestrator","params":{"operation":"transforms","limit":100}}
```

---

## 5) Graphe & Mermaid
Obtenir le graphe process (nodes/edges) ou Mermaid prêt à afficher:
```json
{
  "tool":"py_orchestrator",
  "params":{
    "operation":"graph","worker_name":"<name>",
    "graph":{
      "kind":"process",
      "include":{"shapes":true,"emojis":true,"labels":true},
      "render":{"mermaid":true}
    }
  }
}
```
- current_subgraph: extrait le sous‑graphe de la position courante (si runner actif).
- overview_subgraphs: vue d’ensemble SG→SG via exits mapping.

Convention visuelle
- Steps transform: rectangle bleu (⚙️).
- Steps tool: rectangle violet (emoji selon catégorie du tool).
- Conds: diamant.
- START/END: verts (fond #d9fdd3, bord #2e7d32).

---

## 6) Debug/Observe & Observabilité
Démarrer en debug (pause immédiate):
```json
{"tool":"py_orchestrator","params":{
  "operation":"start","worker_name":"<name>","worker_file":"workers/<name>/process.py","hot_reload":true,
  "debug":{"enable_on_start":true,"pause_at_start":true,"action":"enable_now"}
}}
```
Pilotage: debug.step, debug.continue, debug.run_until (avec timeout_sec).

Observation passive (n’avance pas le workflow):
```json
{"tool":"py_orchestrator","params":{"operation":"observe","worker_name":"<name>","observe":{"timeout_sec":30}}}
```

Status (incl. metrics et timeline récente):
```json
{"tool":"py_orchestrator","params":{"operation":"status","worker_name":"<name>","include_metrics":true}}
```

Erreurs/succès enrichis
- En step, le runner persiste automatiquement (DB job_steps.details_json et KV):
  - call (dernier appel tool/transform)
  - last_result_preview
  - error (si échec)
- Audit de run (table run_audit): statut, durée, dernier nœud, last_call_json, last_result_preview…

---

## 7) Config worker (config/)
Structure supportée (sous workers/<name>/config/):
- config.json: fusion profonde (deep‑merge) dans metadata au démarrage/hot‑reload.
- prompts/*.md ou *.txt: injecte metadata.prompts[stem] = contenu.
- CONFIG_DOC.json: docs libres (surfacent dans status/config).

Lecture/écriture via tool py_orchestrator (operation=config):
- Lire (scan complet):
```json
{"tool":"py_orchestrator","params":{"operation":"config","worker_name":"<name>"}}
```
- Écrire un prompt (autorange vers prompts/<clé>.md):
```json
{"tool":"py_orchestrator","params":{
  "operation":"config","worker_name":"<name>",
  "set":{"key_path":"prompts.notify_email","value":"...","storage":"file"}
}}
```
- Écrire une valeur JSON imbriquée (config.json):
```json
{"tool":"py_orchestrator","params":{
  "operation":"config","worker_name":"<name>",
  "set":{"key_path":"domain_to_company['acme.com']","value":"ACME","storage":"file"}
}}
```

---

## 8) Validation & Checklist
Valider un worker (AST + structure):
```json
{"tool":"py_orchestrator","params":{"operation":"validate","worker_name":"<name>","validate":{"limit_steps":20}}}
```
- Enforce: 1 call/step, 0 call/cond, pas de conditionnel en step, Next/Exit obligatoires, noms uniques par subgraph, 1 edge sortant par step, edges valides.
- Compte par sous‑graphe (steps/conds) et total (lisibilité, limite paramétrable `limit_steps`).

Checklist avant run
- [ ] 1 appel par step / 0 appel dans les conds.
- [ ] Pas de `if/elif/else` ni ternaire dans les steps (utiliser §3).
- [ ] Formats provider‑specific gérés (ex: dates Guardian `YYYY-MM-DD`).
- [ ] Transforms & tools testés (petits volumes, `limit`).
- [ ] `validate` OK (≤ 20 steps/sous‑graphe recommandés).
- [ ] Graphe Mermaid propre (`operation=graph`).
- [ ] Debug prêt (pause au premier nœud si besoin). Observabilité OK (status/recent_steps).

Notes avancées
- Hot‑reload activable via `hot_reload:true` (les modifications de code et config/ sont prises en compte, avec UID de process mis à jour).
- Politique tools stricte possible: `PY_ORCH_STRICT_TOOLS=true` → avertissements “unknown tools” deviennent bloquants en préflight.

Résumé
- Code des steps atomiques, “sans if”, 1 appel env.* par step.
- Déporte les décisions dans des @cond.
- Utilise les transforms pour mapper/filtrer/nettoyer et éviter la logique conditionnelle en step.
- Appuie‑toi sur validate + graphe Mermaid + debug/observe pour un cycle de dev rapide et robuste.
