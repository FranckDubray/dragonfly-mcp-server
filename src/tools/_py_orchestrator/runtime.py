
from typing import Callable, Dict, Any, List, Optional

# Runtime primitives

class Next:
    def __init__(self, target: str):
        self.target = str(target)

class Exit:
    def __init__(self, name: str):
        self.name = str(name)

# Decorator to mark a function as a process step (atomic tool/transform)

def step(fn: Callable) -> Callable:
    setattr(fn, "_py_orch_step", True)
    setattr(fn, "_py_orch_step_name", fn.__name__)
    return fn

# Decorator to mark a function as a conditional step (no tool/transform call)

def cond(fn: Callable) -> Callable:
    setattr(fn, "_py_orch_cond", True)
    setattr(fn, "_py_orch_step_name", fn.__name__)
    return fn

class SubGraph:
    def __init__(self, name: str, entry: str, exits: Optional[Dict[str, str]] = None, parts: Optional[List['SubGraphRef']] = None, metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.entry = entry
        self.exits = exits or {}
        self.parts = parts or []  # nested subgraphs
        self.metadata = metadata or {}
        # steps/conds are discovered dynamically in controller by scanning module attrs

class SubGraphRef:
    def __init__(self, name: str, module: str, next: Optional[Dict[str, str]] = None):
        self.name = name
        self.module = module  # relative import path under worker root (e.g., 'subgraphs.init')
        self.next = next or {}  # exit_label -> target_subgraph_name

class Process:
    def __init__(self, name: str, entry: str, parts: Optional[List[SubGraphRef]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.entry = entry  # name of first subgraph
        self.parts = parts or []
        self.metadata = metadata or {}
