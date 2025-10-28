Cutoff: {FROM_ISO}
Now: {NOW_ISO}

PAGES (JSON d’objets chunkés): {SCRAPES_JSON}
Chaque entrée:
- "url": string (page de blog officielle)
- "offset": integer (octet de départ du chunk dans la page)
- "content": string (texte brut extrait sur ce chunk)

Tâche
- À partir de ces PAGES chunkées (toutes sources confondues), produis le Top ≤10 actus IA/LLM depuis {FROM_ISO}.
- Regrouper les chunks par URL (reconstituer le contenu logique par page), ignorer les doublons évidents.
- Dédupliquer les histoires (même sujet → 1 entrée), choisir l’URL la plus canonique (ne pas modifier les URLs).
- Classer selon: (1) intérêt/impact, (2) diversité des éditeurs, (3) équilibre des thèmes (model/product/research/governance/safety/infra/tools/community).
- N’inventer aucune info qui ne figure pas dans les PAGES; rester strict.

Sortie STRICT JSON ONLY (pas de prose, pas de code fences). Tableau d’objets:
- "title": string
- "url": string (URL stricte de la page la plus canonique)
- "source": string (domaine/publisher)
- "published_at": string (si identifiable; sinon champ vide "")
- "why": string (1–2 phrases FR synthétisant l’importance à partir du contenu)
- "category": "model"|"product"|"research"|"governance"|"safety"|"infra"|"tools"|"community"
- "coverage_count": integer (approximation des recoupements PAGES/éditeurs)
