# Worker Status — Legifrance Ingestion V1

**Date** : 2026-03-10
**Objet** : état réel du code local dans `workers/legifrance_ingestion/`.

---

## 1. Statut général

Le worker Python V1 est **amorcé et partiellement opérationnel**.

Il ne s'agit **pas encore** d'un pipeline complet bootstrap/replay/daily, mais le mode `bootstrap` commence désormais à être **réellement branché** pour LEGI et JORF minimaux.

### Ce que c'est actuellement
- un socle de worker réel,
- un writer Dragonfly testé en réel,
- une acquisition LEGI/JORF minimale testée,
- un bootstrap LEGI minimal séparé,
- un bootstrap JORF minimal séparé,
- un parseur LEGI MVP capable de produire un roundtrip minimal propre,
- un parseur JORF minimal (`texte` uniquement),
- un bridge minimal LEGI ↔ JORF via mappings.

### Ce que ce n'est pas encore
- un runner de production complet,
- un pipeline replay/daily branché,
- un parseur JORF complet,
- un bridge JORF ↔ LEGI robuste à grande échelle,
- un pipeline multi-corpus prêt pour la montée en charge.

---

## 2. Fichiers présents

### Socle
- `README.md`
- `pyproject.toml`
- `.env.example`
- `.env` local de test

### Package
- `legifrance_ingestion/__init__.py`
- `config.py`
- `main.py`
- `http_writer.py`
- `archive_reader.py`
- `validators.py`
- `state_store.py`
- `map_canonical.py`
- `manifests.py`
- `mappings.py`
- `parse_legi.py`
- `parse_jorf.py`
- `utils.py`
- `acquisition.py`
- `bootstrap_legi_minimal.py`
- `bootstrap_jorf_minimal.py`

---

## 3. Ce qui fonctionne réellement

### Backend / API Dragonfly
Validé en réel :
- write datasource ✅
- read datasource ✅
- meta/head datasource ✅
- versions datasource ✅

### Worker
Validé en réel :
- chargement config ✅
- writer HTTP Dragonfly ✅
- lecture streaming `.tar.gz` ✅
- téléchargement archive LEGI ✅
- téléchargement archive JORF ✅
- génération manifests minimaux ✅
- génération mappings minimaux ✅
- bootstrap LEGI minimal ✅
- bootstrap JORF minimal ✅
- roundtrip minimal propre sur :
  - 1 texte LEGI ✅
  - 1 article LEGI ✅
  - 1 section LEGI ✅
  - 1 texte JORF ✅
- bridge minimal LEGI ↔ JORF via mappings ✅
- `main.py --mode bootstrap --corpus legi|jorf` branché et testé ✅

---

## 4. Ce qui est encore partiel ou fragile

### `main.py`
- `bootstrap` minimal branché
- `replay` = TODO
- `daily` = TODO

### `parse_legi.py`
- premier parseur réel utile
- extraction minimale correcte pour roundtrip de base
- reste encore limité pour :
  - hiérarchies plus riches
  - robustesse complète sur tous les variants LEGI
  - filtrage métier plus fin

### `parse_jorf.py`
- MVP utile pour `texte` uniquement
- pas encore d'articles, sections, conteneurs

### `bootstrap_legi_minimal.py` / `bootstrap_jorf_minimal.py`
- vrais harnesss de test utiles
- encore pensés comme bootstrap minimal, pas comme pipeline complet de production

### `state_store.py`
- implémenté
- utilisé par `main.py` pour un état très simple
- pas encore branché à un système plus riche de reprise/checkpoint

### `acquisition.py`
- utilisé pour résoudre/télécharger l'archive bootstrap si `--archive-path` est absent
- pas encore intégré à replay/daily

### `mappings.py`
- produit une base de mappings V1
- bridge minimal LEGI ↔ JORF en place
- validité métier encore à confirmer à grande échelle

---

## 5. Résultats des tests réels

### LEGI
Archive testée :
- `LEGI_20260309-211112.tar.gz`

Publié proprement :
- `legi/texte/LEGITEXT000005616367.json` ✅
- `legi/article/LEGIARTI000006698549.json` ✅
- `legi/section/LEGISCTA000006103669.json` ✅
- manifest LEGI minimal ✅
- mappings minimaux ✅

### JORF
Archive testée :
- `JORF_20260310-002235.tar.gz`

Publié proprement :
- `jorf/texte/JORFTEXT000053642114.json` ✅
- manifest JORF minimal ✅

### Bridge minimal
Mappings observés :
- `legi_to_jorf.jsonl` ✅
- `jorf_to_legi.jsonl` ✅
- `article_to_text.jsonl` ✅
- `text_to_articles.jsonl` ✅
- `section_to_text.jsonl` ✅

---

## 6. Commandes réellement testables

### Bootstrap LEGI auto ou manuel
```bash
python3 -m legifrance_ingestion.main --mode bootstrap --corpus legi
python3 -m legifrance_ingestion.main --mode bootstrap --corpus legi --archive-path /path/to/archive.tar.gz
```

### Bootstrap JORF auto ou manuel
```bash
python3 -m legifrance_ingestion.main --mode bootstrap --corpus jorf
python3 -m legifrance_ingestion.main --mode bootstrap --corpus jorf --archive-path /path/to/archive.tar.gz
```

---

## 7. Permissions nécessaires

Pour la clé d'ingestion datasource, il faut au minimum :
- `storage.write`
- `datasource.write`

Et utilement aussi :
- `storage.read`

---

## 8. Priorité immédiate

### À faire maintenant
1. stabiliser les formats réels de `_meta/manifests/` et `_meta/mappings/`
2. commencer le premier tool réel de consultation (`load_object` ou `resolve_id`)
3. réfléchir à la consommation des mappings par les tools V1

### Ensuite seulement
4. brancher `replay`
5. brancher `daily`
6. renforcer le bridge documentaire
7. élargir JORF si nécessaire

---

## 9. Règle de lecture pour un autre LLM ou dev

Le bon état mental est :

> socle technique validé, tuyau Dragonfly validé, bootstrap LEGI et JORF minimaux validés, bridge minimal LEGI ↔ JORF validé, mais pipeline complet et tools réels encore à construire.
