"""Core handlers for Ollama operations."""
from .services.local_client import OllamaLocalClient
from .services.web_search_client import OllamaWebSearchClient
from .validators import (
    validate_model_required,
    validate_prompt_required,
    validate_messages_required,
    validate_text_required,
    validate_query_required,
    validate_copy_models_required,
    validate_model_creation_required
)
from .utils import get_web_search_token, is_web_search_available


# Initialize clients
local_client = OllamaLocalClient()
web_client = OllamaWebSearchClient()


# ==========================================
# MODEL MANAGEMENT
# ==========================================

def handle_list_models(**params):
    """List available models."""
    return local_client.list_models()


def handle_get_version(**params):
    """Get Ollama version."""
    return local_client.get_version()


def handle_get_running_models(**params):
    """Get currently running models."""
    return local_client.get_running_models()


def handle_show_model(model: str = None, **params):
    """Show detailed model information."""
    validation = validate_model_required(model)
    if not validation["valid"]:
        return {"error": validation["error"]}
    
    return local_client.show_model(model)


def handle_pull_model(model: str = None, **params):
    """Pull/download a model."""
    validation = validate_model_required(model)
    if not validation["valid"]:
        return {"error": validation["error"]}
    
    return local_client.pull_model(model)


def handle_push_model(model: str = None, **params):
    """Push/upload a model."""
    validation = validate_model_required(model)
    if not validation["valid"]:
        return {"error": validation["error"]}
    
    return local_client.push_model(model)


def handle_create_model(model: str = None, modelfile: str = None, **params):
    """Create a custom model."""
    validation = validate_model_creation_required(model, modelfile)
    if not validation["valid"]:
        return {"error": validation["error"]}
    
    return local_client.create_model(model, modelfile)


def handle_copy_model(source_model: str = None, destination_model: str = None, **params):
    """Copy a model."""
    validation = validate_copy_models_required(source_model, destination_model)
    if not validation["valid"]:
        return {"error": validation["error"]}
    
    return local_client.copy_model(source_model, destination_model)


def handle_delete_model(model: str = None, **params):
    """Delete a model."""
    validation = validate_model_required(model)
    if not validation["valid"]:
        return {"error": validation["error"]}
    
    return local_client.delete_model(model)


# ==========================================
# TEXT GENERATION
# ==========================================

def handle_generate(
    model: str = None,
    prompt: str = None, 
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    timeout: int = 120,
    options: dict = None,
    **params
):
    """Generate text completion."""
    # Validate required parameters
    model_validation = validate_model_required(model)
    if not model_validation["valid"]:
        return {"error": model_validation["error"]}
    
    prompt_validation = validate_prompt_required(prompt)
    if not prompt_validation["valid"]:
        return {"error": prompt_validation["error"]}
    
    return local_client.generate(
        model=model,
        prompt=prompt,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        options=options or {}
    )


def handle_chat(
    model: str = None,
    messages: list = None,
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    timeout: int = 120,
    options: dict = None,
    **params
):
    """Chat with context."""
    # Validate required parameters
    model_validation = validate_model_required(model)
    if not model_validation["valid"]:
        return {"error": model_validation["error"]}
    
    messages_validation = validate_messages_required(messages)
    if not messages_validation["valid"]:
        return {"error": messages_validation["error"]}
    
    return local_client.chat(
        model=model,
        messages=messages,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        options=options or {}
    )


def handle_embeddings(
    model: str = None,
    text: str = None,
    timeout: int = 120,
    **params
):
    """Generate text embeddings."""
    # Validate required parameters
    model_validation = validate_model_required(model)
    if not model_validation["valid"]:
        return {"error": model_validation["error"]}
    
    text_validation = validate_text_required(text)
    if not text_validation["valid"]:
        return {"error": text_validation["error"]}
    
    return local_client.embeddings(
        model=model,
        text=text,
        timeout=timeout
    )


# ==========================================
# WEB SEARCH
# ==========================================

def handle_web_search(
    query: str = None,
    web_search_max_results: int = 5,
    timeout: int = 60,
    **params
):
    """Search the web using Ollama cloud API."""
    # Check if web search is available
    if not is_web_search_available():
        return {
            "error": "Web search not available. Set OLLAMA_WEB_SEARCH_TOKEN environment variable."
        }
    
    # Validate required parameters
    query_validation = validate_query_required(query)
    if not query_validation["valid"]:
        return {"error": query_validation["error"]}
    
    return web_client.search(
        query=query,
        max_results=web_search_max_results,
        timeout=timeout
    )


def handle_chat_with_web(
    model: str = None,
    messages: list = None,
    query: str = None,
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    timeout: int = 120,
    web_search_max_results: int = 5,
    options: dict = None,
    **params
):
    """Chat with web search context."""
    # Check if web search is available
    if not is_web_search_available():
        return {
            "error": "Web search not available. Set OLLAMA_WEB_SEARCH_TOKEN environment variable."
        }
    
    # Validate required parameters
    model_validation = validate_model_required(model)
    if not model_validation["valid"]:
        return {"error": model_validation["error"]}
    
    messages_validation = validate_messages_required(messages)
    if not messages_validation["valid"]:
        return {"error": messages_validation["error"]}
    
    query_validation = validate_query_required(query)
    if not query_validation["valid"]:
        return {"error": query_validation["error"]}
    
    # First, search the web
    search_result = web_client.search(
        query=query,
        max_results=web_search_max_results,
        timeout=60  # Fixed timeout for web search
    )
    
    if not search_result.get("success"):
        return {
            "error": f"Web search failed: {search_result.get('error', 'Unknown error')}",
            "operation": "chat_with_web"
        }
    
    # Extract search results and format them
    search_results = search_result.get("results", [])
    if not search_results:
        context = "No web search results found."
    else:
        context_parts = ["Web search results:"]
        for i, result in enumerate(search_results, 1):
            title = result.get("title", "Unknown title")
            url = result.get("url", "")
            content = result.get("content", "")[:500]  # Limit content length
            context_parts.append(f"{i}. {title}")
            context_parts.append(f"   URL: {url}")
            context_parts.append(f"   Content: {content}...")
            context_parts.append("")
        context = "\\n".join(context_parts)
    
    # Add web search context to messages
    enhanced_messages = []
    
    # Add system message with web context if no system message exists
    has_system = any(msg.get("role") == "system" for msg in messages)
    if not has_system:
        enhanced_messages.append({
            "role": "system", 
            "content": f"You are a helpful assistant. Use the following web search results to enrich your response:\\n\\n{context}"
        })
        enhanced_messages.extend(messages)
    else:
        # Enhance existing system message
        for msg in messages:
            if msg.get("role") == "system":
                enhanced_content = f"{msg['content']}\\n\\nWeb search results:\\n{context}"
                enhanced_messages.append({
                    "role": "system",
                    "content": enhanced_content
                })
            else:
                enhanced_messages.append(msg)
    
    # Now chat with enhanced context
    chat_result = local_client.chat(
        model=model,
        messages=enhanced_messages,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        options=options or {}
    )
    
    # Add web search metadata to result
    if chat_result.get("success"):
        chat_result["web_search"] = {
            "query": query,
            "results_count": len(search_results),
            "results_used": min(len(search_results), web_search_max_results)
        }
    
    return chat_result