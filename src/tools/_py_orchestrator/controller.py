




import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any

from .controller_parts.errors import ValidationError
from .controller_parts.validators_toplevel import validate_module_toplevel
from .controller_parts.validators_steps import ast_validate_step
from .controller_parts.graph_extract import build_graph as _build_graph
from .controller_parts.graph_loader import _load_module_from_path, discover_funcs, _is_process_like, _is_subgraphref_like
from .controller_parts.graph_build import validate_and_extract_graph as _legacy_validate_and_extract_graph

__all__ = ["validate_and_extract_graph", "ValidationError", "validate_module_toplevel", "ast_validate_step"]


def validate_and_extract_graph(worker_root: Path) -> Dict[str, Any]:
    """Compatibility façade.
    - Prefer new extractor (graph_extract.build_graph),
    - Fallback to legacy if anything surprising occurs.
    """
    try:
        return _build_graph(worker_root)
    except Exception:
        # Fallback to legacy path for maximum compatibility
        return _legacy_validate_and_extract_graph(worker_root)

 
 
 
 
 
 
 
 
 
 
 
 
 
