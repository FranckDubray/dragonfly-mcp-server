
from pathlib import Path
from fastapi.staticfiles import StaticFiles
import logging

logger = logging.getLogger(__name__)

def mount_static_and_assets(app, project_root: Path):
    """Mount /static and /assets if folders exist."""
    static_dir = project_root / "src" / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"📁 Mounted /static from {static_dir}")
    else:
        logger.warning(f"⚠️ Static directory not found: {static_dir}")

    assets_dir = project_root / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        logger.info(f"📁 Mounted /assets from {assets_dir}")
    else:
        logger.warning(f"⚠️ Assets directory not found: {assets_dir}")
