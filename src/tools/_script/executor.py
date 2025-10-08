"""Script Executor - Main execution engine"""

import requests
import os
import time
import json
import threading
from typing import Dict, Any, Optional, Set, List
import traceback
from io import StringIO
import sys
import importlib
import concurrent
import concurrent.futures as cf

from .security import validate_script_security
from .tools_proxy import ToolsProxy


class ScriptExecutor:
    """Execute scripts that can call other MCP tools"""
    
    def __init__(
        self,
        base_url: str = None,
        allowed_tools: Optional[List[str] | Set[str]] = None,
        default_timeout: Optional[int] = None,
        max_tool_calls: Optional[int] = None,
    ):
        self.base_url = base_url or f"http://127.0.0.1:{os.getenv('MCP_PORT', '8000')}"
        # Timeout and tool-calls limits can be overridden by params
        # If default_timeout is None, fallback to SCRIPT_TIMEOUT_SEC, then EXECUTE_TIMEOUT_SEC, else 60
        if default_timeout is not None:
            self.timeout = int(default_timeout)
        else:
            self.timeout = int(os.getenv('SCRIPT_TIMEOUT_SEC', os.getenv('EXECUTE_TIMEOUT_SEC', '180')))
        self.max_tool_calls = (
            int(max_tool_calls)
            if max_tool_calls is not None
            else int(os.getenv('MAX_TOOL_CALLS_PER_SCRIPT', '50'))
        )
        self.call_count = 0
        # Optional whitelist of allowed tools
        self.allowed_tools: Optional[Set[str]] = set(allowed_tools) if allowed_tools else None
        self.available_tools = self._get_available_tools()
        
    def _get_available_tools(self) -> Set[str]:
        """Get list of available MCP tools"""
        try:
            response = requests.get(f"{self.base_url}/tools", timeout=5)
            if response.status_code == 200:
                tools_data = response.json()
                return {tool.get('regName', tool.get('name', '')) for tool in tools_data if tool.get('regName') or tool.get('name')}
        except Exception:
            pass
        return set()
    
    def call_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call another MCP tool via HTTP API"""
        
        # Check tool call limit
        if self.call_count >= self.max_tool_calls:
            error_msg = f"\u274c TOOL CALL LIMIT EXCEEDED: Script tried to make {self.call_count + 1} tool calls but limit is {self.max_tool_calls}"
            raise Exception(error_msg)
        
        # Whitelist enforcement if provided
        if self.allowed_tools is not None and tool_name not in self.allowed_tools:
            allowed_list = sorted(list(self.allowed_tools))
            error_msg = (
                f"\ud83d\udeab TOOL NOT ALLOWED: '{tool_name}' is not in allowed_tools whitelist.\n"
                f"\ud83d\udccb Allowed tools: {allowed_list}"
            )
            raise Exception(error_msg)
        
        # Check if tool exists
        if tool_name not in self.available_tools:
            available_list = sorted(list(self.available_tools))
            error_msg = f"\u274c UNKNOWN TOOL: '{tool_name}' is not available.\n\ud83d\udccb Available MCP tools: {available_list}"
            raise Exception(error_msg)
        
        self.call_count += 1
        
        if params is None:
            params = {}
        
        # Align tool call timeout with server EXECUTE_TIMEOUT_SEC (fallback 180)
        EXECUTE_TIMEOUT_SEC = int(os.getenv('EXECUTE_TIMEOUT_SEC', '180'))
        
        try:
            response = requests.post(
                f"{self.base_url}/execute",
                json={
                    "tool_reg": tool_name,
                    "params": params
                },
                timeout=EXECUTE_TIMEOUT_SEC,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('result', result)
            else:
                error_msg = f"\u274c TOOL EXECUTION FAILED: {tool_name} returned status {response.status_code}\n\ud83d\udd0d Error: {response.text}"
                return {"error": error_msg, "tool": tool_name, "params": params}
                
        except requests.exceptions.Timeout:
            error_msg = f"\u23f1\ufe0f TIMEOUT: Tool '{tool_name}' exceeded {EXECUTE_TIMEOUT_SEC} seconds (EXECUTE_TIMEOUT_SEC)"
            return {"error": error_msg, "tool": tool_name, "params": params}
        except Exception as e:
            error_msg = f"\u274c NETWORK ERROR: Failed to call tool '{tool_name}': {str(e)}"
            return {"error": error_msg, "tool": tool_name, "params": params}
    
    def get_safe_globals(self) -> Dict[str, Any]:
        """Create safe global namespace for script execution"""
        
        # Extremely limited set of safe built-ins
        def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            allowed = {"concurrent", "concurrent.futures"}
            root = name.split('.')[0]
            if name in allowed or root in {m.split('.')[0] for m in allowed}:
                return importlib.import_module(name)
            raise ImportError(f"Import of '{name}' is forbidden in sandbox")

        safe_builtins = {
            # Basic data types
            'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
            'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
            
            # Safe operations
            'min': min, 'max': max, 'sum': sum, 'abs': abs, 'round': round,
            'sorted': sorted, 'reversed': reversed, 'enumerate': enumerate,
            'zip': zip, 'range': range, 'any': any, 'all': all,
            
            # Type checking (safe)
            'isinstance': isinstance, 'type': type,
            
            # Safe output
            'print': print,

            # Minimal import hook (allowlist)
            '__import__': _safe_import,
        }
        
        # Very limited modules (pre-injected)
        safe_modules = {
            'json': json,  # For data manipulation
            'time': type('time', (), {'time': time.time, 'sleep': time.sleep}),  # Limited time functions for user scripts
            'concurrent': concurrent,
            'concurrent_futures': cf,  # convenience alias if needed
        }
        
        return {
            '__builtins__': safe_builtins,
            'call_tool': self.call_tool,
            'tools': ToolsProxy(self),
            **safe_modules
        }
    
    def execute_script(self, script: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a Python script in a secure environment"""
        
        if not script or not script.strip():
            return {
                "success": False,
                "error": "\u274c EMPTY SCRIPT: No script code provided",
                "help": "Please provide a valid Python script that uses call_tool() or tools.tool_name() to interact with MCP tools"
            }
        
        # Security validation
        security_error = validate_script_security(script)
        if security_error:
            return {
                "success": False,
                "error": security_error,
                "help": "Scripts must only contain basic Python operations and calls to MCP tools via call_tool() or tools.tool_name()"
            }
        
        # Reset call counter
        self.call_count = 0
        
        # Prepare execution namespace
        namespace = self.get_safe_globals()
        
        # Add user variables
        if variables:
            namespace.update(variables)
        
        # Capture stdout
        old_stdout = sys.stdout
        captured_output = StringIO()
        
        try:
            # Redirect stdout to capture print statements
            sys.stdout = captured_output
            
            # Execute script with timeout
            result = self._execute_with_timeout(script, namespace)
            
            # Get captured output
            output = captured_output.getvalue()
            
            return {
                "success": True,
                "result": result,
                "output": output.strip() if output.strip() else None,
                "tool_calls_made": self.call_count,
                "execution_time_seconds": round(getattr(self, '_execution_time', 0.0), 3),
                "available_tools": sorted(list(self.available_tools))
            }
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Format nice error message for LLMs
            formatted_error = f"\ud83d\udea8 {error_type.upper()}: {error_msg}"
            
            # Add context for common errors
            help_msg = None
            if "TOOL CALL LIMIT" in error_msg:
                help_msg = f"Reduce the number of tool calls in your script (current limit: {self.max_tool_calls})"
            elif "UNKNOWN TOOL" in error_msg:
                help_msg = "Check the available_tools list in the response to see what tools are available"
            elif "NOT ALLOWED" in error_msg:
                help_msg = "The tool you tried to call is not in the allowed_tools whitelist"
            elif "TIMEOUT" in error_msg or "timed out" in error_msg.lower():
                help_msg = f"Script execution exceeded {self.timeout} seconds. Simplify your script or reduce tool calls"
            elif "SyntaxError" in error_type:
                help_msg = "Check your Python syntax. Remember: no imports, no function definitions, only basic operations and tool calls"
            
            return {
                "success": False,
                "error": formatted_error,
                "help": help_msg,
                "tool_calls_made": self.call_count,
                "output": captured_output.getvalue().strip() if captured_output.getvalue().strip() else None,
                "traceback": traceback.format_exc(),
                "available_tools": sorted(list(self.available_tools)),
                "execution_time_seconds": round(getattr(self, '_execution_time', 0.0), 3),
            }
            
        finally:
            # Restore stdout
            sys.stdout = old_stdout
    
    def _execute_with_timeout(self, script: str, namespace: Dict[str, Any]) -> Any:
        """Execute script with timeout using threading"""
        result = []
        exception = []
        
        def target():
            try:
                start = time.perf_counter()
                
                # Execute the script (this will block until all inner threads/futures complete)
                exec(script, namespace)
                
                # Look for result in common variable names
                result_vars = ['result', 'results', 'output', 'data', 'return_value', 'final_result']
                script_result = None
                for var_name in result_vars:
                    if var_name in namespace and not var_name.startswith('_'):
                        script_result = namespace[var_name]
                        break
                # If no explicit result variable, return all user-defined variables
                if script_result is None:
                    builtin_vars = set(self.get_safe_globals().keys())
                    script_result = {
                        k: v for k, v in namespace.items()
                        if not k.startswith('_') and k not in builtin_vars
                    }
                self._execution_time = time.perf_counter() - start
                result.append(script_result)
            except Exception as e:
                exception.append(e)
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.timeout)
        
        if thread.is_alive():
            # Thread is still running - timeout occurred
            raise TimeoutError(f"Script execution timed out after {self.timeout} seconds")
        
        if exception:
            raise exception[0]
        
        return result[0] if result else None

    # Compatibility shim with wrapper expecting .run()
    def run(self, script: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.execute_script(script=script, variables=variables)
