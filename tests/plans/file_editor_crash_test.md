# 🧨 File Editor — Plan de Crash Test Complet

## Contexte

**Tool testé** : `file_editor` (branche `feat/file-editor`)
**API S3 backend** : `https://dev-ai.dragonflygroup.fr/api/v1/s3/`
**Auth** : `AI_PORTAL_TOKEN` dans `.env`

### Fichiers de référence à charger avant de commencer
```
filesystem_v3 load:
- src/tools/file_editor.py
- src/tools/_file_editor/api.py
- src/tools/_file_editor/ops_write.py
- src/tools/_file_editor/ops_read.py
- src/tools/_file_editor/edit_engine.py
- src/tools/_file_editor/s3_client.py
- src/tools/_file_editor/validators.py
- src/tool_specs/file_editor.json
```

---

## Convention de résultat

Pour chaque test, noter :
- ✅ PASS — comportement attendu
- ❌ FAIL — bug trouvé (décrire)
- ⚠️ WARN — fonctionne mais comportement discutable

---

## A. OPÉRATIONS CRUD DE BASE (10 tests)

### A1. Create — fichier simple
```json
{"operation": "create", "path": "_crashtest/basic.txt", "content": "Hello World"}
```
**Attendu** : `success: true`, `version_id` retourné, `content_type: text/plain`

### A2. Create — fichier markdown avec content_type explicite
```json
{"operation": "create", "path": "_crashtest/doc.md", "content": "# Titre\n\nParagraphe.", "content_type": "text/markdown"}
```
**Attendu** : `success: true`, `content_type: text/markdown`

### A3. Create — fichier JSON
```json
{"operation": "create", "path": "_crashtest/config.json", "content": "{\"key\": \"value\", \"number\": 42}"}
```
**Attendu** : `success: true`, `content_type: application/json` (auto-détecté)

### A4. Create — fichier vide
```json
{"operation": "create", "path": "_crashtest/empty.txt", "content": ""}
```
**Attendu** : `success: true`, `size: 0`

### A5. Create — contenu Unicode / emojis
```json
{"operation": "create", "path": "_crashtest/unicode.txt", "content": "Héllo Wörld 🌍🔥\nAccénts: àéîõü\nJaponais: こんにちは\nArabe: مرحبا"}
```
**Attendu** : `success: true`, contenu préservé intégralement

### A6. List — scope user, vérifier les fichiers créés
```json
{"operation": "list", "scope": "user", "prefix": "_crashtest/", "max_keys": 20}
```
**Attendu** : 5 objets listés (basic.txt, doc.md, config.json, empty.txt, unicode.txt)

### A7. Append — ajouter à un fichier existant
```json
{"operation": "append", "path": "_crashtest/basic.txt", "content": "\nLine 2 appended"}
```
**Attendu** : `success: true`, `total_size` > taille initiale

### A8. Append — ajouter à un fichier vide
```json
{"operation": "append", "path": "_crashtest/empty.txt", "content": "No longer empty!"}
```
**Attendu** : `success: true`, `total_size: 16`

### A9. Delete — supprimer un fichier
```json
{"operation": "delete", "path": "_crashtest/empty.txt"}
```
**Attendu** : `success: true`, `deleted: true` implicite via version_id

### A10. List — vérifier suppression
```json
{"operation": "list", "scope": "user", "prefix": "_crashtest/", "max_keys": 20}
```
**Attendu** : 4 objets (empty.txt absent)

---

## B. ÉDITION CHIRURGICALE (15 tests)

### Setup : créer le fichier de test d'édition
```json
{"operation": "create", "path": "_crashtest/editable.py", "content": "#!/usr/bin/env python3\n\"\"\"Module de test.\"\"\"\nimport os\nimport sys\n\nDEBUG = True\nVERSION = \"1.0.0\"\nHOST = \"localhost\"\nPORT = 8080\n\ndef main():\n    print(\"Hello World\")\n    if DEBUG:\n        print(\"Debug mode\")\n    return 0\n\nif __name__ == \"__main__\":\n    sys.exit(main())\n"}
```

