#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Télécharge 3 voix Piper FR ciblées depuis Hugging Face et les place sous models/piper/ :
- fr_FR-lessac-medium
- fr_FR-siwis-medium
- fr_FR-mls-medium

Inclut par défaut les .onnx, .json et .onnx.json pour chaque voix.

Usage:
  python scripts/download_piper_fr_voices.py

Options via variables d'environnement (facultatives):
  PIPER_REPO       (par défaut: rhasspy/piper-voices)
  DEST_DIR         (par défaut: models/piper)
  PIPER_PATTERNS   (si tu veux override: patterns séparés par des virgules)
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

REPO = os.getenv("PIPER_REPO", "rhasspy/piper-voices")
DEST_DIR = Path(os.getenv("DEST_DIR", "models/piper")).resolve()
# Par défaut: les 3 voix FR ciblées (onnx + json + onnx.json)
DEFAULT_PATTERNS = [
    "**/fr_FR-lessac-medium.onnx", "**/fr_FR-lessac-medium.json", "**/fr_FR-lessac-medium.onnx.json",
    "**/fr_FR-siwis-medium.onnx",  "**/fr_FR-siwis-medium.json",  "**/fr_FR-siwis-medium.onnx.json",
    "**/fr_FR-mls-medium.onnx",    "**/fr_FR-mls-medium.json",    "**/fr_FR-mls-medium.onnx.json",
]
# Override optionnel via PIPER_PATTERNS (séparées par des virgules)
PATTERNS = [p.strip() for p in os.getenv("PIPER_PATTERNS", ",".join(DEFAULT_PATTERNS)).split(",") if p.strip()]


def main() -> int:
    try:
        from huggingface_hub import snapshot_download  # type: ignore
    except Exception:
        print("[piper-dl] ❌ huggingface_hub non installé. Fais: python -m pip install -U huggingface_hub", file=sys.stderr)
        return 2

    try:
        DEST_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[piper-dl] Téléchargement depuis {REPO} → {DEST_DIR}")
        print(f"[piper-dl] Patterns: {PATTERNS}")
        snapshot_download(
            REPO,
            allow_patterns=PATTERNS,
            local_dir=str(DEST_DIR),
            local_dir_use_symlinks=False,
        )
    except Exception as e:
        print(f"[piper-dl] ❌ snapshot_download a échoué: {e}", file=sys.stderr)
        return 3

    # Vérifie qu'au moins un des 3 modèles est présent et qu'au moins une config .json ou .onnx.json est là
    import glob
    found_models = []
    found_cfg = []
    for base in ("fr_FR-lessac-medium", "fr_FR-siwis-medium", "fr_FR-mls-medium"):
        found_models += glob.glob(str(DEST_DIR / f"**/{base}.onnx"), recursive=True)
        found_cfg += glob.glob(str(DEST_DIR / f"**/{base}.json"), recursive=True)
        found_cfg += glob.glob(str(DEST_DIR / f"**/{base}.onnx.json"), recursive=True)
    if not found_models:
        print("[piper-dl] ⚠️ Aucun des modèles cibles (.onnx) n'a été trouvé après téléchargement.", file=sys.stderr)
        return 4
    if not found_cfg:
        print("[piper-dl] ⚠️ Aucun fichier de config (.json/.onnx.json) trouvé. Le backend streaming Piper peut rester muet.", file=sys.stderr)
        print("- Essaie de relancer ce script; ou récupère manuellement les .onnx.json.", file=sys.stderr)

    print("[piper-dl] ✅ Voix FR téléchargées:")
    for m in sorted(found_models):
        print(" -", os.path.relpath(m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
