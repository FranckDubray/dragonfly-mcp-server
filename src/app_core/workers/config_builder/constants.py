from pathlib import Path
# NOTE: this file is located at src/app_core/workers/config_builder/constants.py
# To reach repo root from here we need 5 parents: config_builder -> workers -> app_core -> src -> <repo root>
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
SQLITE_DIR = PROJECT_ROOT / "sqlite3"
TOOL_SPECS_DIR = PROJECT_ROOT / "src" / "tool_specs"
