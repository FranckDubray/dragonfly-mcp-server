"""Ollama local API client."""
import requests
import json
from typing import Dict, Any, List
from ..utils import OLLAMA_LOCAL_URL, DEFAULT_LOCAL_TIMEOUT, format_model_size, format_duration


class OllamaLocalClient:
    """Client for Ollama local API (localhost:11434)."""
    
    def __init__(self, base_url: str = OLLAMA_LOCAL_URL):
        self.base_url = base_url.rstrip('/')
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, timeout: int = DEFAULT_LOCAL_TIMEOUT) -> Dict[str, Any]:
        """Make HTTP request to Ollama local API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            else:
                headers = {"Content-Type": "application/json"} if data else {}
                response = requests.request(
                    method.upper(),
                    url,
                    json=data,
                    headers=headers,
                    timeout=timeout
                )
            
            # Check if request was successful
            if response.status_code == 404:
                return {
                    "success": False,
                    "error": f"Endpoint not found: {endpoint}. Check if Ollama is running on {self.base_url}",
                    "status_code": 404
                }
            
            if not response.ok:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
            
            # Try to parse JSON response
            try:
                result = response.json()
                return {"success": True, **result}
            except json.JSONDecodeError:
                # Some endpoints return plain text
                return {"success": True, "response": response.text}
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?",
                "suggestion": "Run 'ollama serve' to start Ollama server"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"Request timeout after {timeout} seconds",
                "suggestion": "Try increasing timeout or check if model is too large"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    # ==========================================
    # MODEL MANAGEMENT
    # ==========================================
    
    def list_models(self) -> Dict[str, Any]:
        """List available models."""
        result = self._make_request("GET", "/api/tags")
        
        if result.get("success") and "models" in result:
            # Enhance model info with formatted sizes
            models = result["models"]
            for model in models:
                if "size" in model:
                    model["size_formatted"] = format_model_size(model["size"])
            
            return {
                "success": True,
                "models": models,
                "count": len(models),
                "total_size": sum(m.get("size", 0) for m in models),
                "total_size_formatted": format_model_size(sum(m.get("size", 0) for m in models))
            }
        
        return result
    
    def get_version(self) -> Dict[str, Any]:
        """Get Ollama version."""
        return self._make_request("GET", "/api/version")
    
    def get_running_models(self) -> Dict[str, Any]:
        """Get currently running models."""
        result = self._make_request("GET", "/api/ps")
        
        if result.get("success") and "models" in result:
            models = result["models"]
            for model in models:
                # Format sizes
                if "size" in model:
                    model["size_formatted"] = format_model_size(model["size"])
                if "size_vram" in model:
                    model["size_vram_formatted"] = format_model_size(model["size_vram"])
                
                # Format context length
                if "context_length" in model:
                    model["context_length_formatted"] = f"{model['context_length']:,} tokens"
            
            return {
                "success": True,
                "running_models": models,
                "count": len(models),
                "total_vram": sum(m.get("size_vram", 0) for m in models),
                "total_vram_formatted": format_model_size(sum(m.get("size_vram", 0) for m in models))
            }
        
        return result
    
    def show_model(self, model: str) -> Dict[str, Any]:
        """Show detailed model information."""
        return self._make_request("POST", "/api/show", {"name": model})
    
    def pull_model(self, model: str) -> Dict[str, Any]:
        """Pull/download a model."""
        return self._make_request("POST", "/api/pull", {"name": model})
    
    def push_model(self, model: str) -> Dict[str, Any]:
        """Push/upload a model."""
        return self._make_request("POST", "/api/push", {"name": model})
    
    def create_model(self, model: str, modelfile: str) -> Dict[str, Any]:
        """Create a custom model."""
        return self._make_request("POST", "/api/create", {
            "name": model,
            "modelfile": modelfile
        })
    
    def copy_model(self, source_model: str, destination_model: str) -> Dict[str, Any]:
        """Copy a model."""
        return self._make_request("POST", "/api/copy", {
            "source": source_model,
            "destination": destination_model
        })
    
    def delete_model(self, model: str) -> Dict[str, Any]:
        """Delete a model."""
        return self._make_request("DELETE", "/api/delete", {"name": model})
    
    # ==========================================
    # TEXT GENERATION  
    # ==========================================
    
    def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        timeout: int = DEFAULT_LOCAL_TIMEOUT,
        options: Dict = None
    ) -> Dict[str, Any]:
        """Generate text completion."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **(options or {})
            }
        }
        
        result = self._make_request("POST", "/api/generate", payload, timeout)
        
        # Enhance result with timing info
        if result.get("success"):
            # Format durations if present
            for key in ["total_duration", "load_duration", "prompt_eval_duration", "eval_duration"]:
                if key in result:
                    result[f"{key}_formatted"] = format_duration(result[key])
        
        return result
    
    def chat(
        self,
        model: str,
        messages: List[Dict],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        timeout: int = DEFAULT_LOCAL_TIMEOUT,
        options: Dict = None
    ) -> Dict[str, Any]:
        """Chat with context."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **(options or {})
            }
        }
        
        result = self._make_request("POST", "/api/chat", payload, timeout)
        
        # Enhance result with timing info
        if result.get("success"):
            # Format durations if present
            for key in ["total_duration", "load_duration", "prompt_eval_duration", "eval_duration"]:
                if key in result:
                    result[f"{key}_formatted"] = format_duration(result[key])
        
        return result
    
    def embeddings(self, model: str, text: str, timeout: int = DEFAULT_LOCAL_TIMEOUT) -> Dict[str, Any]:
        """Generate text embeddings."""
        payload = {
            "model": model,
            "prompt": text
        }
        
        result = self._make_request("POST", "/api/embeddings", payload, timeout)
        
        # Enhance embeddings result
        if result.get("success") and "embedding" in result:
            embedding = result["embedding"]
            result["embedding_info"] = {
                "dimensions": len(embedding),
                "type": "float32",
                "first_5_values": embedding[:5] if len(embedding) >= 5 else embedding
            }
        
        return result