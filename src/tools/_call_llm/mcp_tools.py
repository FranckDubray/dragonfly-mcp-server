"""
MCP tools integration utilities
"""
import json
import requests
import logging

LOG = logging.getLogger(__name__)

def fetch_and_prepare_tools(tool_names, mcp_url):
    """
    Fetch tools from MCP server and prepare OpenAI format
    """
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"Fetching tools from MCP: {mcp_url}/tools")
    
    resp = requests.get(f"{mcp_url}/tools", timeout=10)
    resp.raise_for_status()
    all_tools = resp.json()
    
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"MCP returned {len(all_tools)} total tools")
        tool_names_available = [item.get("name") for item in all_tools if item.get("name")]
        LOG.debug(f"Available tool names: {tool_names_available}")
    
    # Filter tools and prepare OpenAI format
    tools = []
    functions = []
    name_to_reg = {}
    found_tools = []
    
    for item in all_tools:
        item_name = item.get("name")
        if item_name in tool_names:
            spec_str = item.get("json")
            reg_name = item.get("regName", item_name)
            
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug(f"Found requested tool: {item_name} (regName: {reg_name})")
            
            if spec_str:
                try:
                    spec = json.loads(spec_str)
                    if "function" in spec:
                        func_spec = spec["function"]
                        
                        # Format for tools (new OpenAI format) - CORRECT FORMAT
                        tools.append({
                            "type": "function",
                            "function": func_spec
                        })
                        
                        # Format for functions (legacy OpenAI format) - BACKUP  
                        functions.append(func_spec)  # Just the function part
                        
                        fname = func_spec.get("name")
                        if fname:
                            name_to_reg[fname] = reg_name
                            found_tools.append(fname)
                        if LOG.isEnabledFor(logging.DEBUG):
                            LOG.debug(f"Tool {item_name} prepared in both formats")
                except Exception as e:
                    if LOG.isEnabledFor(logging.DEBUG):
                        LOG.debug(f"Failed to parse spec for tool {item_name}: {e}")
    
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"Found {len(found_tools)} matching tools: {found_tools}")
        LOG.debug(f"Name to reg mapping: {name_to_reg}")
        missing_tools = set(tool_names) - set(found_tools)
        if missing_tools:
            LOG.debug(f"Missing tools: {missing_tools}")
    
    return {
        "tools": tools,
        "functions": functions,
        "name_to_reg": name_to_reg,
        "found_tools": found_tools
    }

def execute_mcp_tool(fname, args, name_to_reg, mcp_url):
    """
    Execute a single MCP tool
    """
    reg_name = name_to_reg.get(fname, fname)
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"  Mapped to MCP tool: {reg_name}")
    
    # Call MCP
    mcp_payload = {"tool_reg": reg_name, "params": args}
    
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"  → POST {mcp_url}/execute")
        LOG.debug(f"  → MCP payload: {json.dumps(mcp_payload)}")
    
    try:
        mcp_resp = requests.post(
            f"{mcp_url}/execute",
            json=mcp_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"  ← MCP HTTP {mcp_resp.status_code}")
            LOG.debug(f"  ← MCP Response: {mcp_resp.text}")
        
        if mcp_resp.status_code == 200:
            mcp_data = mcp_resp.json()
            result = mcp_data.get("result", {})
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug(f"  ← MCP result: {result}")
            return result
        else:
            error = {"error": f"MCP error {mcp_resp.status_code}: {mcp_resp.text}"}
            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug(f"  ← MCP error: {mcp_resp.text}")
            return error
        
    except Exception as e:
        error = {"error": f"MCP call failed: {e}"}
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(f"  ← MCP exception: {e}")
        return error