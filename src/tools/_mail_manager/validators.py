def validate_params(p: dict) -> dict:
    p = dict(p or {})
    if 'operation' not in p:
        p['operation'] = 'start'
    if p['operation'] not in {'start','stop','status'}:
        raise ValueError('operation invalide')

    if p['operation'] == 'start':
        name = (p.get('worker_name') or '').strip()
        if not name:
            raise ValueError('worker_name requis')
        p['worker_name'] = name
        if not p.get('mailboxes') or not isinstance(p['mailboxes'], list):
            raise ValueError('mailboxes requis (array)')
        p.setdefault('folders', ['INBOX'])
        p.setdefault('poll_interval_minutes', 10)
        p.setdefault('mark_read', True)
        llm_model = p.get('llm_model') or 'gpt-5-mini'
        p['llm_model'] = llm_model.strip()
    return p
