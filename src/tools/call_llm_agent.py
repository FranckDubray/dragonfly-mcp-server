from typing import Any, Dict
import json
import os
from ._call_llm_agent.core import execute_agent


def run(operation: str = "run", **params) -> Dict[str, Any]:
    """
    LLM Agent avec orchestration multi-tours automatique.
    
    Gère l'enchaînement séquentiel de tools en permettant au LLM
    de voir les résultats intermédiaires et d'adapter sa stratégie.
    
    Le LLM continue d'appeler des tools jusqu'à avoir toutes les
    informations nécessaires (finish_reason="stop").
    """
    return execute_agent(**params)


def spec() -> Dict[str, Any]:
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'call_llm_agent.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)
