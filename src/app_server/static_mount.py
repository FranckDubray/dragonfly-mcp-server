
from pathlib import Path
from fastapi.staticfiles import StaticFiles
import logging
import os

logger = logging.getLogger(__name__)

def _relpath(path: Path, cwd: Path) -> str:
    try:
        return str(path.resolve().relative_to(cwd))
    except Exception:
        try:
            return os.path.relpath(str(path.resolve()), str(cwd))
        except Exception:
            return str(path)

def mount_static_and_assets(app, project_root: Path):
    """Mount /static and /assets if folders exist; log absolute paths and CWD.
    Also prints the path relative to the server CWD for easier debugging.
    """
    try:
        cwd = Path(os.getcwd()).resolve()
        logger.info(f"📂 CWD (server): {cwd}")
    except Exception as e:
        logger.warning(f"Could not resolve CWD: {e}")
        cwd = None

    static_dir = project_root / "src" / "static"
    assets_dir = project_root / "assets"

    # Log resolved absolute and relative paths
    if cwd:
        static_rel = _relpath(static_dir, cwd)
        assets_rel = _relpath(assets_dir, cwd)
    else:
        static_rel = str(static_dir)
        assets_rel = str(assets_dir)

    logger.info(
        "📁 Attempting to mount /static from %s (relative: %s, project_root=%s)",
        static_dir.resolve() if static_dir.exists() else static_dir,
        static_rel,
        project_root,
    )
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info("📎 Mounted /static → %s (relative: %s)", static_dir.resolve(), static_rel)
    else:
        logger.warning("⚠️ Static directory not found: %s (relative: %s)", static_dir, static_rel)

    logger.info(
        "📁 Attempting to mount /assets from %s (relative: %s, project_root=%s)",
        assets_dir.resolve() if assets_dir.exists() else assets_dir,
        assets_rel,
        project_root,
    )
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        logger.info("📎 Mounted /assets → %s (relative: %s)", assets_dir.resolve(), assets_rel)
    else:
        logger.warning("⚠️ Assets directory not found: %s (relative: %s)", assets_dir, assets_rel)
