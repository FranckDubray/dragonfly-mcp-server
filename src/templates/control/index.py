
"""
Control UI - glue to assemble layout + sidebar + main and expose CONTROL_HTML
"""
from .layout import CONTROL_LAYOUT_HTML
from .sidebar import CONTROL_SIDEBAR_HTML
from .main import CONTROL_MAIN_HTML

CONTROL_HTML = CONTROL_LAYOUT_HTML.format(content=CONTROL_SIDEBAR_HTML + CONTROL_MAIN_HTML)
