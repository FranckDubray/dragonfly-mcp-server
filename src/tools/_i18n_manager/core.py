import os, re, json, datetime
from .services.fs import glob_locales, read_text, write_atomic
from .utils import (
    parse_locale_file,
    dump_locale_file,
    flatten_dict,
    deep_set,
    deep_delete,
    deep_get,
    deep_rename,
    prune_empty,
    sort_keys_recursive,
)


MAX_PREVIEW_FILES = 3


def _parse_meta_only(path, text, fmt):
    # Fast path for list_langs: avoid parsing full default export
    ext = os.path.splitext(path)[1].lower()
    if fmt == 'json' or (fmt == 'auto' and ext == '.json'):
        code = os.path.splitext(os.path.basename(path))[0]
        return {'code': code, 'meta': None}

    # ES module: try to extract __meta fields without full JSON5 parse
    try:
        from .utils import META_EXPORT_RE, _find_matching_brace
        m = META_EXPORT_RE.search(text)
        meta_obj = None
        code = None
        native = None
        flag = None
        standalone = None
        if m:
            start = m.end() - 1
            end = _find_matching_brace(text, start)
            meta_slice = text[start:end+1]
            # Try robust JSON5 parse first
            try:
                import json5  # type: ignore
                meta_obj = json5.loads(meta_slice)
                code = meta_obj.get('code') if isinstance(meta_obj, dict) else None
                native = meta_obj.get('native') if isinstance(meta_obj, dict) else None
                flag = meta_obj.get('flag') if isinstance(meta_obj, dict) else None
                standalone = meta_obj.get('standalone') if isinstance(meta_obj, dict) else None
            except Exception:
                # Fallback: permissive regex extraction inside the slice
                # Matches code: 'fr' or code: "fr"
                m_code = re.search(r"code\s*:\s*(['\"])\s*([^'\"]+)\s*\1", meta_slice)
                if m_code:
                    code = m_code.group(2).strip()
                m_native = re.search(r"native\s*:\s*(['\"])\s*(.*?)\s*\1", meta_slice)
                if m_native:
                    native = m_native.group(2)
                m_flag = re.search(r"flag\s*:\s*(['\"])\s*(.*?)\s*\1", meta_slice)
                if m_flag:
                    flag = m_flag.group(2)
                m_standalone = re.search(r"standalone\s*:\s*(true|false)", meta_slice, re.IGNORECASE)
                if m_standalone:
                    standalone = (m_standalone.group(1).lower() == 'true')
        if not code:
            code = os.path.splitext(os.path.basename(path))[0]
        meta = {}
        if native is not None:
            meta['native'] = native
        if flag is not None:
            meta['flag'] = flag
        if standalone is not None:
            meta['standalone'] = standalone
        if code and 'code' not in meta:
            meta['code'] = code
        return {'code': code, 'meta': meta if meta else None}
    except Exception:
        code = os.path.splitext(os.path.basename(path))[0]
        return {'code': code, 'meta': None}


def list_langs(root_dir, pattern, fmt):
    files = glob_locales(root_dir, pattern)
    langs = []
    for f in files:
        text = read_text(f)
        info = _parse_meta_only(f, text, fmt)
        code = info.get('code')
        m = info.get('meta') or {}
        # If meta is missing, try full parse to enrich (best-effort)
        if not m:
            try:
                parsed_full = parse_locale_file(f, text, fmt)
                m = parsed_full.get('meta') or {}
                code = parsed_full.get('code') or code
            except Exception:
                pass
        langs.append({
            'code': code,
            'file': os.path.basename(f),
            'native': m.get('native'),
            'flag': m.get('flag'),
            'standalone': m.get('standalone'),
        })
    return langs


def _find_file_by_lang(root_dir, pattern, fmt, lang):
    files = glob_locales(root_dir, pattern)
    # 1) Fast-path by filename match (avoid parsing all files)
    for f in files:
        base = os.path.splitext(os.path.basename(f))[0]
        if base == lang:
            try:
                text = read_text(f)
                parsed = parse_locale_file(f, text, fmt)
                if parsed.get('code') == lang:
                    return f, parsed
            except Exception:
                # Fall back to full scan
                break
    # 2) Fallback: scan with per-file try/except
    for f in files:
        try:
            text = read_text(f)
            parsed = parse_locale_file(f, text, fmt)
            if parsed.get('code') == lang:
                return f, parsed
        except Exception:
            continue
    return None, None


def get_keys(root_dir, pattern, lang, keys, limit, fmt):
    f, parsed = _find_file_by_lang(root_dir, pattern, fmt, lang)
    if not f:
        return { 'error': f"Language '{lang}' not found" }
    data = parsed['data']
    items = []
    if keys:
        for p in keys:
            v = deep_get(data, p)
            if v is not None:
                items.append({ 'path': p, 'value': v })
    else:
        flat = flatten_dict(data)
        for k, v in flat.items():
            items.append({ 'path': k, 'value': v })
    total = len(items)
    truncated = False
    if total > limit:
        items = items[:limit]
        truncated = True
    return {
        'lang': lang,
        'items': items,
        'total_count': total,
        'returned_count': len(items),
        'truncated': truncated,
    }


def _apply_and_write(file_parsed_list, apply_fn, sort_keys=True, dry_run=False, backup=True):
    changed = []
    previews = []
    for (f, parsed) in file_parsed_list:
        before = parsed['data']
        data = json.loads(json.dumps(before))  # deep copy via json
        changed_flag = apply_fn(data)
        if changed_flag:
            if sort_keys:
                data = sort_keys_recursive(data)
            if dry_run:
                if len(previews) < MAX_PREVIEW_FILES:
                    previews.append({
                        'file': os.path.basename(f),
                        'before_sample': list(flatten_dict(before).items())[:5],
                        'after_sample': list(flatten_dict(data).items())[:5],
                    })
            else:
                content = dump_locale_file(f, parsed, data)
                write_atomic(f, content, backup=backup)
            changed.append(os.path.basename(f))
    return changed, previews


