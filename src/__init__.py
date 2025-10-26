
# Short alias to import py orchestrator DSL from workers
from .tools._py_orchestrator import step, Next, Exit, SubGraph, SubGraphRef, Process

# Workers can: from py_orch import step, Next, Exit, SubGraph, SubGraphRef, Process
py_orch = __import__('src.tools._py_orchestrator', fromlist=['step'])
