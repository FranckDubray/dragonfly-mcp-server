"""
Légifrance LEGI Tool v2 - Accès aux codes juridiques français

Permet d'interroger le corpus LEGI (codes en vigueur/abrogés) via SSH.

3 opérations disponibles :

1. list_codes : Liste compacte des 77 codes en vigueur avec métadonnées (nb_articles, nb_sections)
2. get_code : Arborescence complète d'un code spécifique (depth 1-10, calcul temps réel SQL)
3. get_articles : Récupération d'articles avec texte, métadonnées, liens juridiques et fil d'Ariane

Options avancées:
- get_code accepte root_section_id pour récupérer uniquement une sous-branche.

Performance :
- list_codes : < 100ms (cache précalculé)
- get_code : < 500ms (depth ≤ 5), < 2s (depth > 5)
- get_articles : < 1s par article (avec données extraites sur disque)

Examples:
  # Liste des codes en vigueur
  {
    "tool": "legifrance_legi",
    "params": {
      "operation": "list_codes",
      "scope": "codes_en_vigueur"
    }
  }

  # Partie législative du Code du travail
  {
    "tool": "legifrance_legi",
    "params": {
      "operation": "get_code",
      "code_id": "LEGITEXT000006072050",
      "root_section_id": "LEGISCTA000006112874",
      "depth": 4
    }
  }

  # Rupture du CDI (branche ciblée)
  {
    "tool": "legifrance_legi",
    "params": {
      "operation": "get_code",
      "code_id": "LEGITEXT000006072050",
      "root_section_id": "LEGISCTA000006160710",
      "depth": 10,
      "include_articles": true
    }
  }

  # Récupération d'articles
  {
    "tool": "legifrance_legi",
    "params": {
      "operation": "get_articles",
      "article_ids": ["LEGIARTI000019071126"],
      "include_links": true,
      "include_breadcrumb": true
    }
  }
"""
from __future__ import annotations
from typing import Dict, Any

from ._legifrance_legi.api import route_request
from ._legifrance_legi import spec as _spec


def run(**params) -> Dict[str, Any]:
    operation = params.get("operation")

    if not operation:
        return {"error": "Parameter 'operation' is required"}

    clean_params = {k: v for k, v in params.items() if k != "operation"}
    return route_request(operation, **clean_params)


def spec() -> Dict[str, Any]:
    return _spec()
