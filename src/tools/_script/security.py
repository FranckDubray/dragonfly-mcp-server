"""Script Executor - Security validation"""

import ast
from typing import Optional


class RestrictedNodeVisitor(ast.NodeVisitor):
    """AST visitor to check for dangerous operations"""
    
    FORBIDDEN_NODES = {
        ast.Import: "Import statements are forbidden for security",
        ast.ImportFrom: "Import statements are forbidden for security", 
        ast.FunctionDef: "Function definitions are forbidden",
        ast.ClassDef: "Class definitions are forbidden",
        ast.AsyncFunctionDef: "Async function definitions are forbidden",
        ast.Global: "Global statements are forbidden",
        ast.Nonlocal: "Nonlocal statements are forbidden",
    }
    
    FORBIDDEN_FUNCTIONS = {
        'open', 'file', 'input', 'raw_input', 'execfile', 'reload',
        '__import__', 'eval', 'exec', 'compile', 'exit', 'quit',
        'help', 'license', 'copyright', 'credits', 'dir', 'vars',
        'locals', 'globals', 'delattr', 'setattr'
    }
    
    FORBIDDEN_ATTRIBUTES = {
        '__class__', '__bases__', '__subclasses__', '__mro__',
        '__globals__', '__code__', '__closure__', '__defaults__',
        '__dict__', '__weakref__', '__module__', '__file__',
        '__builtins__', '__import__'
    }
    
    def __init__(self):
        self.violations = []
    
    def visit(self, node):
        # Check forbidden node types
        for forbidden_type, message in self.FORBIDDEN_NODES.items():
            if isinstance(node, forbidden_type):
                self.violations.append(f"Line {node.lineno}: {message}")
                return
        
        # Check function calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in self.FORBIDDEN_FUNCTIONS:
                self.violations.append(f"Line {node.lineno}: Function '{node.func.id}' is forbidden for security")
        
        # Check attribute access
        if isinstance(node, ast.Attribute):
            if node.attr in self.FORBIDDEN_ATTRIBUTES:
                self.violations.append(f"Line {node.lineno}: Attribute '{node.attr}' access is forbidden")
        
        # Continue traversing
        self.generic_visit(node)


def validate_script_security(script: str) -> Optional[str]:
    """Validate script for security violations"""
    try:
        tree = ast.parse(script)
        visitor = RestrictedNodeVisitor()
        visitor.visit(tree)
        
        if visitor.violations:
            return "SECURITY VIOLATIONS DETECTED:\n" + "\n".join(visitor.violations)
        
        return None
        
    except SyntaxError as e:
        return f"SYNTAX ERROR: Line {e.lineno}: {e.msg}"
    except Exception as e:
        return f"SCRIPT PARSING ERROR: {str(e)}"