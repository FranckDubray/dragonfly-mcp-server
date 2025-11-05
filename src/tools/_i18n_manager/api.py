from .validators import validate_params
from .core import (
    list_langs,
    get_keys,
    upsert_keys,
    delete_keys,
    rename_key,
    upsert_key_all_langs,
)


def run(**params):
    try:
        op = params.get('operation')
        validate_params(params)

        if op == 'list_langs':
            langs = list_langs(params.get('root_dir'), params.get('pattern', '*.{json,js}'), params.get('format', 'auto'))
            limit = int(params.get('limit', 50))
            truncated = False
            total = len(langs)
            if total > limit:
                langs = langs[:limit]
                truncated = True
            return {
                'languages': langs,
                'total_count': total,
                'returned_count': len(langs),
                'truncated': truncated
            }

        elif op == 'get_keys':
            lang = params.get('lang')
            limit = int(params.get('limit', 50))
            keys = params.get('keys')
            result = get_keys(params.get('root_dir'), params.get('pattern', '*.{json,js}'), lang, keys, limit, params.get('format', 'auto'))
            return result

        elif op == 'upsert_keys':
            result = upsert_keys(
                root_dir=params.get('root_dir'),
                pattern=params.get('pattern', '*.{json,js}'),
                languages=params.get('languages') or ([params.get('lang')] if params.get('lang') else None),
                entries=params.get('entries', []),
                conflict=params.get('conflict', 'overwrite'),
                dry_run=bool(params.get('dry_run', False)),
                backup=bool(params.get('backup', True)),
                sort_keys=bool(params.get('sort_keys', True)),
                remove_empty=bool(params.get('remove_empty_objects', True)),
                fmt=params.get('format', 'auto'),
            )
            return result

        elif op == 'delete_keys':
            result = delete_keys(
                root_dir=params.get('root_dir'),
                pattern=params.get('pattern', '*.{json,js}'),
                languages=params.get('languages') or ([params.get('lang')] if params.get('lang') else None),
                keys=params.get('keys', []),
                dry_run=bool(params.get('dry_run', False)),
                backup=bool(params.get('backup', True)),
                remove_empty=bool(params.get('remove_empty_objects', True)),
                fmt=params.get('format', 'auto'),
            )
            return result

        elif op == 'rename_key':
            result = rename_key(
                root_dir=params.get('root_dir'),
                pattern=params.get('pattern', '*.{json,js}'),
                languages=params.get('languages'),
                from_key=params.get('from_key'),
                to_key=params.get('to_key'),
                conflict=params.get('conflict', 'overwrite'),
                dry_run=bool(params.get('dry_run', False)),
                backup=bool(params.get('backup', True)),
                sort_keys=bool(params.get('sort_keys', True)),
                fmt=params.get('format', 'auto'),
            )
            return result

        elif op == 'upsert_key_all_langs':
            result = upsert_key_all_langs(
                root_dir=params.get('root_dir'),
                pattern=params.get('pattern', '*.{json,js}'),
                target_key=params.get('target_key'),
                values_by_lang=params.get('values_by_lang', []),
                default_lang=params.get('default_lang'),
                conflict=params.get('conflict', 'overwrite'),
                dry_run=bool(params.get('dry_run', False)),
                backup=bool(params.get('backup', True)),
                sort_keys=bool(params.get('sort_keys', True)),
                fmt=params.get('format', 'auto'),
            )
            return result

        else:
            return { 'error': 'Unknown operation', 'operation': op }

    except Exception as e:
        # Erreur contrôlée pour l'API tool
        return { 'error': str(e), 'type': type(e).__name__ }
