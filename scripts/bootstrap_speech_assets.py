#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bootstrap speech assets (best-effort):
- Télécharge une voix Piper FR (Lessac, medium) depuis Hugging Face
- Ecrit dans models/piper/fr_FR-lessac-medium/
- Ne casse rien: skip si déjà présent, écrit via fichiers temporaires + rename
- Fallback HTTP si huggingface_hub n’est pas installé

Env overrides (optionnels):
- PIPER_REPO (par défaut: rhasspy/piper-voices)
- PIPER_VOICE_SUBPATH (ex: "voices/fr_FR-lessac-medium")
- PIPER_VOICE_BASENAME (ex: "fr_FR-lessac-medium")
- PIPER_VOICE_DIRNAME (ex: "fr_FR-lessac-medium")
"""
from __future__ import annotations
import os
import sys
import shutil
import tempfile
from pathlib import Path

DEFAULT_REPO = os.getenv("PIPER_REPO", "rhasspy/piper-voices")
VOICE_SUBPATH = os.getenv("PIPER_VOICE_SUBPATH", "voices/fr_FR-lessac-medium")
VOICE_BASENAME = os.getenv("PIPER_VOICE_BASENAME", "fr_FR-lessac-medium")
VOICE_DIRNAME = os.getenv("PIPER_VOICE_DIRNAME", VOICE_BASENAME)

# Dans ce repo, les fichiers s'appellent fr_FR-lessac-medium.onnx et fr_FR-lessac-medium.json
SRC_FILES = [f"{VOICE_BASENAME}.onnx", f"{VOICE_BASENAME}.json"]

DEST_DIR = Path("models") / "piper" / VOICE_DIRNAME
DEST_FILES = [DEST_DIR / name for name in SRC_FILES]
MIN_SIZES = [1_000_000, 2_000]  # heuristiques: onnx >= ~1MB, json >= ~2KB


def already_ok() -> bool:
    for dest, min_size in zip(DEST_FILES, MIN_SIZES):
        if not dest.exists() or dest.stat().st_size < min_size:
            return False
    return True


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def hf_download(repo_id: str, src_path: str, dest_path: Path) -> bool:
    """Try downloading via huggingface_hub (handles LFS, redirects, auth)."""
    try:
        from huggingface_hub import hf_hub_download  # type: ignore
    except Exception:
        return False
    try:
        tmp_dir = tempfile.mkdtemp(prefix="piper_dl_")
        try:
            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=src_path,
                revision="main",
                cache_dir=None,
                local_dir=tmp_dir,
            )
            ensure_dir(dest_path.parent)
            tmp_file = Path(local_path)
            shutil.copy2(tmp_file, dest_path)
            return dest_path.exists() and dest_path.stat().st_size > 0
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception as e:
        print(f"[bootstrap] hf_hub_download failed for {src_path}: {e}", file=sys.stderr)
        return False


def http_download(repo_id: str, src_path: str, dest_path: Path) -> bool:
    """Fallback HTTP direct via CDN (suit les redirections LFS)."""
    try:
        import requests  # type: ignore
    except Exception:
        print("[bootstrap] requests manquant. pip install requests", file=sys.stderr)
        return False
    url = f"https://huggingface.co/{repo_id}/resolve/main/{src_path}"
    try:
        ensure_dir(dest_path.parent)
        with requests.get(url, stream=True, timeout=60, headers={"User-Agent": "dragonfly-mcp/tts-bootstrap"}) as r:
            if r.status_code != 200:
                print(f"[bootstrap] HTTP {r.status_code} for {url}", file=sys.stderr)
                return False
            with tempfile.NamedTemporaryFile(dir=str(dest_path.parent), delete=False) as tf:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    if chunk:
                        tf.write(chunk)
                tmp_name = tf.name
        Path(tmp_name).replace(dest_path)
        return dest_path.exists() and dest_path.stat().st_size > 0
    except Exception as e:
        print(f"[bootstrap] HTTP download failed for {url}: {e}", file=sys.stderr)
        return False


def main() -> int:
    print("[bootstrap] Piper voice setup (best-effort)")
    if already_ok():
        print("[bootstrap] assets already present → skip")
        return 0

    ensure_dir(DEST_DIR)
    ok_any = True
    for name, min_size in zip(SRC_FILES, MIN_SIZES):
        src = f"{VOICE_SUBPATH}/{name}"
        dest = DEST_DIR / name
        # 1) huggingface_hub
        if hf_download(DEFAULT_REPO, src, dest):
            if dest.stat().st_size >= min_size:
                print(f"[bootstrap] OK via HF: {dest.relative_to(Path.cwd())}")
                continue
        # 2) HTTP direct
        if http_download(DEFAULT_REPO, src, dest) and dest.stat().st_size >= min_size:
            print(f"[bootstrap] OK via HTTP: {dest.relative_to(Path.cwd())}")
            continue
        ok_any = False
        print(f"[bootstrap] ❌ failed to fetch {name}", file=sys.stderr)

    if not ok_any:
        print("\n[bootstrap] Piper voices missing. Aides:", file=sys.stderr)
        print(" - pip install huggingface_hub  (puis relance ce script)", file=sys.stderr)
        print(" - Réseau/proxy: autoriser huggingface.co", file=sys.stderr)
        print(" - Téléchargement manuel (placez les 2 fichiers):", file=sys.stderr)
        print(f"   {DEST_DIR / (VOICE_BASENAME + '.onnx')}", file=sys.stderr)
        print(f"   {DEST_DIR / (VOICE_BASENAME + '.json')}", file=sys.stderr)
        print(f"   (depuis: https://huggingface.co/{DEFAULT_REPO}/tree/main/{VOICE_SUBPATH})", file=sys.stderr)
        return 2

    print("[bootstrap] ✅ Piper ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
