"""Core handlers for Ollama operations."""
import base64
import os
from pathlib import Path
from typing import Dict, Any, Tuple
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

# Image handling (same logic as call_llm)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DEFAULT_DOCS = str(PROJECT_ROOT / "docs")
DOCS_ABS_ROOT = os.getenv("DOCS_ABS_ROOT", DEFAULT_DOCS)


def _to_abs_docs(path: str) -> Tuple[str | None, Dict[str, Any]]:
    """Normalize image path under DOCS_ABS_ROOT."""
    diag: Dict[str, Any] = {
        "input": path,
        "docs_abs_root": DOCS_ABS_ROOT,
        "is_abs": False,
        "resolved": None,
        "under_allowed": False,
    }
    try:
        if not isinstance(path, str) or not path.strip():
            diag["reason"] = "empty_or_invalid_path"
            return None, diag
        p = os.path.normpath(path.strip())
        root = os.path.normpath(DOCS_ABS_ROOT)
        
        if os.path.isabs(p):
            diag["is_abs"] = True
            if p == root or p.startswith(root + os.sep):
                full_abs = p
            else:
                diag["reason"] = "abs_not_under_docs_root"
                diag["resolved"] = p
                return None, diag
        else:
            if p == "docs" or p.startswith("docs" + os.sep):
                suffix = p[4:].lstrip(os.sep)
                full_abs = os.path.normpath(os.path.join(root, suffix)) if suffix else root
            else:
                full_abs = os.path.normpath(os.path.join(root, p))
        
        diag["resolved"] = full_abs
        under = (full_abs == root) or full_abs.startswith(root + os.sep)
        diag["under_allowed"] = under
        if not under:
            diag["reason"] = "not_under_allowed_root"
            return None, diag
        return full_abs, diag
    except Exception as e:
        diag["reason"] = "exception"
        diag["exception"] = str(e)
        return None, diag


def _file_to_base64(path: str) -> Tuple[str | None, Dict[str, Any]]:
    """Convert image file to base64 string."""
    diag: Dict[str, Any] = {"path": path}
    try:
        full_abs, diag_map = _to_abs_docs(path)
        diag.update({"map": diag_map})
        if not full_abs:
            diag["reason"] = "mapping_failed"
            return None, diag
        diag["full_abs"] = full_abs
        
        try:
            max_bytes = int(os.getenv("LLM_MAX_IMAGE_FILE_BYTES", "5000000"))
        except Exception:
            max_bytes = 5000000
        diag["max_bytes"] = max_bytes
        
        exists = os.path.exists(full_abs)
        diag["exists"] = exists
        if not exists:
            diag["reason"] = "file_not_found"
            return None, diag
            
        try:
            size = os.path.getsize(full_abs)
        except Exception as e:
            diag["reason"] = "getsize_failed"
            diag["exception"] = str(e)
            return None, diag
        diag["size"] = size
        if size > max_bytes:
            diag["reason"] = "too_large"
            return None, diag
            
        try:
            with open(full_abs, "rb") as f:
                data = f.read()
        except Exception as e:
            diag["reason"] = "open_failed"
            diag["exception"] = str(e)
            return None, diag
            
        try:
            b64 = base64.b64encode(data).decode("ascii")
        except Exception as e:
            diag["reason"] = "base64_encode_failed"
            diag["exception"] = str(e)
            return None, diag
            
        diag["ok"] = True
        return b64, diag
    except Exception as e:
        diag["reason"] = "unexpected_exception"
        diag["exception"] = str(e)
        return None, diag


def _process_images(image_urls: list = None, image_files: list = None) -> Tuple[list, Dict]:
    """Process image URLs and files into base64 list for Ollama."""
    images_b64 = []
    debug_info = {"files": [], "urls": []}
    
    image_urls = image_urls or []
    image_files = image_files or []
    
    # Limit check
    try:
        max_img = int(os.getenv("LLM_MAX_IMAGE_COUNT", "4"))
    except Exception:
        max_img = 4
    total_imgs = len(image_urls) + len(image_files)
    if total_imgs > max_img:
        return None, {"error": f"Too many images: {total_imgs} > {max_img} (LLM_MAX_IMAGE_COUNT)."}
    
    # Process URLs (download and convert to base64)
    for url in image_urls:
        if isinstance(url, str) and url.strip():
            # For now, we don't download URLs - Ollama needs base64
            # User should provide local files or we implement download
            debug_info["urls"].append({"url": url, "skipped": True, "reason": "URL download not implemented yet"})
    
    # Process local files
    for path in image_files:
        if not isinstance(path, str) or not path.strip():
            debug_info["files"].append({"path": path, "skipped": True, "reason": "empty_or_invalid"})
            continue
        b64, diag = _file_to_base64(path)
        if not b64:
            return None, {"error": f"Image file error: {path}", "diag": diag}
        images_b64.append(b64)
        debug_info["files"].append({"path": path, "ok": True, "diag": diag})
    
    return images_b64, debug_info


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
    image_urls: list = None,
    image_files: list = None,
    **params
):
    """Generate text completion with optional image support."""
    # Validate required parameters
    model_validation = validate_model_required(model)
    if not model_validation["valid"]:
        return {"error": model_validation["error"]}
    
    prompt_validation = validate_prompt_required(prompt)
    if not prompt_validation["valid"]:
        return {"error": prompt_validation["error"]}
    
    # Process images if provided
    images_b64 = None
    if image_urls or image_files:
        images_b64, result = _process_images(image_urls, image_files)
        if images_b64 is None:
            return result  # Error
    
    return local_client.generate(
        model=model,
        prompt=prompt,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        options=options or {},
        images=images_b64
    )


def handle_chat(
    model: str = None,
    messages: list = None,
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    timeout: int = 120,
    options: dict = None,
    image_urls: list = None,
    image_files: list = None,
    **params
):
    """Chat with context.
    
    Note: For image support, use 'generate' operation instead.
    /api/chat endpoint doesn't support images in Ollama.
    """
    # Validate required parameters
    model_validation = validate_model_required(model)
    if not model_validation["valid"]:
        return {"error": model_validation["error"]}
    
    messages_validation = validate_messages_required(messages)
    if not messages_validation["valid"]:
        return {"error": messages_validation["error"]}
    
    # Reject images with clear error message
    if image_urls or image_files:
        return {
            "error": "Images not supported with 'chat' operation. Use 'generate' instead.",
            "suggestion": "Call ollama_local with operation='generate' + prompt + image_files for image analysis",
            "example": {
                "operation": "generate",
                "model": "llava:13b",
                "prompt": "Describe this image",
                "image_files": ["docs/your_image.png"]
            }
        }
    
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
        context = "\n".join(context_parts)
    
    # Add web search context to messages
    enhanced_messages = []
    
    # Add system message with web context if no system message exists
    has_system = any(msg.get("role") == "system" for msg in messages)
    if not has_system:
        enhanced_messages.append({
            "role": "system", 
            "content": f"You are a helpful assistant. Use the following web search results to enrich your response:\n\n{context}"
        })
        enhanced_messages.extend(messages)
    else:
        # Enhance existing system message
        for msg in messages:
            if msg.get("role") == "system":
                enhanced_content = f"{msg['content']}\n\nWeb search results:\n{context}"
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
