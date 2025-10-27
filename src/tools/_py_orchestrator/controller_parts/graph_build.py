
from typing import Dict, Any
from pathlib import Path

# Thin compatibility wrapper: expose the legacy name but delegate to graph_extract
from .graph_extract import build_graph as validate_and_extract_graph
