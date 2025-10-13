import re
import os
from typing import List, Dict, Optional

from .anchors import make_anchor

# Generic YAML router/gateway extractors (Kong/Traefik/Nginx-like)
# This is a light heuristic parser focusing on path keys and methods in common shapes.

# Keys we recognize as path-like
PATH_KEYS = ("path", "uri", "url", "rule", "pathPrefix", "basePath")
METHOD_KEYS = ("method", "methods")

# Simple patterns per line (no YAML loading to keep safe and fast, head-limited)
KEY_VALUE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_\-]+):\s*(?P<val>.+?)\s*$")
LIST_ITEM = re.compile(r"^(?P<indent>\s*)-\s*(?P<val>.+?)\s*$")

# Symfony-like include/import/resource patterns (very light)
RESOURCE_INLINE = re.compile(r"^\s*resource:\s*(?P<val>.+?)\s*$")
IMPORTS_KEY = re.compile(r"^\s*imports:\s*$")
FILES_KEY = re.compile(r"^\s*files:\s*$")
INCLUDE_KEY = re.compile(r"^\s*include[s]?:\s*$")


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        return s[1:-1]
    return s


def extract_yaml_gateway(text: str, relpath: str) -> List[Dict]:
    items: List[Dict] = []
    if not text:
        return items

    lines = text.splitlines()
    current_paths: List[str] = []
    current_methods: List[str] = []
    anchor_line: int = 1
    in_methods_list: bool = False
    methods_indent: Optional[int] = None
    in_paths_list: bool = False
    paths_indent: Optional[int] = None

    def flush():
        nonlocal current_paths, current_methods
        if not current_paths:
            return
        methods = current_methods or ['ANY']
        for p in current_paths:
            p = _strip_quotes(p)
            if not p:
                continue
            for m in methods:
                items.append({
                    'kind': 'http',
                    'method': m.upper(),
                    'path_or_name': p,
                    'source_anchor': make_anchor(relpath, anchor_line, 0),
                    'framework_hint': 'gateway'
                })
        current_paths = []
        current_methods = []

    for idx, line in enumerate(lines, start=1):
        kv = KEY_VALUE.match(line)
        li = LIST_ITEM.match(line)

        if in_methods_list:
            if li and (methods_indent is None or len(li.group('indent')) >= methods_indent):
                current_methods.append(_strip_quotes(li.group('val')).upper())
                continue
            else:
                in_methods_list = False
                methods_indent = None
        if in_paths_list:
            if li and (paths_indent is None or len(li.group('indent')) >= paths_indent):
                current_paths.append(_strip_quotes(li.group('val')))
                continue
            else:
                in_paths_list = False
                paths_indent = None

        if kv:
            key = kv.group('key')
            val = kv.group('val')
            if key in METHOD_KEYS:
                if val.startswith('['):
                    body = val.strip()[1:-1]
                    current_methods.extend([_strip_quotes(x).upper() for x in body.split(',') if x.strip()])
                elif val == '' or val is None:
                    in_methods_list = True
                    methods_indent = len(kv.group('indent'))
                else:
                    current_methods.append(_strip_quotes(val).upper())
                anchor_line = idx
                continue
            if key in PATH_KEYS:
                if val == '' or val is None:
                    in_paths_list = True
                    paths_indent = len(kv.group('indent'))
                else:
                    current_paths.append(_strip_quotes(val))
                anchor_line = idx
                continue

    flush()
    items.sort(key=lambda x: (x['path_or_name'], x['method']))
    return items


def find_yaml_includes(text: str) -> List[str]:
    """Best-effort include/resource extractor for YAML files.
    Supports:
      - resource: path_or_dir
      - imports: [file1.yaml, file2.yaml]
      - files: [file1.yaml, file2.yaml]
      - include: (list) / includes: (list)
    Returns raw values as found (caller must resolve relative to the YAML file directory).
    """
    out: List[str] = []
    if not text:
        return out
    lines = text.splitlines()
    in_list = False
    list_indent: Optional[int] = None

    def end_list():
        nonlocal in_list, list_indent
        in_list = False
        list_indent = None

    for line in lines:
        m_res = RESOURCE_INLINE.match(line)
        if m_res:
            out.append(_strip_quotes(m_res.group('val')))
            end_list()
            continue
        if IMPORTS_KEY.match(line) or FILES_KEY.match(line) or INCLUDE_KEY.match(line):
            in_list = True
            list_indent = len(line) - len(line.lstrip(' '))
            continue
        if in_list:
            m_item = LIST_ITEM.match(line)
            if m_item and (list_indent is None or len(m_item.group('indent')) >= list_indent):
                out.append(_strip_quotes(m_item.group('val')))
                continue
            else:
                end_list()
    return out
