Cutoff: {FROM_ISO}
Now: {NOW_ISO}

ITEMS (bundle JSON par source: news, reddit, arxiv, sonar):
{ITEMS}

CRITIQUE (optionnel, du passage précédent):
{CRITIQUE}

Tâche
- Voici tout ce qui a été remonté en collecte de sources (toutes sections confondues).
- Produis le Top 10 des infos (fusionne, puis déduplique).
- EXCLURE tout item qui n’est pas principalement lié à l’IA/LLM ; REJETER les actus purement financières/générales (même importantes) sans lien direct avec l’IA/LLM.
- Choisis l’URL la plus canonique/primary par histoire.

Pondérations & contraintes (applique strictement)
- Score = 0,5 * importance marché & utilisateur + 0,3 * couverture (sources distinctes, normalisée) + 0,2 * bonus diversité.
- Bonus diversité: +1 si la source provient de SONAR ; +0,5 si arXiv ou blog officiel d’organisation/lab ; 0 sinon.
- Pénalité domaine: −1 par occurrence au‑delà de 2 items pour un même domaine (cap = 2 items/domain dans la liste finale).
- Quotas minimum: ≥ 3 items provenant du set SONAR (si crédibles et dans la fenêtre), ≥ 1 item arXiv (si disponible et crédible).
- Équilibrage: viser un mix couvrant models/products/research/governance/safety/infra/tools/community.

Contraintes de sortie
- STRICT JSON ONLY (pas de texte avant/après, pas de code fences).
- Réponse = tableau JSON (≤ 10 objets) déjà trié par rank.
- Chaque objet contient: "rank" (1..10), "title", "url", "source", "published_at" (UTC Z), "why" (1–2 lignes), "category" (model|product|research|governance|safety|infra|tools|community), "coverage_count" (entier).
- Ne garder que les éléments ≥ {FROM_ISO}.
- Respecter le cap par domaine (≤ 2) et les quotas SONAR/ArXiv, sinon remplacer par la meilleure alternative disponible.
