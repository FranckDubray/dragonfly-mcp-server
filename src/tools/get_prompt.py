"""
Tool get_prompt - Recupere des prompts systeme depuis SQLite.

Wrapper optimise autour de sqlite_db pour simplifier le chargement des prompts
par le Master Orchestrator.
"""

import json
import os


def spec():
    """Load canonical JSON spec."""
    here = os.path.dirname(__file__)
    spec_path = os.path.join(here, '..', 'tool_specs', 'get_prompt.json')
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run(agent_type: str, domain: str = "legal", version: str = "v1") -> dict:
    """
    Recupere un prompt depuis la base SQLite prompts.db.
    
    Args:
        agent_type: Type d'agent (planner, researcher, evaluator, etc.)
        domain: Domaine metier (legal, medical, financial, etc.)
        version: Version du prompt (v1, v2, experimental, etc.)
    
    Returns:
        {"prompt": "..."}  OU  {"error": "..."}
    """
    # Import du tool sqlite_db
    try:
        import sys
        import os
        # Ajouter src/ au path si necessaire
        src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        from tools import sqlite_db
    except ImportError as e:
        return {"error": f"Failed to import sqlite_db: {e}"}
    
    # Construire la query SQL
    query = """
        SELECT prompt, description, tags, updated_at
        FROM prompts
        WHERE domain = ?
          AND agent_type = ?
          AND version = ?
          AND is_active = 1
        LIMIT 1
    """
    
    # Executer la query
    try:
        result = sqlite_db.run(
            operation="query",
            db="prompts.db",
            query=query,
            params=[domain, agent_type, version]
        )
        
        if "error" in result:
            return {"error": f"SQLite error: {result['error']}"}
        
        rows = result.get("rows", [])
        
        if not rows:
            # Prompt non trouve - lister les disponibles
            list_query = "SELECT agent_type, version FROM prompts WHERE domain = ? AND is_active = 1"
            list_result = sqlite_db.run(
                operation="query",
                db="prompts.db",
                query=list_query,
                params=[domain]
            )
            available = list_result.get("rows", [])
            
            return {
                "error": f"Prompt not found: domain={domain}, agent_type={agent_type}, version={version}",
                "available": available,
                "hint": "Check domain, agent_type, and version parameters"
            }
        
        # Retourner le prompt
        row = rows[0]
        return {
            "prompt": row["prompt"],
            "metadata": {
                "domain": domain,
                "agent_type": agent_type,
                "version": version,
                "description": row.get("description"),
                "tags": row.get("tags"),
                "updated_at": row.get("updated_at")
            }
        }
    
    except Exception as e:
        return {"error": f"Failed to retrieve prompt: {e}"}