def upsert_keys(root_dir, pattern, languages, entries, conflict, dry_run, backup, sort_keys, remove_empty, fmt):
    files = glob_locales(root_dir, pattern)
    lang_set = set(languages) if languages else None
    file_parsed = []
    for f in files:
        text = read_text(f)
        parsed = parse_locale_file(f, text, fmt)
        code = parsed.get('code')
        if (lang_set is None) or (code in lang_set):
            file_parsed.append((f, parsed))

    def apply_fn(data):
        changed = False
        for ent in entries:
            path = ent['path']
            val = ent['value']
            existing = deep_get(data, path)
            if existing is None:
                deep_set(data, path, val)
                changed = True
            else:
                if conflict == 'overwrite':
                    if existing != val:
                        deep_set(data, path, val)
                        changed = True
                elif conflict == 'skip':
                    continue
                elif conflict == 'abort':
                    raise RuntimeError(f"Conflict on existing key '{path}'")
        if remove_empty:
            prune_empty(data)
        return changed

    changed, previews = _apply_and_write(file_parsed, apply_fn, sort_keys, dry_run, backup)
    return {
        'changed_files': changed,
        'changed_count': len(changed),
        'dry_run': dry_run,
        'preview': previews if dry_run else None,
    }


def delete_keys(root_dir, pattern, languages, keys, dry_run, backup, remove_empty, fmt):
    files = glob_locales(root_dir, pattern)
    lang_set = set(languages) if languages else None
    file_parsed = []
    for f in files:
        text = read_text(f)
        parsed = parse_locale_file(f, text, fmt)
        code = parsed.get('code')
        if (lang_set is None) or (code in lang_set):
            file_parsed.append((f, parsed))

    def apply_fn(data):
        changed = False
        for p in keys:
            if deep_get(data, p) is not None:
                deep_delete(data, p)
                changed = True
        if remove_empty:
            prune_empty(data)
        return changed

    changed, previews = _apply_and_write(file_parsed, apply_fn, True, dry_run, backup)
    return {
        'changed_files': changed,
        'changed_count': len(changed),
        'dry_run': dry_run,
        'preview': previews if dry_run else None,
    }


def rename_key(root_dir, pattern, languages, from_key, to_key, conflict, dry_run, backup, sort_keys, fmt):
    files = glob_locales(root_dir, pattern)
    file_parsed = []
    langs = set(languages) if languages else None
    for f in files:
        text = read_text(f)
        parsed = parse_locale_file(f, text, fmt)
        if (langs is None) or (parsed.get('code') in langs):
            file_parsed.append((f, parsed))

    def apply_fn(data):
        src = deep_get(data, from_key)
        if src is None:
            return False
        dst_exists = deep_get(data, to_key) is not None
        if dst_exists:
            if conflict == 'abort':
                raise RuntimeError(f"Destination key exists '{to_key}'")
            elif conflict == 'skip':
                return False
        deep_set(data, to_key, src)
        deep_delete(data, from_key)
        return True

    changed, previews = _apply_and_write(file_parsed, apply_fn, sort_keys, dry_run, backup)
    return {
        'changed_files': changed,
        'changed_count': len(changed),
        'dry_run': dry_run,
        'preview': previews if dry_run else None,
    }


def upsert_key_all_langs(root_dir, pattern, target_key, values_by_lang, default_lang, conflict, dry_run, backup, sort_keys, fmt):
    files = glob_locales(root_dir, pattern)
    map_vals = { v['lang']: v['value'] for v in values_by_lang }
    file_parsed = []
    for f in files:
        text = read_text(f)
        parsed = parse_locale_file(f, text, fmt)
        file_parsed.append((f, parsed))

    def apply_fn(data, code=None):
        return False

    def apply_fn_factory(code):
        def fn(data):
            val = map_vals.get(code)
            if val is None and default_lang:
                val = map_vals.get(default_lang)
            if val is None:
                # pas d'écriture pour cette langue
                return False
            existing = deep_get(data, target_key)
            if existing is None:
                deep_set(data, target_key, val)
                return True
            else:
                if conflict == 'overwrite':
                    if existing != val:
                        deep_set(data, target_key, val)
                        return True
                    return False
                elif conflict == 'skip':
                    return False
                elif conflict == 'abort':
                    raise RuntimeError(f"Conflict on existing key '{target_key}' for lang '{code}'")
        return fn

    changed = []
    previews = []
    for (f, parsed) in file_parsed:
        before = parsed['data']
        data = json.loads(json.dumps(before))
        code = parsed.get('code')
        changed_flag = apply_fn_factory(code)(data)
        if changed_flag:
            if sort_keys:
                data = sort_keys_recursive(data)
            if dry_run:
                if len(previews) < MAX_PREVIEW_FILES:
                    previews.append({
                        'file': os.path.basename(f),
                        'before_sample': list(flatten_dict(before).items())[:5],
                        'after_sample': list(flatten_dict(data).items())[:5],
                    })
            else:
                content = dump_locale_file(f, parsed, data)
                write_atomic(f, content, backup=backup)
            changed.append(os.path.basename(f))

    return {
        'changed_files': changed,
        'changed_count': len(changed),
        'dry_run': dry_run,
        'preview': previews if dry_run else None,
    }
