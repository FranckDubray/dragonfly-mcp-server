# Changelog

All notable changes to this project will be documented in this file.

**Note**: Older entries have been archived under `changelogs/` (range-based files).

---

## [1.26.3] - 2025-10-13

### Host Audit (plans compacts OS/progiciels via SSH)
- feat(host_audit): nouveau tool générant des PLANS d’audit (pas d’exécution) pour macOS (local), Ubuntu, MySQL, Symfony, Nginx, Apache, PHP‑FPM, Node.js.
- feat(connectors):
  - ubuntu_ssh_plan: OS résumé (os-release, uname, uptime), ressources (df/free/top/ps), réseau/ports (ss/netstat), pare‑feu (ufw, nft/iptables), SSH (systemctl), logs critiques (journalctl), packages (échantillon), ls sur paths_hint.
  - mysql_ssh_plan: version, variables clés (log_error/slow/general/max_connections), Threads_connected, tail limité log erreur.
  - symfony_ssh_plan: php/composer, bin/console about + debug:router (tronqués), grep routes YAML.
  - nginx_ssh_plan: version, conf head (nginx -T ou nginx.conf), tails logs access/error (limités).
  - apache_ssh_plan: version, vhosts (apachectl/httpd -S tronqué), head conf principale, tail logs error (limités).
  - phpfpm_ssh_plan: version, test conf (-tt tronqué), head pools *.conf, tails logs fpm (limités).
  - nodejs_ssh_plan: node -v, npm -v, pm2 ls si présent.
- safety: aucun rapatriement massif, tout est tronqué/échantillonné; une seule commande SSH concaténée par plan.

### Dev Navigator (endpoints YAML étendus)
- feat(endpoints): YAML Symfony étendu (path/methods inline/bloc/scalaire, prefix global/local, includes/imports/resources suivis). Fallback générique gateways (uri/url/basePath/rule + methods).
- refactor: extracteurs YAML dédiés (connecteur Symfony + extracteur gateway générique), intégrés dans core/endpoints avec suivi d’includes.

---

## [1.26.2] - 2025-10-13

### Tool Audit (models 1..4 + fuser par défaut)
- feat(spec): `models` accepte désormais 1 à 4 modèles (minItems=1, maxItems=4), ordre préservé. Le `fuser_model` par défaut est le premier modèle de la liste.
- feat(validators): validation stricte 1..4, dédoublonnage en conservant l’ordre, et `fuser_model=models[0]` si omis.
- docs: clarifications d’usage (1 modèle possible; comportement identique côté scheduler en mode `auto`).

---

## [1.26.1] - 2025-10-13

### Documentation
- docs(readme): README racine synchronisé avec le catalogue auto‑généré (liste complète des outils, par catégories canoniques). Ajout de Tool Audit dans "Development".
- docs(changelog): mise en avant de Tool Audit comme composant quasi‑worker (multi‑LLM, parallèle borné, fusion LLM, anti‑flood, pagination).

---

## [1.26.0] - 2025-10-13

### Tool Audit (worker-like, multi-LLM)
- feat(tool_audit): nouveau tool d’audit lecture-seule d’un tool MCP unique (perf/quality/maintain/invariants), exécution multi-modèles en parallèle (bornée), fusion algorithmique + fuser LLM, anti-flood strict (caps contexte/tokens), sortie paginée (limit, truncated, counts).
- feat(git_sensitive): détection des fichiers suivis sensibles et marqueurs de secrets (masqués), best-effort.
- perf(scheduler): parallélisme borné (global=8, par modèle=2), retry 3× avec jitter sur erreurs transitoires, agrégation d’usage cumulée (tasks + fuser).
- docs/specs: spec canonique `src/tool_specs/tool_audit.json`, implémentation `src/tools/_tool_audit/*`, catégorie `development` (UI), aucune side-effect à l’import, fichiers < 7KB par unité.
- quality: sorties compactes, anchors-only par défaut (option snippets), `fs_requests` pour lectures ultérieures, respect strict des invariants LLM DEV GUIDE.

---

## Archives

- [v1.23.0 Audit Campaign](changelogs/CHANGELOG_1.23.0_audit_campaign.md) - 17 tools audited
- [v1.22.0 to v1.22.2](changelogs/CHANGELOG_1.22.0_to_1.22.2.md)
- [v1.19.0 to v1.21.1](changelogs/CHANGELOG_1.19.0_to_1.21.1.md) - News aggregator, Trivia API, Ollama fixes
- [v1.14.3 to v1.18.2](changelogs/CHANGELOG_1.14.3_to_1.18.2.md)
- [v1.0.0 to 1.13.x](changelogs/CHANGELOG_1.0.0_to_1.13.x.md)
