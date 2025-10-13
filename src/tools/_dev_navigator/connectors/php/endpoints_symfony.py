import re
from typing import List, Dict, Optional

from ...services.anchors import make_anchor
from .yaml_symfony_routes import extract_yaml_symfony

# Symfony endpoints extractor: PHP attributes #[Route] + YAML routes

ATTR_CLASS = re.compile(r"^\s*#\[Route\(([^\)]*)\)\]\s*$")
CLASS_DECL = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\b")
ATTR_METHOD = re.compile(r"^\s*#\[Route\(([^\)]*)\)\]\s*$")
METHOD_DECL = re.compile(r"^\s*public\s+function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _parse_attr_args(argstr: str) -> Dict[str, object]:
    out: Dict[str, object] = {}
    m = re.search(r"'(/[^']*)'|\"(/[^\"]*)\"", argstr)
    if m:
        out['path'] = m.group(1) or m.group(2)
    m = re.search(r"\bpath\s*:\s*'(/[^']*)'|\bpath\s*:\s*\"(/[^\"]*)\"", argstr)
    if m and (m.group(1) or m.group(2)):
        out['path'] = m.group(1) or m.group(2)
    m = re.search(r"methods\s*:\s*\[([^\]]*)\]", argstr)
    if m:
        methods_raw = m.group(1)
        methods = [s.strip().strip("'\"").upper() for s in methods_raw.split(',') if s.strip()]
        out['methods'] = methods
    return out


def _join_prefix_path(prefix: Optional[str], path: Optional[str]) -> Optional[str]:
    if not path and not prefix:
        return None
    if not prefix:
        return path
    if not path:
        return prefix
    if prefix.endswith('/') and path.startswith('/'):
        return prefix[:-1] + path
    if not prefix.endswith('/') and not path.startswith('/'):
        return prefix + '/' + path
    return prefix + path


def extract_endpoints_symfony(text: str, relpath: str) -> List[Dict]:
    items: List[Dict] = []
    if not text:
        return items

    # PHP attribute mode
    class_prefix = ''
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        m_attr_class = ATTR_CLASS.match(line)
        if m_attr_class:
            args = _parse_attr_args(m_attr_class.group(1) or '')
            class_prefix = args.get('path', '') or class_prefix
            continue
        if CLASS_DECL.match(line):
            continue
        m_attr_method = ATTR_METHOD.match(line)
        if m_attr_method:
            args = _parse_attr_args(m_attr_method.group(1) or '')
            m_method_decl = None
            for j, ln in enumerate(lines[i:i+5], start=i):
                if METHOD_DECL.match(ln):
                    m_method_decl = j
                    break
            path = _join_prefix_path(class_prefix, args.get('path'))
            methods = args.get('methods') or ['ANY']
            if path:
                for meth in methods:
                    items.append({
                        'kind': 'http',
                        'method': str(meth).upper(),
                        'path_or_name': path,
                        'source_anchor': make_anchor(relpath, m_method_decl or i, 0),
                        'framework_hint': 'symfony'
                    })

    # YAML mode (delegated)
    items.extend(extract_yaml_symfony(text, relpath))

    items.sort(key=lambda x: (x['path_or_name'], x['method']))
    return items
