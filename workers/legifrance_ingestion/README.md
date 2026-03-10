# Legifrance Ingestion Worker V1

Worker Python d’ingestion DILA → API Dragonfly → S3 pour la datasource `legifrance`.

## Objectif V1
- ingérer **LEGI** :
  - `texte`
  - `article`
  - `section`
- ingérer **JORF** :
  - `texte` uniquement
- publier les JSON canoniques dans :
  - `scope=datasource`
  - `datasource=legifrance`

## Modes
- `bootstrap` : ingestion initiale
- `replay` : rejeu historique incrémental
- `daily` : incrémental quotidien

## Commandes prévues
```bash
python -m legifrance_ingestion.main --mode bootstrap --corpus legi
python -m legifrance_ingestion.main --mode replay --corpus legi
python -m legifrance_ingestion.main --mode daily --corpus jorf
```

## Variables d’environnement
Voir `.env.example`

## Architecture
Le worker :
1. découvre et télécharge les archives DILA
2. lit les `.tar.gz` en streaming
3. parse les XML
4. mappe vers le JSON canonique
5. publie via l’API Dragonfly
6. génère manifests, mappings et logs `_meta/`

## Non-objectifs V1
- pas de jurisprudence
- pas de KALI
- pas de NLP
- pas de moteur externe
- pas de OCR circulaires
