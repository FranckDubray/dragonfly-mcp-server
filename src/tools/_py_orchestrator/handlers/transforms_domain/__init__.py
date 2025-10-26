# Domain-specific transforms package
# (normalize_llm_output, extract_field, format_template, filter_by_date, ...)
# Extended with chess-specific helpers and auto-imports for handler registration.

from .normalize_entities import NormalizeEntitiesHandler  # kind: "normalize_entities"
from .pos_to_square import PosToSquareHandler            # kind: "pos_to_square"
from .compare_positions import ComparePositionsHandler   # kind: "compare_positions"
from .uci_build import UciBuildHandler                   # kind: "uci_build"
from .uci_parse import UciParseHandler                   # kind: "uci_parse"

# Explicit imports to guarantee registration in environments where dynamic scan misses files
from .board_coords import BoardCoordsHandler             # kind: "board_coords"
from .template_map import TemplateMapHandler            # kind: "template_map"

__all__ = [
    "NormalizeEntitiesHandler",
    "PosToSquareHandler",
    "ComparePositionsHandler",
    "UciBuildHandler",
    "UciParseHandler",
    "BoardCoordsHandler",
    "TemplateMapHandler",
]
