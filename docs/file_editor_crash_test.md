# 🧪 File Editor — Plan de Crash Test

> **Contexte** : Tu es un assistant de test. Tu as accès aux tools `file_editor` et `filesystem_v3`.
> Tu dois exécuter ce plan de test **séquentiellement**, en notant ✅ ou ❌ pour chaque test.
> À la fin, produis un **rapport de synthèse**.
>
> **Environnement** : Backend local `http://localhost:8001`
> **Scope par défaut** : `user`

---

## Phase 0 — Pré-requis

Vérifie que le tool `file_editor` est disponible en appelant :
```json
{"operation": "list", "scope": "user", "max_keys": 5}
```
Si ça retourne une réponse avec `"success": true`, tu peux commencer.

---

## Phase 1 — CRUD basique (create / list / append / delete)

### T01 — Créer un fichier texte simple
```json
{"operation": "create", "path": "_crash_test/hello.txt", "content": "Hello World!\nLine 2\nLine 3\n"}
```
**Attendu** : `success: true`, `version_id` retourné, `size` = 30 (environ)

### T02 — Créer un fichier Markdown
```json
{"operation": "create", "path": "_crash_test/readme.md", "content": "# Crash Test\n\n## Section A\n- item 1\n- item 2\n- item 3\n\n## Section B\nSome content here.\n", "content_type": "text/markdown"}
```
**Attendu** : `success: true`, `content_type: text/markdown`

### T03 — Créer un fichier JSON
```json
{"operation": "create", "path": "_crash_test/config.json", "content": "{\n  \"database\": {\n    \"host\": \"localhost\",\n    \"port\": 5432,\n    \"name\": \"testdb\"\n  },\n  \"debug\": true,\n  \"version\": \"1.0.0\"\n}"}
```
**Attendu** : `success: true`, content_type auto-détecté `application/json`

### T04 — Créer un fichier YAML
```json
{"operation": "create", "path": "_crash_test/config.yaml", "content": "server:\n  host: 0.0.0.0\n  port: 8080\n  debug: true\n\nlogging:\n  level: info\n  format: json\n  output: stdout\n\nfeatures:\n  feature_a: true\n  feature_b: false\n  feature_c: true\n"}
```
**Attendu** : `success: true`, content_type auto-détecté `text/yaml`

### T05 — Lister les fichiers créés
```json
{"operation": "list", "prefix": "_crash_test/"}
```
**Attendu** : 4 objets (hello.txt, readme.md, config.json, config.yaml)

### T06 — Append sur fichier existant
```json
{"operation": "append", "path": "_crash_test/hello.txt", "content": "Line 4 appended\nLine 5 appended"}
```
**Attendu** : `success: true`, `total_size` > taille initiale

### T07 — Append sur fichier inexistant (DOIT ÉCHOUER)
```json
{"operation": "append", "path": "_crash_test/NEXISTE_PAS.txt", "content": "boo"}
```
**Attendu** : `error` (fichier non trouvé)

---

## Phase 2 — Édition chirurgicale (edit)

### T08 — search_replace simple
```json
{"operation": "edit", "path": "_crash_test/config.yaml", "edits": [
  {"type": "search_replace", "search": "debug: true", "replace": "debug: false"}
]}
```
**Attendu** : `changed: true`, diff montre le changement, 1 edit applied

### T09 — search_replace multiple (batch)
```json
{"operation": "edit", "path": "_crash_test/config.json", "edits": [
  {"type": "search_replace", "search": "\"host\": \"localhost\"", "replace": "\"host\": \"prod-db.internal\""},
  {"type": "search_replace", "search": "\"debug\": true", "replace": "\"debug\": false"},
  {"type": "search_replace", "search": "\"version\": \"1.0.0\"", "replace": "\"version\": \"2.0.0\""}
]}
```
**Attendu** : `changed: true`, `edits_applied: 3`, diff montre 3 changements

### T10 — search_replace occurrence spécifique
D'abord crée un fichier avec des doublons :
```json
{"operation": "create", "path": "_crash_test/duplicates.txt", "content": "foo bar foo baz foo qux"}
```
Puis remplace seulement la 2e occurrence de "foo" :
```json
{"operation": "edit", "path": "_crash_test/duplicates.txt", "edits": [
  {"type": "search_replace", "search": "foo", "replace": "REPLACED", "occurrence": 2}
]}
```
**Attendu** : Résultat = `"foo bar REPLACED baz foo qux"` (seule la 2e est remplacée)

