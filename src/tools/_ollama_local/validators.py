"""Validators for Ollama operations."""
from typing import Dict, Any, List


def validate_model_required(model: str) -> Dict[str, Any]:
    """Validate that model parameter is provided."""
    if not model or not model.strip():
        return {"valid": False, "error": "Parameter 'model' is required"}
    return {"valid": True, "model": model.strip()}


def validate_prompt_required(prompt: str) -> Dict[str, Any]:
    """Validate that prompt parameter is provided."""
    if not prompt or not prompt.strip():
        return {"valid": False, "error": "Parameter 'prompt' is required"}
    return {"valid": True, "prompt": prompt.strip()}


def validate_text_required(text: str) -> Dict[str, Any]:
    """Validate that text parameter is provided."""
    if not text or not text.strip():
        return {"valid": False, "error": "Parameter 'text' is required"}
    return {"valid": True, "text": text.strip()}


def validate_query_required(query: str) -> Dict[str, Any]:
    """Validate that query parameter is provided."""
    if not query or not query.strip():
        return {"valid": False, "error": "Parameter 'query' is required"}
    return {"valid": True, "query": query.strip()}


def validate_messages_required(messages: List[Dict]) -> Dict[str, Any]:
    """Validate that messages parameter is provided and well-formed."""
    if not messages:
        return {"valid": False, "error": "Parameter 'messages' is required"}
    
    if not isinstance(messages, list):
        return {"valid": False, "error": "Parameter 'messages' must be a list"}
    
    for i, message in enumerate(messages):
        if not isinstance(message, dict):
            return {"valid": False, "error": f"Message {i} must be a dict"}
        
        if "role" not in message:
            return {"valid": False, "error": f"Message {i} missing 'role' field"}
        
        if "content" not in message:
            return {"valid": False, "error": f"Message {i} missing 'content' field"}
        
        role = message["role"]
        if role not in ["system", "user", "assistant"]:
            return {"valid": False, "error": f"Message {i} invalid role '{role}'. Must be: system, user, assistant"}
        
        content = message["content"]
        if not isinstance(content, str) or not content.strip():
            return {"valid": False, "error": f"Message {i} content must be non-empty string"}
    
    return {"valid": True, "messages": messages}


def validate_copy_models_required(source_model: str, destination_model: str) -> Dict[str, Any]:
    """Validate that both source and destination models are provided."""
    if not source_model or not source_model.strip():
        return {"valid": False, "error": "Parameter 'source_model' is required"}
    
    if not destination_model or not destination_model.strip():
        return {"valid": False, "error": "Parameter 'destination_model' is required"}
    
    if source_model.strip() == destination_model.strip():
        return {"valid": False, "error": "Source and destination models must be different"}
    
    return {
        "valid": True, 
        "source_model": source_model.strip(),
        "destination_model": destination_model.strip()
    }


def validate_model_creation_required(model: str, modelfile: str) -> Dict[str, Any]:
    """Validate that model name and modelfile are provided."""
    if not model or not model.strip():
        return {"valid": False, "error": "Parameter 'model' is required"}
    
    if not modelfile or not modelfile.strip():
        return {"valid": False, "error": "Parameter 'modelfile' is required"}
    
    return {
        "valid": True,
        "model": model.strip(),
        "modelfile": modelfile.strip()
    }