### B1. search_replace — remplacement simple
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "search_replace", "search": "DEBUG = True", "replace": "DEBUG = False"}
]}
```
**Attendu** : `changed: true`, diff montre `-DEBUG = True` / `+DEBUG = False`

### B2. search_replace — remplacement multiple (occurrence=0 = toutes)
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "search_replace", "search": "print(", "replace": "logging.info(", "occurrence": 0}
]}
```
**Attendu** : TOUTES les occurrences de `print(` remplacées (2 occurrences)

### B3. search_replace — occurrence spécifique (1ère seulement)
Recréer le fichier d'abord, puis :
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "search_replace", "search": "print(", "replace": "FIRST_REPLACED(", "occurrence": 1}
]}
```
**Attendu** : Seule la 1ère occurrence remplacée

### B4. search_replace — chaîne introuvable
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "search_replace", "search": "THIS_DOES_NOT_EXIST", "replace": "xxx"}
]}
```
**Attendu** : `error` contenant "not found"

### B5. regex_replace — pattern valide
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "regex_replace", "search": "\"[0-9]+\\.[0-9]+\\.[0-9]+\"", "replace": "\"9.9.9\""}
]}
```
**Attendu** : `VERSION = "9.9.9"` dans le diff

### B6. regex_replace — pattern invalide
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "regex_replace", "search": "[invalid(regex", "replace": "xxx"}
]}
```
**Attendu** : `error` contenant "invalid pattern"

### B7. regex_replace — pattern qui ne matche rien
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "regex_replace", "search": "ZZZZZ[0-9]+", "replace": "xxx"}
]}
```
**Attendu** : `error` contenant "matched nothing"

### B8. insert_after — insérer après une ligne
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "insert_after", "line": 3, "content": "import logging"}
]}
```
**Attendu** : `import logging` apparaît après la ligne 3 dans le diff

### B9. insert_before — insérer avant une ligne
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "insert_before", "line": 1, "content": "# -*- coding: utf-8 -*-"}
]}
```
**Attendu** : Le commentaire encoding apparaît AVANT la ligne 1

### B10. delete_lines — supprimer une plage
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "delete_lines", "start_line": 13, "end_line": 14}
]}
```
**Attendu** : 2 lignes supprimées dans le diff

### B11. replace_lines — remplacer une plage
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "replace_lines", "start_line": 11, "end_line": 11, "content": "def main() -> int:"}
]}
```
**Attendu** : La ligne 11 remplacée dans le diff

### B12. Batch — multiple edits atomiques
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "search_replace", "search": "HOST = \"localhost\"", "replace": "HOST = \"0.0.0.0\""},
  {"type": "search_replace", "search": "PORT = 8080", "replace": "PORT = 443"},
  {"type": "insert_after", "line": 5, "content": "# Configuration modifiée par batch edit"}
]}
```
**Attendu** : `edits_applied: 3`, les 3 changements dans le diff

