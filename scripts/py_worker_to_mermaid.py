#!/usr/bin/env python3
"""
Generate Mermaid graph for a Python worker (workers/<name>/process.py) and validate output.
Usage:
  python scripts/py_worker_to_mermaid.py <worker_name|process_file> [--out mermaid.mmd] [--check]

Notes:
- If <worker_name> is provided (no slash and no .py), the script resolves to workers/<name>/process.py.
- Escapes dangerous characters in subgraph labels.
- Validates basic Mermaid structure (graph header, balanced subgraph/end).
- If 'mmdc' (Mermaid CLI) is installed, you can further validate/output to SVG/PNG manually.
"""
import argparse
import sys
from pathlib import Path
import importlib.util
import json

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tools._py_orchestrator.controller import validate_and_extract_graph, ValidationError

ESCAPE_MAP = {
    '"': '\\"',
    "'": "\\'",
    "`": "'",
    "<": "\u003C",
    ">": "\u003E",
}

def resolve_target_to_process(target: str) -> Path:
    """Resolve a CLI target to a process.py path.
    - If target is a worker name (no '/' and no '.py'), resolve to workers/<name>/process.py.
    - Else, treat target as a direct path to process.py
    """
    t = target.strip()
    if ('/' not in t and '\\' not in t and not t.endswith('.py')):
        return (PROJECT_ROOT / 'workers' / t / 'process.py').resolve()
    p = Path(t).resolve()
    return p


def escape_label(s: str) -> str:
    out = []
    for ch in str(s):
        out.append(ESCAPE_MAP.get(ch, ch))
    return ''.join(out)


def build_mermaid_from_graph(graph: dict) -> str:
    """Build a safe Mermaid from extracted graph JSON (nodes/edges/subgraphs)."""
    nodes = graph.get('nodes', [])
    edges = graph.get('edges', [])
    subgraphs = graph.get('subgraphs', {})

    lines = ["graph TD"]
    # Group nodes by subgraph
    by_sg = {}
    for n in nodes:
        sg = n.get('subgraph') or '__ROOT__'
        by_sg.setdefault(sg, []).append(n)

    # START at top if any
    has_start = any(n.get('type') == 'start' for n in nodes)
    if has_start:
        lines.append("  START")

    # Subgraph clusters
    for sg_name, info in subgraphs.items():
        label = escape_label(sg_name)
        lines.append(f"  subgraph {label}")
        for n in by_sg.get(sg_name, []):
            lines.append(f"    {n['name']}")
        lines.append("  end")

    # Nodes not in subgraphs (e.g., END)
    for n in by_sg.get('__ROOT__', []):
        lines.append(f"  {n['name']}")

    # Edges
    for e in edges:
        src = e.get('from')
        dst = e.get('to')
        when = e.get('when')
        if when and when != 'always':
            lbl = escape_label(when)
            lines.append(f"  {src}-->|{lbl}|{dst}")
        else:
            lines.append(f"  {src}-->{dst}")

    return "\n".join(lines)


def validate_mermaid(mmd: str) -> None:
    # Basic checks: header, balanced subgraph/end, non-empty lines
    if not mmd.startswith("graph TD"):
        raise ValueError("Mermaid must start with 'graph TD'")
    subs = sum(1 for ln in mmd.splitlines() if ln.strip().startswith('subgraph '))
    ends = sum(1 for ln in mmd.splitlines() if ln.strip() == 'end' or ln.strip() == '  end')
    if subs != ends:
        raise ValueError(f"Unbalanced subgraph/end blocks: subgraphs={subs}, ends={ends}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target', help='Worker name (under workers/) or path to process.py')
    ap.add_argument('--out', help='Output .mmd path (optional)')
    ap.add_argument('--check', action='store_true', help='Validate mermaid syntax heuristically')
    args = ap.parse_args()

    proc_path = resolve_target_to_process(args.target)
    if not proc_path.exists():
        print(f"process.py not found: {proc_path}", file=sys.stderr)
        sys.exit(1)
    worker_root = proc_path.parent

    try:
        graph = validate_and_extract_graph(worker_root)
    except ValidationError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(3)

    # Prefer controller-provided Mermaid if available
    mmd = graph.get('mermaid') or build_mermaid_from_graph(graph)
    if args.check:
        try:
            validate_mermaid(mmd)
        except Exception as e:
            print(f"Mermaid validation failed: {e}", file=sys.stderr)
            sys.exit(4)

    if args.out:
        outp = Path(args.out)
        outp.write_text(mmd, encoding='utf-8')
        print(f"Mermaid written to {outp}")
    else:
        print(mmd)

if __name__ == '__main__':
    main()
