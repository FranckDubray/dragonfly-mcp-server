# Worker Status — Legifrance Ingestion V1

**Date** : 2026-03-10
**Objet** : état réel du code local dans `workers/legifrance_ingestion/`.

---

## 1. Statut général

Le worker Python V1 est **amorcé et partiellement opérationnel**.

Il ne s'agit **pas encore** d'un pipeline complet bootstrap/replay/daily entièrement branché dans `main.py`.

### Ce que c'est actuellement
- un socle de worker réel,
- un writer Dragonfly testé en réel,
- une acquisition LEGI minimale testée,
- un bootstrap LEGI minimal séparé,
- un parseur LEGI MVP désormais capable de produire un roundtrip minimal propre,
- un futur parseur JORF encore à implémenter.

### Ce que ce n'est pas encore
- un runner de production complet,
- un pipeline daily entièrement branché,
- un parseur JORF V1,
- un bridge JORF ↔ LEGI stabilisé,
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
- `utils.py`
- `acquisition.py`
- `bootstrap_legi_minimal.py`

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
- génération manifests minimaux ✅
- génération mappings minimaux ✅
- bootstrap LEGI minimal ✅
- roundtrip minimal propre sur :
  - 1 texte LEGI ✅
  - 1 article LEGI ✅
  - 1 section LEGI ✅

---

## 4. Ce qui est encore partiel ou fragile

### `main.py`
- expose `--mode bootstrap|replay|daily`
- mais les vraies branches restent essentiellement des `TODO`
- **ne pas considérer `main.py` comme pipeline complet fonctionnel**

### `parse_legi.py`
- premier parseur réel utile
- extraction minimale désormais correcte pour un roundtrip de base
- reste encore limité pour :
  - hiérarchies plus riches
  - robustesse complète sur tous les variants LEGI
  - filtrage métier plus fin

### `bootstrap_legi_minimal.py`
- c'est actuellement le **vrai harness de test utile**
- beaucoup plus réel que `main.py` pour les tests LEGI

### `state_store.py`
- implémenté
- pas encore réellement branché au flow principal

### `acquisition.py`
- implémenté minimalement
- sert déjà à télécharger une archive LEGI
- pas encore intégré dans un pipeline orchestré complet via `main.py`

### `mappings.py`
- produit une base de mappings V1
- validité métier encore à confirmer à grande échelle

---

## 5. Résultats du test LEGI minimal

### Archive testée
- `LEGI_20260309-211112.tar.gz`

### Ce qui a été publié proprement
- `legi/texte/LEGITEXT000005616367.json` ✅
- `legi/article/LEGIARTI000006698549.json` ✅
- `legi/section/LEGISCTA000006103669.json` ✅
- manifest LEGI minimal ✅
- mappings minimaux ✅

### Mappings observés
- `article_to_text.jsonl`
- `text_to_articles.jsonl`
- `legi_to_jorf.jsonl`
- `section_to_text.jsonl`

### Conclusion
Le roundtrip LEGI minimal est maintenant **fonctionnel**.

---

## 6. Commandes / usages réellement testables

### Écriture Dragonfly de test
Le writer est testable et validé avec une vraie API key.

### Bootstrap LEGI minimal
Le module suivant est aujourd'hui la meilleure base de test :
- `legifrance_ingestion.bootstrap_legi_minimal`

### Acquisition LEGI
Le module suivant est déjà exploitable :
- `legifrance_ingestion.acquisition`

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
1. implémenter `parse_jorf.py`
2. créer un `bootstrap_jorf_minimal.py`
3. tester un roundtrip JORF `texte` uniquement
4. commencer le bridge minimal `JORF ↔ LEGI`

### Ensuite seulement
5. brancher davantage le flux dans `main.py`
6. stabiliser la couche JORF V1
7. préparer le bridge documentaire plus robuste

---

## 9. Règle de lecture pour un autre LLM ou dev

Si tu reprends ce worker, ne pars pas du principe que :
- `main.py` est complet,
- `bootstrap/replay/daily` sont déjà branchés,
- JORF est déjà implémenté,
- les mappings sont déjà métierment fiables à grande échelle.

Le bon état mental est :

> socle technique validé, tuyau Dragonfly validé, bootstrap LEGI minimal validé, JORF minimal encore à coder.
