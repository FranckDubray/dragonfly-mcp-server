import os, re, json
try:
    import json5
except Exception:
    json5 = None


# More tolerant regex (handle comments between tokens)
EXPORT_DEFAULT_RE = re.compile(r"export\s+default(?:\s|/\*.*?\*/|//[^\n]*\n)*{", re.MULTILINE | re.DOTALL)
META_EXPORT_RE = re.compile(r"export\s+const\s+__meta\s*=\s*(?:\s|/\*.*?\*/|//[^\n]*\n)*{", re.MULTILINE | re.DOTALL)


def parse_locale_file(path, text, fmt):
    ext = os.path.splitext(path)[1].lower()
    if fmt == 'json' or (fmt == 'auto' and ext == '.json'):
        data = json.loads(text)
        code = os.path.splitext(os.path.basename(path))[0]
        return { 'format': 'json', 'code': code, 'meta': None, 'data': data }
    else:
        # es_module
        if json5 is None:
            raise RuntimeError("json5 is required to parse ES module i18n files. Please install 'json5'.")
        meta_obj = None
        # Extract meta block
        m = META_EXPORT_RE.search(text)
        if m:
            start = m.end() - 1
            end = _find_matching_brace(text, start)
            meta_str = text[start:end+1]
            meta_obj = json5.loads(meta_str)
        # Extract default export block
        d = EXPORT_DEFAULT_RE.search(text)
        if not d:
            raise RuntimeError("No export default { ... } found in ES module")
        start = d.end() - 1
        end = _find_matching_brace(text, start)
        data_str = text[start:end+1]
        data_obj = json5.loads(data_str)
        code = (meta_obj.get('code') if isinstance(meta_obj, dict) else None) or os.path.splitext(os.path.basename(path))[0]
        return { 'format': 'es_module', 'code': code, 'meta': meta_obj, 'data': data_obj }


def dump_locale_file(path, parsed, data):
    fmt = parsed.get('format')
    if fmt == 'json':
        return json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    else:
        meta = parsed.get('meta') or {}
        if 'code' not in meta or not meta['code']:
            meta['code'] = parsed.get('code') or os.path.splitext(os.path.basename(path))[0]
        meta_str = json.dumps(meta, ensure_ascii=False, indent=2)
        data_str = json.dumps(data, ensure_ascii=False, indent=2)
        return f"export const __meta = {meta_str};\nexport default {data_str};\n"


def _find_matching_brace(text, open_brace_pos):
    # open_brace_pos is position of '{'
    depth = 0
    in_single = False
    in_double = False
    in_backtick = False
    escape = False
    i = open_brace_pos
    while i < len(text):
        c = text[i]
        if escape:
            escape = False
        else:
            if in_single:
                if c == '\\':
                    escape = True
                elif c == "'":
                    in_single = False
            elif in_double:
                if c == '\\':
                    escape = True
                elif c == '"':
                    in_double = False
            elif in_backtick:
                if c == '\\':
                    escape = True
                elif c == '`':
                    in_backtick = False
            else:
                if c == "'":
                    in_single = True
                elif c == '"':
                    in_double = True
                elif c == '`':
                    in_backtick = True
                elif c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        return i
        i += 1
    raise ValueError('Unbalanced braces in ES module')


def flatten_dict(d, parent_key='', sep='.'):
    items = {}
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


def _split_path(path):
    # Supports escaping dot with \.
    parts = []
    buf = ''
    esc = False
    for ch in path:
        if esc:
            buf += ch
            esc = False
        else:
            if ch == '\\':
                esc = True
            elif ch == '.':
                parts.append(buf)
                buf = ''
            else:
                buf += ch
    if buf:
        parts.append(buf)
    return parts


def deep_get(data, path):
    cur = data
    for seg in _split_path(path):
        if not isinstance(cur, dict) or seg not in cur:
            return None
        cur = cur[seg]
    return cur


def deep_set(data, path, value):
    cur = data
    parts = _split_path(path)
    for seg in parts[:-1]:
        if seg not in cur or not isinstance(cur.get(seg), dict):
            cur[seg] = {}
        cur = cur[seg]
    cur[parts[-1]] = value


def deep_delete(data, path):
    cur = data
    parts = _split_path(path)
    for seg in parts[:-1]:
        if seg not in cur or not isinstance(cur.get(seg), dict):
            return False
        cur = cur[seg]
    if parts[-1] in cur:
        del cur[parts[-1]]
        return True
    return False


def deep_rename(data, from_key, to_key):
    val = deep_get(data, from_key)
    if val is None:
        return False
    deep_set(data, to_key, val)
    deep_delete(data, from_key)
    return True


def prune_empty(obj):
    if not isinstance(obj, dict):
        return obj
    keys = list(obj.keys())
    for k in keys:
        v = obj[k]
        if isinstance(v, dict):
            prune_empty(v)
            if len(v) == 0:
                del obj[k]
    return obj


def sort_keys_recursive(d):
    if isinstance(d, dict):
        return {k: sort_keys_recursive(d[k]) for k in sorted(d.keys())}
    return d
