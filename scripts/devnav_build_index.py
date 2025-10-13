#!/usr/bin/env python3
import argparse, json, os, shutil, subprocess, sys, time, hashlib
from pathlib import Path

# Allow imports from src/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tools._dev_navigator.release_index.builder import build_index
from tools._dev_navigator.release_index.reader_paths import make_repo_slug

def _git(cmd, default=""):
    try:
        out = subprocess.check_output(cmd, cwd=ROOT, stderr=subprocess.DEVNULL).decode("utf-8").strip()
        return out
    except Exception:
        return default

def _detect_tag_commit():
    tag = _git(["git", "describe", "--tags", "--abbrev=0"], default="no-tag")
    commit = _git(["git", "rev-parse", "HEAD"], default=str(int(time.time())))
    return tag, commit

def _ensure_latest(src_dir: Path, latest_dir: Path):
    try:
        if latest_dir.is_symlink() or latest_dir.exists():
            if latest_dir.is_symlink():
                latest_dir.unlink()
            else:
                shutil.rmtree(latest_dir)
        try:
            latest_dir.symlink_to(src_dir, target_is_directory=True)
        except Exception:
            latest_dir.mkdir(parents=True, exist_ok=True)
            for name in ("index.db", "manifest.json"):
                shutil.copy2(src_dir / name, latest_dir / name)
    except Exception as e:
        print(f"[WARN] latest setup failed: {e}", file=sys.stderr)

def main():
    ap = argparse.ArgumentParser(description="Build Dev Navigator release index (offline).")
    ap.add_argument("--path", default=str(ROOT), help="Repo root (default: project root)")
    ap.add_argument("--tag", help="Git tag (default: autodetect or 'no-tag')")
    ap.add_argument("--commit", help="Commit hash (default: HEAD)")
    ap.add_argument("--slug", help="Override repo slug (or set DEVNAV_REPO_SLUG env)")
    ap.add_argument("--analyzer-version", default="devnav-1.0.0")
    ap.add_argument("--budgets", help='Budgets JSON (default: {"max_files_scanned":10000,"max_bytes_per_file":65536})')
    args = ap.parse_args()

    path = str(Path(args.path).resolve())
    tag, commit = (args.tag, args.commit) if (args.tag and args.commit) else _detect_tag_commit()
    slug_env = os.getenv("DEVNAV_REPO_SLUG")
    if args.slug:
        os.environ["DEVNAV_REPO_SLUG"] = args.slug
        slug_env = args.slug

    budgets = {"max_files_scanned": 10000, "max_bytes_per_file": 65536}
    if args.budgets:
        budgets_path = Path(args.budgets)
        if budgets_path.exists():
            budgets = json.loads(budgets_path.read_text(encoding="utf-8"))

    cfg_bytes = json.dumps(budgets, separators=(",", ":")).encode("utf-8")
    fprint = hashlib.sha1(cfg_bytes).hexdigest()

    slug = make_repo_slug(path)
    print(f"[INFO] repo_slug={slug} (DEVNAV_REPO_SLUG={slug_env or ''})")

    db_path, manifest_path = build_index(
        path=path,
        tag_name=tag,
        commit_hash=commit,
        analyzer_version=args.analyzer_version,
        config_fingerprint=fprint,
        budgets=budgets,
    )

    release_dir = Path(manifest_path).resolve().parent
    latest_dir = release_dir.parent / "latest"
    _ensure_latest(release_dir, latest_dir)

    print("[OK] Index built")
    print(" - db:", db_path)
    print(" - manifest:", manifest_path)
    print(" - latest:", str(latest_dir))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
