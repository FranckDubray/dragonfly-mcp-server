IMPÉRATIF : Réponds UNIQUEMENT en français. Génère un rapport Markdown Top 10 IA/LLM À PARTIR des données fournies (ne fabrique rien).

Règles importantes
- NE JAMAIS traduire ni modifier les URL. Les URL doivent rester strictement identiques.
- Ne pas traduire les noms propres, noms de modèles (GPT, Claude, Llama…), noms d’organisations, ni les domaines/sources.
- Sortie 100% Markdown, sans JSON, sans code fences.
- Si un champ est manquant, omets-le proprement (n’invente pas).

Entrées
- TOP10 JSON: {TOP10}
  - Tableau d’objets (rank, title, url, source, published_at, why, category, coverage_count)
- VALIDATION: {VALIDATION}
  - Objet {"score": 0..10, "feedback": "…"}

Objectif
- Produire un rapport concis en français, lisible, avec un Top 10 classé.
- Conserver les URL EXACTES; ne pas traduire ni altérer les domaines.

Structure attendue (Markdown)
# Rapport IA/LLM — Top 10

## Qualité de la curation
- Score: {VALIDATION.score}/10
- Synthèse: {VALIDATION.feedback}

## Top 10 (dernières ~72h)
(Numérote de 1 à 10, en conservant l’ordre fourni; si <10, affiche ce qui existe.)

1. [Titre en français (adapter si besoin, sans altérer les noms propres)](URL-STRICTE)
   - Source: domaine/publisher (inchangé)
   - Date (UTC): published_at (format d’origine)
   - Catégorie: category
   - Couverture: coverage_count sources
   - Pourquoi c’est notable: reformule en 1–2 phrases en français à partir de "why" (ne traduis pas les noms propres, garde les acronymes)

2. …

Notes
- Ne cherche pas à traduire les URL ni à les reformater.
- Reste factuel; n’ajoute aucune histoire non présente dans TOP10.
- Si des champs sont absents dans TOP10 (ex: image_url), n’en parle pas.
