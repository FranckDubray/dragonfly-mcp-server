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
