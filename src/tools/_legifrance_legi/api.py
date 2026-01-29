"""API routing layer for Légifrance LEGI operations v2."""
from __future__ import annotations
from typing import Dict, Any
import logging

from .validators import (
    validate_operation,
    validate_scope,
    validate_nature,
    validate_code_id,
    validate_root_section_id,
    validate_depth,
    validate_article_ids,
    validate_date
)
from .core import list_codes, get_code, get_articles

LOG = logging.getLogger(__name__)


def route_request(operation: str, **params) -> Dict[str, Any]:
    """Route request to appropriate handler."""
    op_validation = validate_operation(operation)
    if not op_validation["valid"]:
        LOG.warning(f"Invalid operation: {op_validation['error']}")
        return {"error": op_validation["error"]}

    operation = op_validation["operation"]

    if operation == "list_codes":
        return handle_list_codes(**params)

    if operation == "get_code":
        return handle_get_code(**params)

    if operation == "get_articles":
        return handle_get_articles(**params)

    return {"error": f"Unknown operation: {operation}"}


def handle_list_codes(**params) -> Dict[str, Any]:
    scope_validation = validate_scope(params.get("scope"))
    if not scope_validation["valid"]:
        LOG.warning(f"Invalid scope: {scope_validation['error']}")
        return {"error": scope_validation["error"]}

    nature_validation = validate_nature(params.get("nature"))
    if not nature_validation["valid"]:
        LOG.warning(f"Invalid nature: {nature_validation['error']}")
        return {"error": nature_validation["error"]}

    scope = scope_validation["scope"]
    nature = nature_validation["nature"]
    
    LOG.info(f"📋 list_codes: scope={scope}, nature={nature}")
    result = list_codes(scope=scope, nature=nature)
    
    # Log success avec détails (v3.1)
    if "error" not in result:
        total = result.get("total", 0)
        LOG.info(f"✅ list_codes returned {total} codes")
    
    return result


def handle_get_code(**params) -> Dict[str, Any]:
    code_id_validation = validate_code_id(params.get("code_id"))
    if not code_id_validation["valid"]:
        LOG.warning(f"Invalid code_id: {code_id_validation['error']}")
        return {"error": code_id_validation["error"]}

    code_id = code_id_validation["code_id"]

    root_validation = validate_root_section_id(params.get("root_section_id"))
    if not root_validation["valid"]:
        LOG.warning(f"Invalid root_section_id: {root_validation['error']}")
        return {"error": root_validation["error"]}

    root_section_id = root_validation["root_section_id"]

    depth_validation = validate_depth(params.get("depth"))
    if not depth_validation["valid"]:
        LOG.warning(f"Invalid depth: {depth_validation['error']}")
        return {"error": depth_validation["error"]}

    depth = depth_validation["depth"]
    include_articles = params.get("include_articles", False)

    # --- SMART CAP VOLUMÉTRIQUE ---
    # Protection contre la saturation du contexte :
    # Si l'IA demande un Code entier (pas de root_section_id) avec une profondeur trop élevée,
    # on bride la requête pour forcer une exploration itérative.
    if root_section_id is None and depth > 3:
        LOG.warning(f"🛡️ Smart Cap activé : depth {depth} -> 3 pour requête globale sur {code_id}")
        depth = 3
        include_articles = False
    # ------------------------------

    LOG.info(
        f"📖 get_code: code_id={code_id}, depth={depth}, include_articles={include_articles}, root_section_id={root_section_id}"
    )

    result = get_code(
        code_id=code_id,
        depth=depth,
        include_articles=include_articles,
        root_section_id=root_section_id
    )
    
    # Log success avec titre si disponible (v3.1)
    if "error" not in result:
        code_titre = result.get("code_titre", "")
        from_cache = result.get("from_cache", False)
        cache_status = "cache ⚡" if from_cache else "dynamic 🐢"
        
        if code_titre:
            LOG.info(f"✅ get_code: {code_titre} ({code_id}) [{cache_status}]")
        else:
            LOG.info(f"✅ get_code: {code_id} succeeded [{cache_status}]")
    
    return result


def handle_get_articles(**params) -> Dict[str, Any]:
    ids_validation = validate_article_ids(params.get("article_ids"))
    if not ids_validation["valid"]:
        LOG.warning(f"Invalid article_ids: {ids_validation['error']}")
        return {"error": ids_validation["error"]}

    article_ids = ids_validation["article_ids"]

    date_validation = validate_date(params.get("date"))
    if not date_validation["valid"]:
        LOG.warning(f"Invalid date: {date_validation['error']}")
        return {"error": date_validation["error"]}

    date = date_validation["date"]

    include_links = params.get("include_links", True)
    include_breadcrumb = params.get("include_breadcrumb", True)

    LOG.info(
        f"📄 get_articles: {len(article_ids)} articles, date={date}, links={include_links}, breadcrumb={include_breadcrumb}"
    )

    result = get_articles(
        article_ids=article_ids,
        date=date,
        include_links=include_links,
        include_breadcrumb=include_breadcrumb
    )
    
    # Log success avec détails (v3.1)
    if "error" not in result:
        total = result.get("total", 0)
        LOG.info(f"✅ get_articles returned {total} articles")
    
    return result
