#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-generates a compact tools catalog from canonical JSON specs.

- Source of truth: src/tool_specs/*.json
- Optional metadata: src/tool_specs/_meta/tools_meta.json
- Output (overwrites): src/tools/README.md

Design goals:
- Single, lightweight index (kept short and readable)
- Zero duplication: names, categories, operations read from specs
- Robust: works even if some specs miss optional fields

Run: python scripts/generate_tools_catalog.py
"""
from __future__ import annotations
import json
import os
import sys
import glob
from typing import Any, Dict, List

CAT_MAP: Dict[str, str] = {
    "intelligence": "📊 Intelligence & Orchestration",
    "development": "🔧 Development",
    "communication": "📧 Communication",
    "data": "🗄️ Data & Storage",
    "documents": "📄 Documents",
    "media": "🎬 Media",
    "transportation": "✈️ Transportation",
    "networking": "🌐 Networking",
    "utilities": "🔢 Utilities",
    "entertainment": "🎮 Social & Entertainment",
}

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPEC_DIR = os.path.join(ROOT, "src", "tool_specs")
META_PATH = os.path.join(SPEC_DIR, "_meta", "tools_meta.json")
OUT_PATH = os.path.join(ROOT, "src", "tools", "README.md")


def eprint(*args: Any, **kwargs: Any) -> None:
    print(*args, file=sys.stderr, **kwargs)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_meta() -> Dict[str, Any]:
    try:
        return load_json(META_PATH)
    except FileNotFoundError:
        return {}
    except Exception as e:
        eprint(f"⚠️  Failed to load meta file: {META_PATH} → {e}")
        return {}


def iter_specs() -> List[Dict[str, Any]]:
    if not os.path.isdir(SPEC_DIR):
        raise FileNotFoundError(f"Spec directory not found: {SPEC_DIR}")
    specs: List[Dict[str, Any]] = []
    for path in glob.glob(os.path.join(SPEC_DIR, "*.json")):
        base = os.path.basename(path)
        if base.startswith("_"):
            # skip meta or special files
            continue
        try:
            s = load_json(path)
        except Exception as e:
            eprint(f"⚠️  Skipping malformed spec {base}: {e}")
            continue
        fn = s.get("function", {}) or {}
        name = fn.get("name") or os.path.splitext(base)[0]
        display = fn.get("displayName") or name
        category = fn.get("category")
        if category not in CAT_MAP:
            eprint(f"⚠️  Spec {base}: invalid or missing category '{category}'. Skipping.")
            continue
        desc = (fn.get("description") or "").strip()
        tags = fn.get("tags", []) or []
        # operations enum
        params = fn.get("parameters") or {}
        props = params.get("properties") or {}
        op_enum = []
        op_prop = props.get("operation") or {}
        if isinstance(op_prop, dict):
            enum_val = op_prop.get("enum")
            if isinstance(enum_val, list):
                op_enum = [str(x) for x in enum_val]
        specs.append({
            "_path": path,
            "name": name,
            "display": display,
            "category": category,
            "description": desc,
            "tags": tags,
            "operations": op_enum,
        })
    return specs


def shorten_ops(ops: List[str], max_items: int = 6) -> str:
    if not ops:
        return "N/A"
    if len(ops) <= max_items:
        return ", ".join(ops)
    return ", ".join(ops[:max_items]) + " …"


def render_index(specs: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    by_cat: Dict[str, List[Dict[str, Any]]] = {k: [] for k in CAT_MAP}
    for s in specs:
        by_cat[s["category"]].append(s)
    total = len(specs)

    lines: List[str] = []
    lines.append("# 🧰 Dragonfly Tools Catalog (auto‑généré)\n")
    lines.append(
        "Ce fichier est généré automatiquement par `scripts/generate_tools_catalog.py`. Ne pas éditer à la main.\n"
    )
    lines.append(f"Total tools: {total}\n")

    for cat_key, nice in CAT_MAP.items():
        tools = sorted(by_cat[cat_key], key=lambda x: x["display"].lower())
        if not tools:
            continue
        lines.append(f"## {nice} ({len(tools)})\n")
        for t in tools:
            m = meta.get(t["name"], {}) if isinstance(meta, dict) else {}
            tokens = m.get("tokens") if isinstance(m, dict) else None
            tokens_str = ", ".join(tokens) if tokens else "aucun"
            ops_str = shorten_ops(t.get("operations", []))
            desc = t.get("description") or ""
            if len(desc) > 140:
                desc = desc[:137].rstrip() + "…"
            tags = t.get("tags") or []
            tags_str = (" · Tags: " + ", ".join(tags)) if tags else ""
            # Single bullet per tool, with two short sub-lines
            lines.append(f"- {t['display']} — {desc}{tags_str}")
            lines.append(f"  - Opérations: {ops_str}")
            lines.append(f"  - Tokens: {tokens_str}\n")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    try:
        specs = iter_specs()
    except Exception as e:
        eprint(f"❌ Unable to load specs from {SPEC_DIR}: {e}")
        return 1
    meta = load_meta()
    content = render_index(specs, meta)

    out_dir = os.path.dirname(OUT_PATH)
    os.makedirs(out_dir, exist_ok=True)
    try:
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        eprint(f"❌ Failed to write tools catalog to {OUT_PATH}: {e}")
        return 2

    print(f"✅ Tools catalog generated → {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
