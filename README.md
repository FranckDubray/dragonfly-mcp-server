<div align="center">

<img src="assets/LOGO_DRAGONFLY_HD.jpg" alt="Dragonfly logo" width="120" style="background:#ffffff; padding:6px; border-radius:8px;" />

# 🐉 Dragonfly MCP Server

Serveur MCP multi‑outils, rapide et extensible, propulsé par FastAPI. **42 tools** prêts à l'emploi, orchestrateur LLM avancé, panneau de contrôle web moderne.

[![License: MIT](./LICENSE)](./LICENSE)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-%F0%9F%9A%80-009688)

</div>

---

## 🚀 Installation

```bash
git clone https://github.com/FranckDubray/dragonfly-mcp-server.git
cd dragonfly-mcp-server
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\Activate.ps1
pip install -U pip && pip install -e ".[dev]"
./scripts/dev.sh
```

Par défaut: http://127.0.0.1:8000

---

## 🧠 Nouveauté majeure: Dev Navigator (couteau suisse LLM)

Un seul outil pour explorer un dépôt de code de manière ultra-efficace et sans flood: compose, overview, tree, search, outline, open (plans FS), endpoints, tests, et Q&A index par release (symbol_info/find_callers/...)

- Anti-flood dur: cap 20 KB par réponse, anchors‑only par défaut, pagination‑first, fs_requests pour lecture via FS.
- .gitignore respecté (best‑effort), docs volumineux bloqués par défaut (README/CHANGELOG/docs).
- Index par release (SQLite) prioritaire: réponses Q&A instantanées quand ./sqlite3/<slug>/<tag>__<sha>/index.db est présent.
- Slug stable: DEVNAV_REPO_SLUG (CI + serveur) pour résoudre ./sqlite3/<slug>/...

Voir les specs et l’API: src/tool_specs/dev_navigator.json et src/tools/_dev_navigator.

---

## 🧰 Outils inclus (42)

[Liste groupée par catégories...]  
> Détails complets : [src/tools/README.md](./src/tools/README.md)

---

## ⚙️ Configuration

Variables clés (.env):
- DEVNAV_REPO_SLUG=dragonfly-mcp-server (slug stable pour l’index Dev Navigator)
- AI_PORTAL_TOKEN, LLM_ENDPOINT, … (voir .env.example)

---

## 🧩 CI “on: release” (index automatique)

Le workflow GitHub Actions construit et publie l’Index Release Pack à chaque release:
- .github/workflows/devnav_index.yml
- Génère: ./sqlite3/<slug>/<tag>__<sha>/index.db + manifest.json et les attache aux releases.

Côté serveur MCP: déposer ces 2 fichiers sous ./sqlite3/<slug>/<tag>__<sha>/ (et latest/ si souhaité), définir DEVNAV_REPO_SLUG, et redémarrer le process.

---

## 📚 Documentation

- Guide LLM: [LLM_DEV_GUIDE.md](./LLM_DEV_GUIDE.md)
- Catalog tools: [src/tools/README.md](./src/tools/README.md)
- Changelog: [CHANGELOG.md](./CHANGELOG.md)
- API: [src/README.md](./src/README.md)

---

## 📄 Licence

MIT — voir [LICENSE](./LICENSE)
