"""
Script Executor Tool - Execute multi-tool scripts with orchestration
Allows users to create complex research workflows by scripting MCP tool calls
SECURITY: Sandboxed execution with strict limitations
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json

# TODO: Implement with _script module when imports are fixed
# from ._script import ScriptExecutor

_SPEC_DIR = Path(__file__).resolve().parent.parent / "tool_specs"


def _load_spec_override(name: str) -> Dict[str, Any] | None:
    try:
        p = _SPEC_DIR / f"{name}.json"
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def run(script: str, variables: Dict[str, Any] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
    """Execute a multi-tool script
    
    Args:
        script: Python script code to execute
        variables: Optional dictionary of variables to make available in script
        timeout: Optional timeout in seconds (overrides default)
    """
    
    if not script:
        return {
            "success": False,
            "error": "❌ MISSING SCRIPT: The 'script' parameter is required",
            "help": "Provide a Python script that uses call_tool() or tools.tool_name() to orchestrate MCP tools"
        }
    
    # TODO: Implement with _script module when imports are fixed
    return {
        "success": False,
        "error": "Script executor temporarily disabled due to import issues",
        "help": "Being fixed..."
    }


def spec() -> Dict[str, Any]:
    """Return the MCP function specification for Script Executor"""
    
    base = {
        "type": "function",
        "function": {
            "name": "script_executor",
            "description": "🎭 SCRIPT EXECUTOR: Execute Python scripts that orchestrate multiple MCP tools (temporarily disabled)",
            "parameters": {
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "Python script to execute"
                    },
                    "variables": {
                        "type": "object",
                        "description": "Optional variables to inject into script namespace",
                        "patternProperties": {
                            "^[a-zA-Z_][a-zA-Z0-9_]*$": {}
                        },
                        "additionalProperties": False
                    },
                    "timeout": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 300,
                        "description": "Execution timeout in seconds (default: 60)"
                    }
                },
                "required": ["script"],
                "additionalProperties": False
            }
        }
    }
    
    override = _load_spec_override("script_executor")
    if override and isinstance(override, dict):
        fn = base.get("function", {})
        ofn = override.get("function", {})
        if ofn.get("displayName"):
            fn["displayName"] = ofn["displayName"]
        if ofn.get("description"):
            fn["description"] = ofn["description"]
        if ofn.get("parameters"):
            fn["parameters"] = ofn["parameters"]
    return base