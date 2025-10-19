# 🤖 AI/LLM Curation Worker

Worker d'orchestration pour la curation automatisée des actualités IA/LLM (≤ 72h), avec fusion du rapport précédent et déduplication, génération d’un rapport FR lisible grand public mais techniquement fiable.

---

## 📋 Description

- Collecte multi-sources (News, Reddit, arXiv, Papers With Code, Sonar + blogs/labs selon config)
- Fraîcheur stricte: ≤ 72 heures (3 jours)
- Double verrou fraîcheur:
  1) Filtrage côté API via les paramètres MCP (from_date/to_date, etc.)
  2) Filet de sécurité moteur via transform `filter_by_date` (déterministe)
- Scoring via GPT (pertinence/novelty/source/diversité)
- Validation qualité via Sonar (score ≥ 7/10)
- Fusion/dédoublonnage avec le rapport précédent via GPT (sortie JSON stricte), puis format final FR
- Sauvegarde en base unique du worker (`worker_ai_curation.db`)

---

## 🧭 Politique de fraîcheur (≤ 72h)

- Cutoff dynamique: `from_date = now - 3 jours`, `to_date = now` (UTC)
- Priorité aux filtres API (MCP params) pour réduire le volume amont:
  - News (news_aggregator): `from_date`, `to_date`, `query` stricte LLM-core
  - Reddit (reddit_intelligence): `time_filter=week` (approx), puis filtre moteur <72h via `created_utc`
  - arXiv (academic_research_super): filtre moteur <72h via `publication_date` (et bornage année si utile)
  - Sonar: contrainte dans le prompt (imposer `published_at` ISO et ≤72h)
- Sécurité moteur (transform `filter_by_date`): applique la règle <72h de manière déterministe par source

---

## 🔄 Workflow (v6.0.3)

1) Collecte (API-level filters d’abord)
- News: requête LLM-core + from/to
- Reddit: multi_subs (time_filter=week)
- arXiv: derniers papiers (max_results 30)
- PWC: page “latest”
- Sonar: recherche temps réel (prompt)

2) Normalisation & Fraîcheur
- Normalise Sonar (JSON)
- `filter_by_date` par source (news/reddit/arXiv/sonar)
- Déduplication éventuelle (optionnelle) avant LLM (par URL)

3) Scoring & Validation
- GPT scoring → top10 (mix sources)
- Sonar validation (score >= 7) + retry loop (max 3)

4) Fusion / Dédup rapport
- Charge le rapport précédent (markdown + top10_json)
- GPT “merge” (prompts/gpt_merge_report_fr.json) → JSON: {final_report_markdown, final_top10}
- Parse + utilise `final_top10` pour la sauvegarde

5) Sauvegarde
- DB: `reports(report_markdown, top10_json, avg_score, retry_count, completed_at, ...)`

---

## 📁 Répertoire

```
workers/ai_curation/
├── main.process.json                 # Process principal
├── config/
│   ├── worker_ctx.json               # db_name=worker_ai_curation, modèles, seuils, etc.
│   └── scopes.json                   # Scopes cycle*
├── prompts/
│   ├── gpt_scoring.json              # Scoring (rappel de FROM/TO ISO, JSON only)
│   ├── sonar_fetch.json              # Sonar (published_at ISO obligatoire, ≤72h)
│   ├── sonar_validation.json         # Validation Sonar (score 1-10 + feedback JSON)
│   └── gpt_merge_report_fr.json      # Fusion/dédoublonnage de rapports (JSON strict)
└── README.md
```

---

## 🗄️ Base de données (worker_ai_curation.db)

- `validation_logs(id, timestamp, attempt, score, feedback, top10_json)`
- `reports(id, created_at, date_from, date_to, report_markdown, avg_score, retry_count, top10_json, completed_at)`

---

## 🚀 Lancement

```python
from src.tools.orchestrator import run

# Start
run(operation="start", worker_name="ai_curation", worker_file="workers/ai_curation/main.process.json", hot_reload=True)

# Status
run(operation="status", worker_name="ai_curation")

# Stop
run(operation="stop", worker_name="ai_curation", stop={"mode": "soft"})
```

---

## 🎛️ MCP params (filtres côté API)

- News (news_aggregator.search_news)
  - `query`: (LLM OR "large language model" OR transformer OR "fine-tuning") AND (OpenAI OR Anthropic OR DeepMind OR "Google AI" OR Meta)
  - `from_date`: `${cycle.dates.from}` (ISO date YYYY-MM-DD)
  - `to_date`: `${cycle.dates.now}` (ISO date YYYY-MM-DD)
  - `providers`: ["nyt","guardian"], `limit`: 30, pagination si besoin
- Reddit (reddit_intelligence.multi_search)
  - `subreddits`: ["MachineLearning","LocalLLaMA","OpenAI"], `limit_per_sub`: 10, `time_filter`: "week"
  - Filtrage moteur <72h via `created_utc`
- arXiv (academic_research_super.search_papers)
  - `query` LLM-core, `max_results`: 30; filtrage moteur via `publication_date`
- Sonar (call_llm)
  - Prompt impose `published_at` ISO ≤72h; filtre moteur `filter_by_date` en plus

---

## 🧪 Qualité & Traçabilité

- Compteurs par source: `cycle.metrics.*_kept` / `*_dropped` après `filter_by_date`
- Fusion GPT: retourne JSON strict; on exige `published_at` dans `final_top10[]`
- Déduplication: par URL et par titres quasi-identiques (règle de prompt), + option filet moteur `dedupe_by_url`

---

## 🛠️ Transforms utilisés

- `filter_by_date` (déterministe, <72h) — SÉCURITÉ
- `normalize_llm_output`, `extract_field`, `json_stringify`, `sanitize_text`, `increment`, `set_value`

NB: Les transforms sont pures (aucune I/O). Toute I/O passe par les tools MCP (`http_tool`, `sqlite_db`, etc.).

---

## 📝 Changelog

- v6.0.3 (2025-10-18)
  - Fraîcheur: filtres API (MCP) + `filter_by_date` moteur
  - Fusion/dédoublonnage GPT entre ancien et nouveau rapport
  - Refactor transforms: 1 fichier = 1 transform (pur)
