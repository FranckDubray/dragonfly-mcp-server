"""Model validation via Platform API with caching."""

from typing import Dict, List, Optional, Any
import requests
import logging
import time

LOG = logging.getLogger(__name__)

# Cache (in-memory)
_MODEL_CACHE: Dict[str, Any] = {
    "models": None,
    "timestamp": 0,
    "ttl": 300  # 5 minutes
}


def fetch_models(api_base: str, token: str) -> List[Dict[str, Any]]:
    """Fetch available models from Platform API with caching.
    
    Returns:
        List of model dicts with 'id' and 'context_length' fields
    
    Raises:
        Exception if API call fails
    """
    now = time.time()
    
    # Check cache
    if _MODEL_CACHE["models"] and (now - _MODEL_CACHE["timestamp"]) < _MODEL_CACHE["ttl"]:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug("Using cached models list")
        return _MODEL_CACHE["models"]
    
    # Fetch from API
    url = f"{api_base}/models"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"Fetching models from: {url}")
        
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # Parse response (List of hosts, each containing 'models' list)
        models = []
        if isinstance(data, list):
            for host in data:
                if isinstance(host, dict):
                    host_models = host.get("models", [])
                    if isinstance(host_models, list):
                        models.extend(host_models)
        elif isinstance(data, dict):
            # Fallback for older/other format
            models = data.get("data", [])
            if not isinstance(models, list):
                models = data.get("models", [])
        
        if not isinstance(models, list):
             # Should not happen if logic above is correct, but safe fallback
             models = []

        # Update cache
        _MODEL_CACHE["models"] = models
        _MODEL_CACHE["timestamp"] = now
        
        LOG.info(f"Fetched {len(models)} models from Platform API")
        return models
    
    except Exception as e:
        LOG.error(f"Failed to fetch models: {e}")
        raise


def validate_model(model_name: str, api_base: str, token: str) -> Optional[Dict[str, Any]]:
    """Validate that model exists and is available.
    
    Returns:
        None if valid, error dict if invalid
    """
    try:
        models = fetch_models(api_base, token)
    except Exception as e:
        return {
            "error": f"Failed to validate model (API error): {e}",
            "hint": "Check AI_PORTAL_TOKEN and network connectivity"
        }
    
    # Check if model exists
    # Models have 'id' (e.g. 'qwen3-next:80b') or 'name'
    model_ids = []
    for m in models:
        if isinstance(m, dict):
            if m.get("id"): model_ids.append(str(m.get("id")))
            if m.get("name"): model_ids.append(str(m.get("name")))
    
    if str(model_name) not in model_ids:
        # Fuzzy match or simple list
        return {
            "error": f"Model '{model_name}' not found",
            "available_models": sorted(list(set(model_ids)))[:10],  # Show first 10 unique
            "hint": f"Use one of the available models. Total: {len(model_ids)}"
        }
    
    return None


def get_model_context_length(model_name: str, api_base: str, token: str) -> Optional[int]:
    """Get context length for a model.
    
    Returns:
        Context length in tokens, or None if not found
    """
    try:
        models = fetch_models(api_base, token)
    except Exception:
        return None
    
    for m in models:
        if isinstance(m, dict):
            # Check id or name
            mid = str(m.get("id", ""))
            mname = str(m.get("name", ""))
            
            if mid == str(model_name) or mname == str(model_name):
                # Try specific fields
                ctx = m.get("context_window") or m.get("context_length") or m.get("max_token")
                if isinstance(ctx, int) and ctx > 0:
                    return ctx
                return 100000 # Default if found but no context info
    
    return None