### T11 — regex_replace
```json
{"operation": "edit", "path": "_crash_test/config.json", "edits": [
  {"type": "regex_replace", "search": "\"port\":\\s*\\d+", "replace": "\"port\": 3306"}
]}
```
**Attendu** : `changed: true`, port changé de 5432 → 3306

### T12 — insert_after
```json
{"operation": "edit", "path": "_crash_test/readme.md", "edits": [
  {"type": "insert_after", "line": 3, "content": "## Section Inserted\nThis was inserted after line 3."}
]}
```
**Attendu** : 2 nouvelles lignes insérées après la ligne 3

### T13 — insert_before
```json
{"operation": "edit", "path": "_crash_test/readme.md", "edits": [
  {"type": "insert_before", "line": 1, "content": "<!-- Auto-generated test file -->"}
]}
```
**Attendu** : Commentaire inséré tout en haut (avant la ligne 1)

### T14 — delete_lines
```json
{"operation": "edit", "path": "_crash_test/hello.txt", "edits": [
  {"type": "delete_lines", "start_line": 2, "end_line": 3}
]}
```
**Attendu** : Lignes 2 et 3 supprimées

### T15 — replace_lines
```json
{"operation": "edit", "path": "_crash_test/config.yaml", "edits": [
  {"type": "replace_lines", "start_line": 1, "end_line": 3, "content": "server:\n  host: 127.0.0.1\n  port: 9090\n  debug: false\n  workers: 4"}
]}
```
**Attendu** : Les 3 premières lignes remplacées par 5 nouvelles lignes

### T16 — dry_run (preview sans écrire)
```json
{"operation": "edit", "path": "_crash_test/config.yaml", "dry_run": true, "edits": [
  {"type": "search_replace", "search": "info", "replace": "CATASTROPHE"}
]}
```
**Attendu** : `dry_run: true`, `changed: true`, diff affiché, **mais le fichier NE doit PAS être modifié**
Vérifie en refaisant le même edit sans dry_run — la string "info" doit toujours être là.

### T17 — edit chaîné complexe (multi-type en un seul appel)
```json
{"operation": "edit", "path": "_crash_test/readme.md", "edits": [
  {"type": "search_replace", "search": "item 1", "replace": "item ONE"},
  {"type": "insert_after", "line": 5, "content": "- item 1bis (inserted)"},
  {"type": "regex_replace", "search": "item \\d+", "replace": "item X"}
]}
```
**Attendu** : Les 3 opérations appliquées séquentiellement. D'abord "item 1" → "item ONE", puis insertion, puis tous les "item N" restants → "item X"

---

## Phase 3 — Versioning & Diff

### T18 — Lister les versions
```json
{"operation": "versions", "path": "_crash_test/config.yaml"}
```
**Attendu** : Plusieurs versions (au moins 3 après les edits), triées par date décroissante

### T19 — Diff entre deux versions
Prends la première et la dernière version_id du résultat T18 :
```json
{"operation": "diff", "path": "_crash_test/config.yaml", "version_a": "<PREMIÈRE_VERSION>", "version_b": "<DERNIÈRE_VERSION>"}
```
**Attendu** : `identical: false`, diff unifié lisible

### T20 — Diff avec une seule version (vs current)
```json
{"operation": "diff", "path": "_crash_test/config.yaml", "version_a": "<PREMIÈRE_VERSION>"}
```
**Attendu** : Compare la première version avec la version courante

### T21 — Restore vers une version antérieure
Prends le `version_id` de la toute première version de config.yaml :
```json
{"operation": "restore", "path": "_crash_test/config.yaml", "version_id": "<PREMIÈRE_VERSION>"}
```
**Attendu** : `success: true`, `new_version_id` créé. Le fichier revient à son contenu initial.
Vérifie en faisant un diff entre le nouveau current et la première version → `identical: true`

---

## Phase 4 — Workspace (load / unload)

> **Note** : Le thread_id est fourni par le backend au moment du chat. Utilise ton propre thread_id
> (tu le trouves dans le contexte de la conversation, ou invente-en un comme `thread_stream_crashtest001`).

### T22 — Load un fichier complet
```json
{"operation": "load", "path": "_crash_test/config.yaml", "thread_id": "<TON_THREAD_ID>"}
```
**Attendu** : `success: true`, `loaded_size` = taille du fichier, `workspace_files: 1`

### T23 — Load un fichier avec range (partiel)
```json
{"operation": "load", "path": "_crash_test/readme.md", "thread_id": "<TON_THREAD_ID>", "range": "0-50"}
```
**Attendu** : `loaded_size: 50`, `total_size` > 50, `workspace_files: 2`