### B13. Batch — échec au milieu (atomicité)
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "search_replace", "search": "import os", "replace": "import pathlib"},
  {"type": "search_replace", "search": "CETTE_LIGNE_N_EXISTE_PAS", "replace": "xxx"},
  {"type": "search_replace", "search": "import sys", "replace": "import argparse"}
]}
```
**Attendu** : `error` sur le 2ème edit. **IMPORTANT** : le fichier ne doit PAS être modifié (le 1er edit ne doit pas être persisté).

### B14. dry_run — prévisualisation sans écriture
```json
{"operation": "edit", "path": "_crashtest/editable.py", "dry_run": true, "edits": [
  {"type": "search_replace", "search": "import os", "replace": "import pathlib"}
]}
```
**Attendu** : `dry_run: true`, `changed: true`, diff affiché. Ensuite vérifier que le fichier n'a PAS changé (relire via versions — pas de nouvelle version).

### B15. Lignes hors limites
```json
{"operation": "edit", "path": "_crashtest/editable.py", "edits": [
  {"type": "insert_after", "line": 99999, "content": "impossible"}
]}
```
**Attendu** : `error` contenant "out of range"

---

## C. VERSIONING & DIFF (8 tests)

### C1. versions — historique complet
```json
{"operation": "versions", "path": "_crashtest/editable.py"}
```
**Attendu** : Plusieurs versions listées (au moins les edits précédents), ordonnées du plus récent au plus ancien

### C2. diff — entre deux versions connues
Prendre `version_a` = première version, `version_b` = dernière version depuis C1.
```json
{"operation": "diff", "path": "_crashtest/editable.py", "version_a": "<V_FIRST>", "version_b": "<V_LAST>"}
```
**Attendu** : Diff unifié non-vide, `lines_added` et `lines_removed` > 0

### C3. diff — version vs current (version_b omis)
```json
{"operation": "diff", "path": "_crashtest/editable.py", "version_a": "<V_FIRST>"}
```
**Attendu** : Diff entre la V1 et la version courante

### C4. diff — fichier identique (même version deux fois)
```json
{"operation": "diff", "path": "_crashtest/editable.py", "version_a": "<V_LAST>", "version_b": "<V_LAST>"}
```
**Attendu** : `identical: true`, `diff: null`

### C5. diff — aucune version fournie
```json
{"operation": "diff", "path": "_crashtest/editable.py"}
```
**Attendu** : `error` demandant au moins un version_id

### C6. diff — version_id invalide
```json
{"operation": "diff", "path": "_crashtest/editable.py", "version_a": "0000000000000", "version_b": "9999999999999"}
```
**Attendu** : `error` (S3 404 ou similaire)

### C7. restore — restaurer une ancienne version
```json
{"operation": "restore", "path": "_crashtest/editable.py", "version_id": "<V_FIRST>"}
```
**Attendu** : `success: true`, `new_version_id` différent de `restored_version_id`. Vérifier ensuite que le contenu est bien celui de V1.

### C8. restore — version_id manquant
```json
{"operation": "restore", "path": "_crashtest/editable.py"}
```
**Attendu** : `error` "version_id is required"

---

## D. SCOPES MULTI-TENANT (8 tests)

### D1. list — scope company
```json
{"operation": "list", "scope": "company", "max_keys": 10}
```
**Attendu** : `success: true` (même si vide)

### D2. create + edit — scope company
```json
{"operation": "create", "scope": "company", "path": "_crashtest/shared.txt", "content": "Shared file"}
```
Puis :
```json
{"operation": "edit", "scope": "company", "path": "_crashtest/shared.txt", "edits": [
  {"type": "search_replace", "search": "Shared file", "replace": "Shared file (edited)"}
]}
```
**Attendu** : Les deux opérations réussissent

### D3. delete — scope company (cleanup)
```json
{"operation": "delete", "scope": "company", "path": "_crashtest/shared.txt"}
```
**Attendu** : `success: true`

### D4. list — scope media
```json
{"operation": "list", "scope": "media", "max_keys": 10}
```
**Attendu** : `success: true`

### D5. create — scope media
```json
{"operation": "create", "scope": "media", "path": "_crashtest/media_test.txt", "content": "Media scope test"}
```
**Attendu** : `success: true`
Cleanup : delete ensuite.

### D6. list — scope datasource (lecture seule)
```json
{"operation": "list", "scope": "datasource", "datasource": "legi", "prefix": "codes/", "max_keys": 5}
```
**Attendu** : `success: true`, liste de prefixes/objets

### D7. create — scope datasource (INTERDIT)
```json
{"operation": "create", "scope": "datasource", "datasource": "legi", "path": "hack.txt", "content": "nope"}
```
**Attendu** : `error` "read-only"

### D8. edit — scope datasource (INTERDIT)
```json
{"operation": "edit", "scope": "datasource", "datasource": "legi", "path": "codes/something.json", "edits": [
  {"type": "search_replace", "search": "a", "replace": "b"}
]}
```
**Attendu** : `error` "read-only"

---

## E. SÉCURITÉ & CAS LIMITES (10 tests)

### E1. Path traversal — double dot
```json
{"operation": "create", "path": "../../../etc/passwd", "content": "hack"}
```
**Attendu** : `error` "must not contain '..'"

### E2. Path traversal — null byte
```json
{"operation": "create", "path": "test\u0000.txt", "content": "hack"}
```
**Attendu** : `error` "null bytes"

### E3. Path vide
```json
{"operation": "edit", "path": "", "edits": [{"type": "search_replace", "search": "a", "replace": "b"}]}
```
**Attendu** : `error` "path is required"

### E4. Path absent (pas de param)
```json
{"operation": "edit", "edits": [{"type": "search_replace", "search": "a", "replace": "b"}]}
```
**Attendu** : `error` "path is required"

### E5. Edits vide
```json
{"operation": "edit", "path": "_crashtest/basic.txt", "edits": []}
```
**Attendu** : `error` "must not be empty"

### E6. Edits pas un array
```json
{"operation": "edit", "path": "_crashtest/basic.txt", "edits": "not an array"}
```
**Attendu** : `error` "must be an array"

### E7. Edit sans type
```json
{"operation": "edit", "path": "_crashtest/basic.txt", "edits": [{"search": "a", "replace": "b"}]}
```
**Attendu** : `error` "missing 'type'"

### E8. Fichier inexistant — edit
```json
{"operation": "edit", "path": "_crashtest/DOES_NOT_EXIST.txt", "edits": [
  {"type": "search_replace", "search": "a", "replace": "b"}
]}
```
**Attendu** : `error` (S3 404)

### E9. Fichier inexistant — append
```json
{"operation": "append", "path": "_crashtest/DOES_NOT_EXIST.txt", "content": "hello"}
```
**Attendu** : `error` (S3 404)

### E10. Fichier inexistant — versions
```json
{"operation": "versions", "path": "_crashtest/DOES_NOT_EXIST.txt"}
```
**Attendu** : `error` ou liste vide (dépend du backend S3)

---

## F. OPÉRATIONS PHASE 2 — STUBS (2 tests)

### F1. load — pas encore implémenté
```json
{"operation": "load", "path": "_crashtest/basic.txt", "thread_id": "thread_stream_test123"}
```
**Attendu** : `error` contenant "not yet implemented" ou "Phase 2"

### F2. unload — pas encore implémenté
```json
{"operation": "unload", "path": "_crashtest/basic.txt"}
```
**Attendu** : `error` contenant "not yet implemented" ou "Phase 2"

---

## G. OPÉRATION INVALIDE (2 tests)

### G1. Opération inconnue
```json
{"operation": "foobar"}
```
**Attendu** : `error` "Invalid operation 'foobar'"

### G2. Opération absente
```json
{}
```
**Attendu** : `error` "operation is required"

---

## Z. CLEANUP

À la fin de TOUS les tests, supprimer le dossier de test :
```json
{"operation": "list", "scope": "user", "prefix": "_crashtest/"}
```
Puis pour chaque fichier listé :
```json
{"operation": "delete", "path": "<key>"}
```
Et aussi cleanup company/media si des fichiers y ont été créés.

---

## Résumé des tests

| Section | Nb tests | Description |
|---------|----------|-------------|
| A. CRUD de base | 10 | create, list, append, delete |
| B. Édition chirurgicale | 15 | search_replace, regex, insert, delete_lines, batch, dry_run |
| C. Versioning & diff | 8 | versions, diff, restore |
| D. Scopes multi-tenant | 8 | user, company, media, datasource (R/W + R/O) |
| E. Sécurité & limites | 10 | path traversal, fichiers inexistants, edits invalides |
| F. Phase 2 stubs | 2 | load, unload |
| G. Opérations invalides | 2 | foobar, vide |
| **TOTAL** | **55** | |
