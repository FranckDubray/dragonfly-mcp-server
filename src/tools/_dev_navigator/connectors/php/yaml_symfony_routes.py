import re
from typing import List, Dict, Optional

from ...services.anchors import make_anchor

YAML_NAME = re.compile(r"^(?P<indent>\s*)([A-Za-z0-9_\.\-]+):\s*$")
YAML_PATH_INLINE = re.compile(r"^\s*path:\s*(?P<val>.+?)\s*$")
YAML_METHODS_INLINE = re.compile(r"^\s*methods:\s*\[(?P<vals>[^\]]*)\]\s*$")
YAML_METHODS_KEY = re.compile(r"^\s*methods:\s*$")
YAML_METHODS_SCALAR = re.compile(r"^\s*methods:\s*(?P<val>[^\[#][^#]*)$")
YAML_METHOD_ITEM = re.compile(r"^(?P<indent>\s*)-\s*(?P<val>.+?)\s*$")
YAML_PREFIX_INLINE = re.compile(r"^\s*prefix:\s*(?P<val>.+?)\s*$")
YAML_GLOBAL_PREFIX = re.compile(r"^(?P<indent>\s*)prefix:\s*(?P<val>.+?)\s*$")


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        return s[1:-1]
    return s


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


def extract_yaml_symfony(text: str, relpath: str) -> List[Dict]:
    items: List[Dict] = []
    if not text:
        return items

    lines = text.splitlines()
    current_path: Optional[str] = None
    current_methods: List[str] = []
    current_prefix: Optional[str] = None
    global_prefix: Optional[str] = None
    block_indent_level: Optional[int] = None
    in_methods_list: bool = False
    methods_indent_level: Optional[int] = None
    anchor_line_for_block: int = 1

    def flush(anchor_line: int):
        nonlocal current_path, current_methods, current_prefix
        if current_path:
            full_path = _join_prefix_path(current_prefix or global_prefix, current_path)
            methods = current_methods or ['ANY']
            for m in methods:
                items.append({
                    'kind': 'http',
                    'method': m.upper(),
                    'path_or_name': _strip_quotes(full_path or ''),
                    'source_anchor': make_anchor(relpath, anchor_line, 0),
                    'framework_hint': 'symfony'
                })
        current_path = None
        current_methods = []
        current_prefix = None

    for idx, line in enumerate(lines, start=1):
        if block_indent_level is None:
            m_global = YAML_GLOBAL_PREFIX.match(line)
            if m_global and len(m_global.group('indent') or '') == 0:
                global_prefix = _strip_quotes(m_global.group('val'))
                continue

        m_name = YAML_NAME.match(line)
        if m_name and not line.strip().startswith('-'):
            if current_path or current_methods or current_prefix:
                flush(anchor_line_for_block)
            block_indent_level = len(m_name.group('indent'))
            in_methods_list = False
            methods_indent_level = None
            anchor_line_for_block = idx
            current_path = None
            current_methods = []
            current_prefix = global_prefix
            continue

        if block_indent_level is not None:
            leading_spaces = len(line) - len(line.lstrip(' '))
            if line.strip() and leading_spaces <= block_indent_level and not line.strip().startswith('-'):
                flush(anchor_line_for_block)
                block_indent_level = None
                in_methods_list = False
                methods_indent_level = None
                m_name2 = YAML_NAME.match(line)
                if m_name2:
                    block_indent_level = len(m_name2.group('indent'))
                    anchor_line_for_block = idx
                else:
                    m_global2 = YAML_GLOBAL_PREFIX.match(line)
                    if m_global2 and len(m_global2.group('indent') or '') == 0:
                        global_prefix = _strip_quotes(m_global2.group('val'))
                continue

            if in_methods_list:
                m_item = YAML_METHOD_ITEM.match(line)
                if m_item and (methods_indent_level is None or len(m_item.group('indent')) >= methods_indent_level):
                    val = _strip_quotes(m_item.group('val')).upper()
                    if val:
                        current_methods.append(val)
                    continue
                else:
                    in_methods_list = False
                    methods_indent_level = None

            m_path = YAML_PATH_INLINE.match(line)
            if m_path:
                current_path = _strip_quotes(m_path.group('val'))
                continue

            m_pref = YAML_PREFIX_INLINE.match(line)
            if m_pref:
                current_prefix = _strip_quotes(m_pref.group('val'))
                continue

            m_methods_inline = YAML_METHODS_INLINE.match(line)
            if m_methods_inline:
                raw = m_methods_inline.group('vals') or ''
                vals = [ _strip_quotes(s).upper() for s in raw.split(',') if s.strip() ]
                current_methods.extend(vals)
                continue

            m_methods_scalar = YAML_METHODS_SCALAR.match(line)
            if m_methods_scalar:
                val = _strip_quotes(m_methods_scalar.group('val')).upper()
                if val:
                    current_methods.append(val)
                continue

            if YAML_METHODS_KEY.match(line):
                in_methods_list = True
                methods_indent_level = leading_spaces
                continue

    if current_path or current_methods or current_prefix:
        flush(anchor_line_for_block)

    items.sort(key=lambda x: (x['path_or_name'], x['method']))
    return items