### T24 — Load un 3e fichier
```json
{"operation": "load", "path": "_crash_test/config.json", "thread_id": "<TON_THREAD_ID>"}
```
**Attendu** : `workspace_files: 3`, `workspace_total` = somme des tailles

### T25 — Vérifier que le workspace est dans le contexte
Après les loads T22-T24, tu devrais voir le contenu des fichiers dans ton contexte
(balises `<workspace>` avec `<file>`). Décris ce que tu vois.

### T26 — Reload un fichier avec un range différent
```json
{"operation": "load", "path": "_crash_test/readme.md", "thread_id": "<TON_THREAD_ID>", "range": "0-100"}
```
**Attendu** : Le fichier est mis à jour (pas dupliqué), `loaded_size: 100`, toujours `workspace_files: 3`

### T27 — Unload un fichier spécifique
```json
{"operation": "unload", "path": "_crash_test/config.json", "thread_id": "<TON_THREAD_ID>"}
```
**Attendu** : `workspace_files: 2`, le fichier n'apparaît plus dans le contexte au tour suivant

### T28 — Unload all
```json
{"operation": "unload", "thread_id": "<TON_THREAD_ID>", "all": true}
```
**Attendu** : `removed_count: 2`, `workspace_files: 0`, plus aucun `<workspace>` au tour suivant

