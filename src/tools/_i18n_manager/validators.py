def validate_params(p):
    op = p.get('operation')
    if not op:
        raise ValueError('operation is required')

    if op not in {'list_langs', 'get_keys', 'upsert_keys', 'delete_keys', 'rename_key', 'upsert_key_all_langs'}:
        raise ValueError('invalid operation')

    if op in {'get_keys'}:
        if not p.get('lang'):
            raise ValueError('lang is required for get_keys')

    if op in {'upsert_keys'}:
        if not (p.get('lang') or p.get('languages')):
            raise ValueError('lang or languages required for upsert_keys')
        if not p.get('entries'):
            raise ValueError('entries required for upsert_keys')

    if op in {'delete_keys'}:
        if not (p.get('lang') or p.get('languages')):
            raise ValueError('lang or languages required for delete_keys')
        if not p.get('keys'):
            raise ValueError('keys required for delete_keys')

    if op in {'rename_key'}:
        if not p.get('from_key') or not p.get('to_key'):
            raise ValueError('from_key and to_key required for rename_key')

    if op in {'upsert_key_all_langs'}:
        if not p.get('target_key'):
            raise ValueError('target_key required for upsert_key_all_langs')
        if not p.get('values_by_lang'):
            raise ValueError('values_by_lang required for upsert_key_all_langs')
