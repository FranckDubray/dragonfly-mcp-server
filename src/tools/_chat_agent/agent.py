"""Core orchestrator for chat_agent.

Main entry point for executing the conversational agent with tools.
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any, Dict, List, Optional

from .validators import validate_params, validate_token_env
from .model_validator import validate_model, get_model_context_length
from .platform_api import fetch_mcp_tools
from .thread_chain import ThreadChain
from .thread_utils import estimate_tokens
from .output_builder import build_output

LOG = logging.getLogger(__name__)


def execute_chat_agent(
    message: str,
    model: str = "gpt-5.2",  # Default model
    tools: List[str] = None,
    thread_id: Optional[str] = None,
    output_mode: str = "minimal",
    max_iterations: int = 10,
    timeout: int = 300,
    temperature: float = 0.5,
    system_prompt: Optional[str] = None,
    parallel_execution: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """Execute chat agent with Platform Threading API.
    
    Args:
        message: User message
        model: Model name (default: "gpt-5.2")
        tools: List of MCP tool names (optional, default=[])
        thread_id: Thread ID for continuation (optional)
        output_mode: "minimal", "intermediate", or "debug"
        max_iterations: Maximum number of tool use iterations
        timeout: Global timeout in seconds
        temperature: Sampling temperature
        system_prompt: Custom system prompt
        parallel_execution: Execute independent tools in parallel
    
    Returns:
        Result dict formatted according to output_mode
    """
    start_time = time.time()
    
    # Normalize tools
    if tools is None:
        tools = []
    
    # Validate token
    token = os.getenv("AI_PORTAL_TOKEN")
    error = validate_token_env(token)
    if error:
        return error
    
    # Validate params
    error = validate_params(
        message=message,
        model=model,
        tools=tools,
        thread_id=thread_id,
        output_mode=output_mode,
        max_iterations=max_iterations,
        timeout=timeout,
        temperature=temperature
    )
    if error:
        return error
    
    # API configuration
    api_base = os.getenv("AI_PLATFORM_API_BASE", "https://ai.dragonflygroup.fr/api/v1")
    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000")
    
    # Validate model
    error = validate_model(model, api_base, token)
    if error:
        return error
    
    # Get model context length
    context_limit = get_model_context_length(model, api_base, token)
    if not context_limit:
        context_limit = 100000  # Default fallback
        LOG.warning(f"Could not fetch context length for {model}, using default: {context_limit}")
    
    # Fetch MCP tools (if any)
    tools_spec = []
    if tools:
        try:
            tools_spec = fetch_mcp_tools(tools, mcp_url)
        except Exception as e:
            return {"error": f"Failed to fetch MCP tools: {e}"}
    
    # Initialize thread chain
    # NOTE: We DON'T load thread history from Platform anymore
    # The Platform server manages the history internally when we pass threadId
    messages = []
    thread_chain = ThreadChain()
    
    # Add user message to chain
    user_msg = thread_chain.new_user(message)
    messages.append(user_msg)
    
    # Default system prompt
    if not system_prompt:
        system_prompt = _DEFAULT_SYSTEM_PROMPT
    
    # Execute agent loop
    from .loop import execute_agent_loop
    
    try:
        result = execute_agent_loop(
            messages=messages,
            thread_chain=thread_chain,
            model=model,
            tools_spec=tools_spec,
            system_prompt=system_prompt,
            temperature=temperature,
            token=token,
            api_base=api_base,
            mcp_url=mcp_url,
            thread_id=thread_id,
            max_iterations=max_iterations,
            timeout=timeout,
            start_time=start_time,
            parallel_execution=parallel_execution,
            context_limit=context_limit
        )
    except Exception as e:
        LOG.exception("Agent loop failed")
        return {"error": f"Agent execution failed: {e}"}
    
    # Build output based on mode
    output = build_output(
        output_mode=output_mode,
        success=result.get("success", False),
        response=result.get("response", ""),
        thread_id=result.get("thread_id", thread_id),
        iterations=result.get("iterations", 0),
        operations=result.get("operations", []),
        messages=messages,
        usage=result.get("usage", {}),
        error=result.get("error")
    )
    
    return output


_DEFAULT_SYSTEM_PROMPT = """Tu es un assistant IA conversationnel capable d'utiliser des outils.

RÈGLES :
1. Analyse la demande de l'utilisateur et identifie si des outils sont nécessaires
2. Appelle les outils appropriés pour obtenir les informations requises
3. Utilise les résultats des outils pour formuler une réponse complète
4. Si aucun outil n'est nécessaire, réponds directement
5. Sois concis et précis dans tes réponses

IMPORTANT :
- Ne devine JAMAIS les résultats : utilise toujours les outils disponibles
- Si un outil échoue, essaie une autre approche ou informe l'utilisateur
- Continue à appeler des outils tant que nécessaire pour répondre complètement
"""
