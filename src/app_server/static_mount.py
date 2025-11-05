





from pathlib import Path
from fastapi.staticfiles import StaticFiles
import logging
import os

logger = logging.getLogger(__name__)

REQUIRED_WORKERS_FILES = [
    Path("workers") / "index.css",
    Path("workers") / "list.js",
]

def _relpath(path: Path, cwd: Path) -> str:
    try:
        return str(path.resolve().relative_to(cwd))
    except Exception:
        try:
            return os.path.relpath(str(path.resolve()), str(cwd))
        except Exception:
            return str(path)

def _has_required_workers_assets(base: Path) -> bool:
    try:
        for rf in REQUIRED_WORKERS_FILES:
            if not (base / rf).is_file():
                return False
        return True
    except Exception:
        return False

def mount_static_and_assets(app, project_root: Path):
    """Mount /static and /assets if folders exist; log absolute paths and CWD.
    Prefer src/web/static over src/static to ensure latest Workers UI assets are served consistently.
    Also mount /docs/images if present so avatars from identity can be served.
    """
    try:
        cwd = Path(os.getcwd()).resolve()
        logger.info(f"📂 CWD (server): {cwd}")
    except Exception as e:
        logger.warning(f"Could not resolve CWD: {e}")
        cwd = None

    static_dir = project_root / "src" / "static"
    web_static_dir = project_root / "src" / "web" / "static"
    assets_dir = project_root / "assets"
    docs_images_dir = project_root / "docs" / "images"

    # Compute relpaths for logs
    if cwd:
        static_rel = _relpath(static_dir, cwd)
        web_static_rel = _relpath(web_static_dir, cwd)
        assets_rel = _relpath(assets_dir, cwd)
        docs_images_rel = _relpath(docs_images_dir, cwd)
    else:
        static_rel = str(static_dir)
        web_static_rel = str(web_static_dir)
        assets_rel = str(assets_dir)
        docs_images_rel = str(docs_images_dir)

    # Prefer web_static_dir if it exists
    if web_static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(web_static_dir)), name="static")
        logger.info("📎 Mounted /static (web) → %s (relative: %s)", web_static_dir.resolve(), web_static_rel)
    elif static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info("📎 Mounted /static → %s (relative: %s)", static_dir.resolve(), static_rel)
    else:
        logger.warning("⚠️ Static directory not found: %s or %s", static_dir, web_static_dir)

    # Mount assets
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        logger.info("📎 Mounted /assets → %s (relative: %s)", assets_dir.resolve(), assets_rel)
    else:
        logger.warning("⚠️ Assets directory not found: %s (relative: %s)", assets_dir, assets_rel)

    # Mount docs/images for local avatars referenced by identity.avatar_url (file name)
    if docs_images_dir.exists():
        app.mount("/docs/images", StaticFiles(directory=str(docs_images_dir)), name="docs_images")
        logger.info("📎 Mounted /docs/images → %s (relative: %s)", docs_images_dir.resolve(), docs_images_rel)
    else:
        logger.info("ℹ️ docs/images directory not found (avatars file-names will 404): %s", docs_images_rel)

 
 
 
 
 
 
 
 
