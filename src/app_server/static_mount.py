





from pathlib import Path
from fastapi.staticfiles import StaticFiles
import logging
import os

logger = logging.getLogger(__name__)

# Minimal presence check for Workers SPA
REQUIRED_WORKERS_FILES = [
    Path("workers") / "index.css",
    Path("workers") / "spa_main.js",
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
    Backward-compatible policy:
    - Mount Workers SPA assets from src/web/static/workers at /static/workers (FIRST, to avoid being shadowed).
    - Mount legacy Control Panel assets from src/static at /static.
    This avoids breaking /control which historically expects /static/css and /static/js,
    while keeping /workers functional.
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
    workers_dir = web_static_dir / "workers"
    assets_dir = project_root / "assets"
    docs_images_dir = project_root / "docs" / "images"

    # Compute relpaths for logs
    if cwd:
        static_rel = _relpath(static_dir, cwd)
        web_static_rel = _relpath(web_static_dir, cwd)
        workers_rel = _relpath(workers_dir, cwd)
        assets_rel = _relpath(assets_dir, cwd)
        docs_images_rel = _relpath(docs_images_dir, cwd)
    else:
        static_rel = str(static_dir)
        web_static_rel = str(web_static_dir)
        workers_rel = str(workers_dir)
        assets_rel = str(assets_dir)
        docs_images_rel = str(docs_images_dir)

    # 1) Workers SPA assets → /static/workers (mount FIRST to avoid /static shadowing)
    if workers_dir.exists():
        app.mount("/static/workers", StaticFiles(directory=str(workers_dir)), name="static_workers")
        logger.info("📎 Mounted /static/workers → %s (relative: %s)", workers_dir.resolve(), workers_rel)
    elif web_static_dir.exists():
        # Fallback: mount full web static under /static_web to inspect
        app.mount("/static_web", StaticFiles(directory=str(web_static_dir)), name="static_web")
        logger.info("ℹ️ Mounted /static_web (full web static) → %s (relative: %s)", web_static_dir.resolve(), web_static_rel)
    else:
        logger.info("ℹ️ Web static directory not found: %s", web_static_rel)

    # 2) Legacy Control Panel assets → /static
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info("📎 Mounted /static → %s (relative: %s)", static_dir.resolve(), static_rel)
    else:
        logger.warning("⚠️ Legacy static directory not found: %s", static_rel)

    # 3) Mount assets
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        logger.info("📎 Mounted /assets → %s (relative: %s)", assets_dir.resolve(), assets_rel)
    else:
        logger.warning("⚠️ Assets directory not found: %s (relative: %s)", assets_dir, assets_rel)

    # 4) Mount docs/images for local avatars referenced by identity.avatar_url (file name)
    if docs_images_dir.exists():
        app.mount("/docs/images", StaticFiles(directory=str(docs_images_dir)), name="docs_images")
        logger.info("📎 Mounted /docs/images → %s (relative: %s)", docs_images_dir.resolve(), docs_images_rel)
    else:
        logger.info("ℹ️ docs/images directory not found (avatars file-names will 404): %s", docs_images_rel)
