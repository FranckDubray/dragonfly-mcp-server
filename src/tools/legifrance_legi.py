"""
Légifrance LEGI Tool - Accès aux codes juridiques français

Permet d'interroger le corpus LEGI (codes en vigueur/abrogés) via SSH.
Récupère l'arborescence des codes et le contenu des articles avec métadonnées,
liens juridiques et fil d'Ariane.

Utilise des données précalculées côté serveur pour des performances optimales
(< 100ms pour get_summary grâce au cache).

Examples:
  # Liste des codes en vigueur (depth=2 : codes + livres)
  {
    "tool": "legifrance_legi",
    "params": {
      "operation": "get_summary",
      "scope": "codes_en_vigueur",
      "depth": 2,
      "limit": 10
    }
  }
  
  # Arborescence complète du Code civil (depth=5 : jusqu'aux articles)
  {
    "tool": "legifrance_legi",
    "params": {
      "operation": "get_summary",
      "scope": "codes_en_vigueur",
      "depth": 5,
      "limit": 1
    }
  }
  
  # Récupérer des articles spécifiques
  {
    "tool": "legifrance_legi",
    "params": {
      "operation": "get_article",
      "article_ids": ["LEGIARTI000044072567", "LEGIARTI000044072568"],
      "include_links": true,
      "include_breadcrumb": true
    }
  }
  
  # Article à une date donnée (version historique)
  {
    "tool": "legifrance_legi",
    "params": {
      "operation": "get_article",
      "article_ids": ["LEGIARTI000044072567"],
      "date": "2020-01-15"
    }
  }
"""
from __future__ import annotations
from typing import Dict, Any

from ._legifrance_legi.api import route_request
from ._legifrance_legi import spec as _spec


def run(**params) -> Dict[str, Any]:
    """Execute LEGI operation via SSH.
    
    Args:
        **params: Operation parameters (operation, scope, depth, article_ids, etc.)
        
    Returns:
        Operation result (codes summary or articles data)
    """
    operation = params.get("operation")
    
    if not operation:
        return {"error": "Parameter 'operation' is required"}
    
    # Remove operation from params to avoid duplicate arguments
    clean_params = {k: v for k, v in params.items() if k != "operation"}
    
    # Route to appropriate handler
    return route_request(operation, **clean_params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
