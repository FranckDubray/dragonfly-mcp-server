"""Script Executor - Tools Proxy for syntactic sugar"""


class ToolsProxy:
    """Proxy class to allow tools.tool_name() syntax"""
    
    def __init__(self, executor):
        self.executor = executor
    
    def __getattr__(self, tool_name: str):
        """Return a function that calls the specified tool"""
        def tool_function(**params):
            return self.executor.call_tool(tool_name, params)
        return tool_function