### T29 — Load + Edit + vérifier refresh auto
1. Load `_crash_test/hello.txt`
2. Edit : `search_replace` "Hello World!" → "Bonjour Monde!"
3. Au tour suivant, le contenu affiché dans `<workspace>` doit refléter "Bonjour Monde!" (pas l'ancien)

---

## Phase 5 — Cas d'erreur & sécurité (TOUT DOIT ÉCHOUER)

### T30 — Path traversal
```json
{"operation": "create", "path": "../../../etc/passwd", "content": "hack"}
```
**Attendu** : `error: "Path must not contain '..'"` 

### T31 — Écrire dans un scope read-only
```json
{"operation": "create", "path": "test.txt", "scope": "datasource", "content": "hack"}
```
**Attendu** : `error` contenant "read-only"
*(Note : nécessite le param `datasource` — tester aussi sans)*

### T32 — Edit sans edits
```json
{"operation": "edit", "path": "_crash_test/hello.txt"}
```
**Attendu** : `error` (edits requis)

### T33 — Edit avec edits vide
```json
{"operation": "edit", "path": "_crash_test/hello.txt", "edits": []}
```
**Attendu** : `error` (edits ne doit pas être vide)

### T34 — Edit : search string introuvable
```json
{"operation": "edit", "path": "_crash_test/hello.txt", "edits": [
  {"type": "search_replace", "search": "CETTE_STRING_NEXISTE_PAS", "replace": "boo"}
]}
```
**Attendu** : `error` contenant "not found"

### T35 — Edit : regex invalide
```json
{"operation": "edit", "path": "_crash_test/hello.txt", "edits": [
  {"type": "regex_replace", "search": "[invalid(regex", "replace": "boo"}
]}
```
**Attendu** : `error` contenant "invalid pattern"

### T36 — Edit : numéro de ligne hors range
```json
{"operation": "edit", "path": "_crash_test/hello.txt", "edits": [
  {"type": "insert_after", "line": 99999, "content": "impossible"}
]}
```
**Attendu** : `error` contenant "out of range"

### T37 — Edit : delete_lines avec end < start
```json
{"operation": "edit", "path": "_crash_test/hello.txt", "edits": [
  {"type": "delete_lines", "start_line": 5, "end_line": 2}
]}
```
**Attendu** : `error` contenant "end_line" et "start_line"

### T38 — Delete fichier inexistant
```json
{"operation": "delete", "path": "_crash_test/FANTOME.txt"}
```
**Attendu** : `error` (ou `success` si S3 retourne 200 sur delete d'un objet absent — noter le comportement)

### T39 — Restore avec version_id bidon
```json
{"operation": "restore", "path": "_crash_test/hello.txt", "version_id": "0000000000000"}
```
**Attendu** : `error` (version non trouvée)

### T40 — Load sans thread_id
```json
{"operation": "load", "path": "_crash_test/hello.txt"}
```
**Attendu** : `error: "Parameter 'thread_id' is required for load"`

### T41 — Unload un fichier non loadé
```json
{"operation": "unload", "path": "_crash_test/JAMAIS_LOADE.txt", "thread_id": "<TON_THREAD_ID>"}
```
**Attendu** : `error` contenant "not found in workspace"

### T42 — Opération invalide
```json
{"operation": "YOLO"}
```
**Attendu** : `error` contenant "Invalid operation"

---

## Phase 6 — Stress & edge cases

### T43 — Fichier vide
```json
{"operation": "create", "path": "_crash_test/empty.txt", "content": ""}
```
Puis :
```json
{"operation": "append", "path": "_crash_test/empty.txt", "content": "first content"}
```
**Attendu** : Create OK (size 0), append OK (total_size = 13)

### T44 — Fichier avec caractères spéciaux (UTF-8)
```json
{"operation": "create", "path": "_crash_test/unicode.txt", "content": "Héllo Wörld! 🚀\nLigne avec des accents: éàüöñ\n日本語テスト\nEmoji: 🎯✅❌🔥\n"}
```
Puis edit :
```json
{"operation": "edit", "path": "_crash_test/unicode.txt", "edits": [
  {"type": "search_replace", "search": "🚀", "replace": "🌍"}
]}
```
**Attendu** : Les deux opérations réussissent, les caractères UTF-8 sont préservés

### T45 — Fichier avec très longues lignes
Crée un fichier dont une ligne fait 10 000 caractères :
```json
{"operation": "create", "path": "_crash_test/longline.txt", "content": "short line\n<10000 fois 'A'>\nshort again\n"}
```
Puis edit sur cette longue ligne avec regex.
**Attendu** : Fonctionne sans crash

### T46 — Edits en cascade qui modifient le nombre de lignes
```json
{"operation": "edit", "path": "_crash_test/hello.txt", "edits": [
  {"type": "insert_after", "line": 1, "content": "NEW LINE A\nNEW LINE B\nNEW LINE C"},
  {"type": "delete_lines", "start_line": 5, "end_line": 6}
]}
```
**Attendu** : Les numéros de ligne du 2e edit s'appliquent au contenu **après** le 1er edit (séquentiel). Vérifier que c'est cohérent.

### T47 — Versions rapides (créer 5 versions en rafale)
```json
// Faire 5 edits successifs sur le même fichier
{"operation": "edit", "path": "_crash_test/config.yaml", "edits": [{"type": "search_replace", "search": "info", "replace": "debug"}]}
{"operation": "edit", "path": "_crash_test/config.yaml", "edits": [{"type": "search_replace", "search": "debug", "replace": "warn"}]}
{"operation": "edit", "path": "_crash_test/config.yaml", "edits": [{"type": "search_replace", "search": "warn", "replace": "error"}]}
{"operation": "edit", "path": "_crash_test/config.yaml", "edits": [{"type": "search_replace", "search": "error", "replace": "trace"}]}
{"operation": "edit", "path": "_crash_test/config.yaml", "edits": [{"type": "search_replace", "search": "trace", "replace": "info"}]}
```
Puis `versions` → **Attendu** : au moins 5 nouvelles versions

---

## Phase 7 — Nettoyage

### T48 — Supprimer tous les fichiers de test
```json
{"operation": "delete", "path": "_crash_test/hello.txt"}
{"operation": "delete", "path": "_crash_test/readme.md"}
{"operation": "delete", "path": "_crash_test/config.json"}
{"operation": "delete", "path": "_crash_test/config.yaml"}
{"operation": "delete", "path": "_crash_test/duplicates.txt"}
{"operation": "delete", "path": "_crash_test/empty.txt"}
{"operation": "delete", "path": "_crash_test/unicode.txt"}
{"operation": "delete", "path": "_crash_test/longline.txt"}
```
Puis : `{"operation": "list", "prefix": "_crash_test/"}`
**Attendu** : `count: 0` (ou seulement des delete markers)

### T49 — Nettoyer le workspace
```json
{"operation": "unload", "thread_id": "<TON_THREAD_ID>", "all": true}
```

### T50 — Vérification finale
```json
{"operation": "list", "prefix": "_crash_test/"}
```
**Attendu** : Plus rien.

---

## 📋 Template de rapport

```
# Rapport Crash Test — file_editor
Date : ...
Thread ID : ...
Environnement : localhost:8001

## Résultats

| # | Test | Résultat | Notes |
|---|------|----------|-------|
| T01 | Create .txt | ✅/❌ | ... |
| T02 | Create .md | ✅/❌ | ... |
...
| T50 | Vérif finale | ✅/❌ | ... |

## Résumé
- Total : XX/50
- Passés : XX
- Échoués : XX
- Observations : ...

## Bugs trouvés
1. ...
2. ...
```
