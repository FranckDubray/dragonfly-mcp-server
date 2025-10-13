<div align="center">

<img src="assets/LOGO_DRAGONFLY_HD.jpg" alt="Dragonfly logo" width="120" style="background:#ffffff; padding:6px; border-radius:8px;" />

# 🐉 Dragonfly MCP Server

Serveur MCP multi‑outils, rapide et extensible, propulsé par FastAPI. **44 tools** prêts à l'emploi, orchestrateur LLM avancé, panneau de contrôle web moderne.

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

Un seul outil pour explorer un dépôt de code de manière ultra-efficace et sans flood: compose, overview, tree, search, outline, open (plans FS), endpoints, tests, metrics et Q&A index (symbol_info/find_callers/...).

- Anti-flood dur: cap 20 KB par réponse, anchors‑only par défaut, pagination‑first, fs_requests pour lecture via FS.
- .gitignore respecté (best‑effort), docs volumineux bloqués par défaut (README/CHANGELOG/docs).
- Index par release (SQLite) prioritaire.

Voir les specs et l’API: src/tool_specs/dev_navigator.json et src/tools/_dev_navigator.

---

## 🧩 Nouveauté: Host Audit (plans OS/progiciels via SSH)

Audit compact (lecture‑seule) de machines et progiciels. Génère des plans safe à exécuter avec l’outil ssh_admin.

- macos_local (laptop): résumé OS/hardware/apps (échantillon), Homebrew, Word installé ?
- ubuntu_ssh_plan: OS, ressources, réseau/ports, pare‑feu (ufw, nft/iptables), SSH (systemctl), logs critiques (journalctl), packages (échantillon), ls sur paths_hint.
- mysql_ssh_plan: version, variables clés (logs, max_connections…), Threads_connected, tail log erreur.
- symfony_ssh_plan: php/composer, bin/console about + debug:router (tronqués), grep routes YAML.
- nginx_ssh_plan: version, conf head (nginx -T/nginx.conf), tails logs access/error (limités).
- apache_ssh_plan: version, vhosts (-S tronqué), head conf principale, tail logs error (limités).
- phpfpm_ssh_plan: version, test conf (-tt tronqué), head pools *.conf, tails logs fpm (limités).
- nodejs_ssh_plan: node -v, npm -v, pm2 ls si présent.

Usage type:
1) Générer un plan:
```json
POST /execute
{"tool":"host_audit","params":{"operation":"ubuntu_ssh_plan","profile":"prod","logs_lines":200,"paths_hint":["/var/www/app"]}}
```
2) Exécuter via SSH:
```json
POST /execute
{"tool":"ssh_admin","params":{"operation":"exec","profile":"prod","command":"<colle ici la commande du plan>"}}
```

---

## 🧰 Outils inclus (extrait)

- Development: Dev Navigator, Git, GitBook, Python Sandbox, Tool Audit
- Communication: Discord Bot/Webhook, Email Send (SMTP), IMAP, Telegram Bot
- Data & Storage: CoinGecko, Excel to SQLite, SQLite Database
- Documents: Doc Scraper, Office→PDF, PDF Download/Search/ToText
- Media: FFmpeg Frames, Gemini Image Studio, Video Transcription, YouTube (search/download)
- Transportation: Aviation Weather, Flight Tracker, Ship Tracker, Vélib'
- Networking: HTTP Client
- Utilities: Date/Time, Device Location, Google Maps, Math, Open‑Meteo, Random Numbers, SSH Admin, Host Audit
- Social & Entertainment: Astronomy, Chess.com, Reddit, Trivia API

Version auto‑générée détaillée: src/tools/README.md

---

## ⚙️ Configuration

Variables clés (.env):
- DEVNAV_REPO_SLUG=dragonfly-mcp-server
- SSH_PROFILES_JSON (pour ssh_admin)
- AI_PORTAL_TOKEN, LLM_ENDPOINT, … (voir .env.example)

---

## 🧪 CI “on: release” (index automatique)

Le workflow GitHub Actions construit et publie l’Index Release Pack à chaque release:
- .github/workflows/devnav_index.yml
- Génère: ./sqlite3/<slug>/<tag>__<sha>/index.db + manifest.json

Côté serveur MCP: déposer ces 2 fichiers sous ./sqlite3/<slug>/<tag>__<sha>/ (et latest/ si souhaité), définir DEVNAV_REPO_SLUG, et redémarrer le process.

---

## 📚 Documentation

- Guide LLM: [LLM_DEV_GUIDE.md](./LLM_DEV_GUIDE.md)
- Catalog tools (auto‑généré): [src/tools/README.md](./src/tools/README.md)
- Changelog: [CHANGELOG.md](./CHANGELOG.md)
- API: [src/README.md](./src/README.md)

---

## 🗄️ Licence

MIT — voir [LICENSE](./LICENSE)
