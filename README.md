# 🐉 Dragonfly MCP Server

Serveur MCP (Model Context Protocol) moderne avec 45+ tools pour LLM, interface vocale temps réel et orchestration workers asynchrones.

---

## 🚀 Quickstart

```bash
# Installation
pip install -e .

# Configuration
cp .env.example .env
# Éditer .env avec vos clés API

# Démarrer le serveur (au choix)
./scripts/dev.sh          # Recommandé (Unix/Mac)
./scripts/dev.ps1         # Windows PowerShell
python src/server.py      # Direct

# Interfaces web (même serveur, port 8000)
http://localhost:8000/control     # Control Panel (tools)
http://localhost:8000/workers     # Workers Vocaux (Realtime)
```

---

## ✨ Nouveautés

### 1.27.5
- Nouveaux tools:
  - Lichess (Public API, read‑only): profils, perfs, équipes, parties, tournois, leaderboards, puzzles.
  - Stockfish (Auto‑75): évaluation de position et analyse de partie avec auto‑configuration (~75% des ressources), MultiPV, budget‑temps global.
- Catalog/tools: specs chargées dans le registre (src/tool_specs/).

### 1.27.4
- 🔔 Sonnerie “Skype-like” (≈400/450 Hz), volume unifié (slider 50%)
- 🧠 VAD: coupure IA immédiate à la parole utilisateur
- 📈 Process overlay (Mermaid): préchargement, KPIs dernière heure, replay “magnétophone”, alerte d’incohérence détaillée
- 🟩🟧🟥 Cartes colorées par activité (0–15 vert, 16–40 orange, >40 rouge)

---

## 🧩 Architecture
- FastAPI (routes workers) + SafeJSON + tool registry
- SQLite local (sqlite3/worker_*.db), scan automatique
- Config Realtime hybride (DB‑first, fallback .env)

---

## 🧪 Démo rapide
1. Ouvrir `http://localhost:8000/workers`.
2. Cliquer 📞 “Appeler” → sonnerie → session.
3. Parler: l’IA se coupe aussitôt; reprend après ~silence stable.
4. Cliquer 🧭 “Processus” → schéma Mermaid, nœud courant, arguments, historique, replay.
5. Le curseur Volume contrôle sonnerie + voix IA.

---

## 📝 Changelog
Voir `CHANGELOG.md`.


## 🧩 Worker config (config.py) — variables d’init centralisées (NOUVEAU)

Pour configurer un worker sans toucher à son process.py, placez un fichier dédié:

- Emplacement: `workers/<worker_name>/config.py`
- Clé requise: `CONFIG` (dict de variables de contexte)
- Clé optionnelle: `CONFIG_DOC` (dict var → description lisible)
- Alternatives acceptées (si vous préférez): `WORKER_CONFIG` ou `config` pour les valeurs, `CONFIG_DESC`/`DOC`/`DESCRIPTIONS` pour la doc.

Chargement & priorité
- L’orchestrateur charge `process.py` puis fusionne `config.py`.
- Priorité: les valeurs de `config.py` surchargent celles de `PROCESS.metadata` si une clé existe dans les deux.
- Les paires (valeur, description) sont exposées à l’UI et via l’API (voir ci‑dessous).

Exemple `workers/ai_curation_v2/config.py`
```python
CONFIG = {
    # Réseau / I/O
    "http_timeout_sec": 120,  # Timeout HTTP (sec) pour les calls MCP (ex: call_llm)

    # LLM
    "llm_model": "gpt-4o-mini",
    "sonar_model": "sonar",
    "llm_temperature": 0.3,

    # Logique métier
    "quality_threshold": 7,
    "max_retries": 3,

    # Sources
    "primary_sites": [
        "https://openai.com/index",
        "https://www.anthropic.com/news",
        "https://blog.google/technology/ai",
        "https://deepmind.google/discover/blog",
        "https://ai.meta.com/blog",
        "https://aws.amazon.com/blogs",
        "https://azure.microsoft.com/blog",
        "https://developer.nvidia.com/blog",
        "https://stability.ai/news",
        "https://arxiv.org"
    ],

    # Stockage
    "db_file": "worker_ai_curation_v2.db",
}

CONFIG_DOC = {
    "http_timeout_sec": "Timeout HTTP (sec) pour les appels MCP (call_llm, etc.). Défaut 30s.",
    "llm_model": "Modèle LLM principal utilisé pour le scoring et le formatage du rapport.",
    "sonar_model": "Modèle Sonar utilisé pour la validation/collecte.",
    "llm_temperature": "Température de génération LLM.",
    "quality_threshold": "Seuil de score minimal pour considérer la curation satisfaisante.",
    "max_retries": "Nombre maximal de tentatives de re‑scoring si la validation échoue.",
    "primary_sites": "Liste des sites officiels prioritaires pour l’enrichissement/validation.",
    "db_file": "Nom du fichier SQLite pour persister l’état et les rapports.",
}
```

Récupérer la config en live (API)
```json
{
  "tool": "py_orchestrator",
  "params": { "operation": "config", "worker_name": "ai_curation_v2" }
}
```
Réponse (extrait):
```json
{
  "accepted": true,
  "status": "ok",
  "worker_name": "ai_curation_v2",
  "metadata": { "http_timeout_sec": 120, "llm_model": "gpt-4o-mini", ... },
  "docs": { "http_timeout_sec": "Timeout HTTP...", ... },
  "truncated": false
}
```

Notes
- `http_timeout_sec` est lu par le runner pour configurer le timeout HTTP des tools MCP (fallback 30s). Pas besoin de variable d’env globale.
- Vous pouvez déplacer progressivement les variables de `PROCESS.metadata` vers `config.py`. Si une même clé existe dans les deux, c’est `config.py` qui gagne.
- L’API `status` continue de renvoyer `py.metadata` (pour compat) et `config` offre une vue dédiée variables+docs.
