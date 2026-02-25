"""Core orchestrator for chat_agent.

Main entry point for executing the conversational agent with tools.

IMPORTANT: Thread continuation strategy v2 (FIXED)
- When continuing a thread (thread_id provided), we NOW load the full history
- This enables proper context display in debug mode (transcript_snapshot)
- Platform still handles deduplication via id/parentId/level
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any, Dict, List, Optional

from .validators import validate_params, validate_token_env
from .model_validator import validate_model, get_model_context_length
from .platform_api import fetch_mcp_tools, load_thread_history
from .thread_chain import ThreadChain
from .thread_utils import platform_history_to_thread_messages
from .output_builder import build_output

LOG = logging.getLogger(__name__)


def execute_chat_agent(
    message: str,
    model: str = "gpt-5.2",
    tools: List[str] = None,
    thread_id: Optional[str] = None,
    output_mode: str = "minimal",
    max_iterations: int = 10,
    timeout: int = 300,
    temperature: float = 0.5,
    system_prompt: Optional[str] = None,
    system_prompt_ref: Optional[str] = None,
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
        system_prompt: Custom system prompt (direct)
        system_prompt_ref: Reference to prompt in prompts.db (format: domain/agent_type/version)
        parallel_execution: Execute independent tools in parallel
    
    Returns:
        Result dict formatted according to output_mode
    """
    start_time = time.time()
    
    # Normalize tools
    if tools is None:
        tools = []
    
    # Resolve system_prompt_ref if provided (PRIORITY: ref overrides direct prompt)
    if system_prompt_ref:
        LOG.info(f"Resolving system_prompt_ref: {system_prompt_ref}")
        resolved = _resolve_prompt_ref(system_prompt_ref)
        
        if isinstance(resolved, dict) and "error" in resolved:
            LOG.error(f"Failed to resolve system_prompt_ref: {resolved['error']}")
            return resolved  # Return error
        
        system_prompt = resolved
        LOG.info(f"System prompt resolved successfully (length: {len(system_prompt)} chars)")
    
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
    _FALLBACK_API_BASE = "https://ai.dragonflygroup.fr/api/v1"
    api_base = os.getenv("AI_PLATFORM_API_BASE", _FALLBACK_API_BASE)
    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000")
    
    if api_base == _FALLBACK_API_BASE:
        LOG.warning("AI_PLATFORM_API_BASE not set in .env — falling back to production: %s", api_base)
    else:
        LOG.info("Platform API base: %s", api_base)
    
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
    
    # Load thread history if continuing a conversation
    messages = []
    if thread_id:
        LOG.info(f"Loading thread history for continuation: {thread_id}")
        history_result = load_thread_history(thread_id, token, api_base, timeout=30)
        
        if not history_result.get("success"):
            return {
                "error": history_result.get("error"),
                "hint": history_result.get("hint", "Thread not found or API error")
            }
        
        # Parse Platform history to OpenAI messages format
        platform_messages = history_result.get("messages", [])
        if platform_messages:
            LOG.info(f"Parsing {len(platform_messages)} messages from Platform history")
            messages = platform_history_to_thread_messages(platform_messages)
            LOG.info(f"Converted to {len(messages)} OpenAI messages")
        else:
            LOG.warning(f"Thread {thread_id} has no message history")
    
    # Initialize thread chain from existing history (or empty)
    if messages:
        thread_chain = ThreadChain.from_messages(messages)
        LOG.info(f"ThreadChain initialized from history: last_level={thread_chain.last_level}, last_id={thread_chain.last_id}")
    else:
        thread_chain = ThreadChain()
        LOG.info("ThreadChain initialized empty (new thread)")
    
    # Add new user message
    user_msg = thread_chain.new_user(message)
    messages.append(user_msg)
    LOG.info(f"New user message added: id={user_msg.get('id')}, level={user_msg.get('level')}")
    
    # Default system prompt (if none provided)
    if not system_prompt:
        system_prompt = _DEFAULT_SYSTEM_PROMPT
        LOG.info("Using default system prompt")
    
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


def _resolve_prompt_ref(prompt_ref: str) -> str | Dict[str, Any]:
    """Resolve system_prompt_ref to actual prompt content.
    
    Args:
        prompt_ref: Format "domain/agent_type/version" (e.g., "legal/planner/v1")
    
    Returns:
        Prompt string OR error dict
    """
    try:
        # Parse reference
        parts = prompt_ref.split("/")
        if len(parts) != 3:
            return {"error": f"Invalid system_prompt_ref format: {prompt_ref}. Expected: domain/agent_type/version"}
        
        domain, agent_type, version = parts
        
        LOG.info(f"Fetching prompt: domain={domain}, agent_type={agent_type}, version={version}")
        
        # Import get_prompt tool
        import sys
        import os
        src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        from tools import get_prompt
        
        # Call get_prompt
        result = get_prompt.run(agent_type=agent_type, domain=domain, version=version)
        
        if "error" in result:
            LOG.error(f"get_prompt returned error: {result['error']}")
            return {"error": f"Failed to resolve prompt_ref '{prompt_ref}': {result['error']}"}
        
        prompt_text = result.get("prompt")
        
        if not prompt_text or not isinstance(prompt_text, str):
            LOG.error(f"get_prompt returned invalid prompt: {type(prompt_text)}")
            return {"error": f"get_prompt returned empty or invalid prompt for '{prompt_ref}'"}
        
        LOG.info(f"Successfully resolved prompt (length: {len(prompt_text)} chars)")
        return prompt_text
    
    except Exception as e:
        LOG.exception(f"Exception while resolving system_prompt_ref")
        return {"error": f"Failed to resolve system_prompt_ref: {e}"}


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
