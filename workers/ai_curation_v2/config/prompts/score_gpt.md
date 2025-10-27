Cutoff: {FROM_ISO}
Now: {NOW_ISO}

ITEMS (bundle JSON par source: news, reddit, arxiv, sonar):
{ITEMS}

CRITIQUE (optionnel, du passage précédent):
{CRITIQUE}

Tâche
- Voici tout ce qui a été remonté en collecte de sources (toutes sections confondues).
- Produis le Top 10 des infos (fusionne, puis déduplique).
- Classe selon: (1) nombre de sources distinctes par info, (2) importance marché & utilisateur, (3) niveau de buzz (communauté/médias).
- Choisis l’URL la plus canonique/primary par histoire.

Contraintes de sortie
- STRICT JSON ONLY (pas de texte avant/après, pas de code fences).
- Réponse = tableau JSON de max 10 objets.
- Chaque objet contient: "rank" (1..10), "title", "url", "source", "published_at" (UTC Z), "why" (1–2 lignes), "category" (model|product|research|governance|safety|infra|tools|community), et "coverage_count" (entier, estimation du nb de sources distinctes).
- Ne garder que les éléments >= {FROM_ISO}.
- Si beaucoup de candidats, couvre équitablement les sections (news/reddit/arxiv/sonar) avant de classer.
