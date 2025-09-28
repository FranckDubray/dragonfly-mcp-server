"""
Tool execution handlers for both new and legacy OpenAI formats
"""
import json
import requests
import logging
from .mcp_tools import execute_mcp_tool
from .streaming import process_streaming_chunks

LOG = logging.getLogger(__name__)

def handle_tool_calls(tool_calls, name_to_reg, mcp_url, payload, endpoint, headers):
    """
    Handle tool_calls (NEW OpenAI format)
    """
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"=== EXECUTING TOOL CALLS (NEW FORMAT) ===")
    
    # Add assistant message to conversation
    # (message is already in payload from caller)
    
    # Execute each tool call
    for tool_call in tool_calls:
        tc_id = tool_call.get("id")
        function_data = tool_call.get("function", {})
        fname = function_data.get("name")
        args_str = function_data.get("arguments", "{}")
        
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"→ Tool call {tc_id}: {fname}")
        
        try:
            args = json.loads(args_str)
        except Exception as e:
            args = {}
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug(f"  Failed to parse args '{args_str}': {e}")
        
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"  Args: {args}")
        
        # Execute MCP tool
        result = execute_mcp_tool(fname, args, name_to_reg, mcp_url)
        
        # Add tool response to conversation (NEW FORMAT)
        tool_response = {
            "role": "tool",
            "tool_call_id": tc_id,
            "content": json.dumps(result)
        }
        payload["messages"].append(tool_response)
        
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"  Added tool response to conversation")
    
    # Call LLM again with tool results (streaming)
    return final_llm_call(payload, endpoint, headers)

def handle_function_call(function_call, name_to_reg, mcp_url, payload, endpoint, headers):
    """
    Handle function_call (LEGACY OpenAI format) 
    """
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"=== EXECUTING FUNCTION CALL (LEGACY FORMAT) ===")
    
    # Add assistant message to conversation
    # (message is already in payload from caller)
    
    # Execute function
    fname = function_call.get("name")
    args_str = function_call.get("arguments", "{}")
    
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"→ Function: {fname}")
    
    try:
        args = json.loads(args_str)
    except Exception as e:
        args = {}
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"  Failed to parse args '{args_str}': {e}")
    
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"  Args: {args}")
    
    # Execute MCP tool
    result = execute_mcp_tool(fname, args, name_to_reg, mcp_url)
    
    # Add function response to conversation (LEGACY FORMAT)
    function_response = {
        "role": "function",
        "name": fname,
        "content": json.dumps(result)
    }
    payload["messages"].append(function_response)
    
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"  Added function response to conversation")
    
    # Call LLM again with function results (streaming)
    return final_llm_call(payload, endpoint, headers)

def final_llm_call(payload, endpoint, headers):
    """
    Make final LLM call with streaming after tool execution
    """
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"=== FINAL LLM CALL (streaming) ===")
        LOG.debug(f"→ POST {endpoint} with {len(payload['messages'])} messages")
    
    payload["stream"] = True
    resp = requests.post(endpoint, headers=headers, json=payload, stream=True, verify=False)
    
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"← HTTP {resp.status_code}")
    
    resp.raise_for_status()
    
    # Process streaming response
    result = process_streaming_chunks(resp)
    
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"← Final streaming complete: content='{result['content']}', finish_reason={result['finish_reason']}")
    
    return {
        "success": True,
        "content": result["content"],
        "finish_reason": result["finish_reason"],
        "usage": result["usage"]
    }