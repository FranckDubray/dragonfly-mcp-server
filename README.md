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

## ✨ Nouveautés (1.27.4)

### 🔔 Sonnerie & Volume unifié
- Sonnerie “Skype-like” par défaut (≈400/450 Hz), cadence tu‑tu‑tuu tu‑tu‑tu, agréable et familière pendant 2–10 s d’init.
- Volume par défaut 50% et curseur unique pilotant à la fois la sonnerie et la voix IA (setVolume partagé).

### 🧠 VAD & coupure IA instantanée
- Dès que l’utilisateur parle, arrêt immédiat de la sortie IA et annulation de la réponse en cours; reprise rapide au silence stable.

### 📈 Overlay Process (Mermaid) enrichi
- Préchargement Mermaid au chargement de page (/workers) pour supprimer la latence.
- KPIs “Activité (dernière heure)” (Tâches, Appels call_llm, Cycles) mis à jour à chaque refresh.
- Replay “magnétophone” (⏮ ⏪ ▶︎/⏸ ⏩ ⏭), suivi live si on est “au bout”, pas d’auto‑avance si on explore le passé.
- Alerte d’incohérence logs ↔ schéma avec détails: id + nom de nœud + date/heure (échantillons limités).

### 🟩🟧🟥 Cartes colorées par activité (1h)
- 0–15 → vert | 16–40 → orange | >40 → rouge

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
4. Cliquer 🧭 “Processus” → schéma Mermaid réel, nœud courant, arguments, historique, replay.
5. Le curseur Volume contrôle sonnerie + voix IA.

---

## 📝 Changelog
Voir `CHANGELOG.md`.
