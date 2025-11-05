export const __meta = { standalone: true, code: 'hu', flag: '🇭🇺', native: 'Magyar' };
export default {
  lang: { hu: 'Magyar' },
  common: {
    process: 'Folyamat', details: 'Részletek', tools_mcp: 'MCP eszközök:', last_step: 'Utolsó lépés',
    edit_identity: 'Identitás megtekintése/szerkesztése', close: 'Bezárás', start_debug: 'Indítás (hibakeresés)', start_observe: 'Indítás (megfigyelés)',
    step: 'Lépés', continue: 'Folytatás', stop: 'Leállítás', copy_in: 'IN másolása', copy_out: 'OUT másolása', copy_err: 'Hiba másolása',
    error_network: 'Hálózati hiba', error_action: 'Művelet sikertelen', ok: 'OK', current_sg: 'Aktuális részgráf',
    chat: 'Csevegés', worker_status: 'Worker állapot', save: 'Mentés', send: 'Küldés'
  },
  header: { title: 'Munkavállalók és vezetők', add_leader: '+ Vezető hozzáadása', add_worker: '+ Munkavállaló hozzáadása', leader: 'Vezető:' },
  kpis: { workers: 'MUNKAVÁLLALÓK', actifs: 'AKTÍV', steps24h: 'LÉPÉSEK (24Ó)', tokens24h: 'TOKENEK (24Ó)', qualite7j: 'MINŐSÉG (7N)' },
  toolbar: {
    process: 'Folyamat', current: 'Aktuális részgráf', overview: 'Áttekintés', hide_start: 'START elrejtése', hide_end: 'END elrejtése',
    labels: 'címkék', follow_sg: 'SG követése', mode_observe: 'Megfigyelés', mode_debug: 'Hibakeresési stream',
    current_sg_btn: 'Aktuális SG', display: 'Megjelenítés:', mode: 'Mód:'
  },
  modal: { process_title: 'Folyamat —' },
  status: {
    panel_title: 'Állapot és metrikák', running: 'Fut', starting: 'Indul', failed: 'Sikertelen',
    completed: 'Kész', canceled: 'Megszakítva', idle: 'Tétlen', unknown: 'Ismeretlen'
  },
  io: { title: 'Csomópont be-/kimenetek', in: 'IN', out: 'OUT', error: 'HIBA' },
  config: {
    title: 'Folyamat konfigurációja', general: 'Általános', params: 'Paraméterek', docs: 'Dokumentáció',
    doc_title: 'Cím', doc_desc: 'Leírás', none: 'Nincs elérhető konfiguráció'
  },
  graph: {
    error_title: 'Gráf', unavailable: 'Gráf nem érhető el', aria_label: 'Mermaid gráf',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'renderelési hiba'
  },
  node_menu: {
    aria_actions: 'Csomópont műveletek', open_sg: 'Részgráf megnyitása', run_until: 'Futtatás eddig',
    break_add: 'Töréspontot hozzáadása', break_remove: 'Töréspont eltávolítása', inspect: 'Vizsgálat'
  },
  control_inputs: {
    debug_label: 'Hibakeresés:', node_id: 'Csomópont ID', when: 'Feltétel', when_always: 'mindig',
    when_success: 'sikeres', when_fail: 'sikertelen', when_retry: 'újrapróbálás',
    run_until: 'Futtatás eddig', break_add: 'Töréspont hozzáadása', break_remove: 'Töréspont eltávolítása'
  },
  chat: {
    leader_panel_title: 'Vezető — Csevegés', placeholder: 'Üzenet...', tools_trace: 'Eszköz nyomok megtekintése',
    error_history: 'Előzmények betöltése sikertelen', empty_reply: '(üres válasz)', global: 'Globális csevegés',
    error_history_global: 'Globális előzmények betöltése sikertelen', you: 'Ön', assistant: 'LLM'
  },
  leader_global: {
    title: 'Vezető — Globális csevegés', select_label: 'Vezető:', select_aria: 'Válasszon vezetőt',
    display: 'Megjelenített név', role: 'Szerep', persona: 'Személyiség', persona_ph: 'Munkavállalók koordinátora',
    none_detected: '(nincs vezető)'
  },
  leader_identity_panel: {
    no_leader: 'Nincs hozzárendelt vezető', error_read: 'Identitás olvasása sikertelen', refresh: 'Frissítés',
    display: 'Megjelenített név', role: 'Szerep', persona: 'Személyiség', persona_ph: 'Munkavállalók koordinátora',
    global_chat: 'Globális csevegés', leader_workers: 'Vezető munkavállalói', loading: 'Betöltés…',
    none_attached: 'Nincs csatolt munkavállaló', error_load: 'Betöltési hiba'
  },
  list: { title: 'Munkavállalók', view: 'Megtekintés' },
  config_editor: {
    tabs_simple: 'Egyszerű', tabs_json: 'JSON', beautify: 'Formázás', minify: 'Tömörítés',
    validate: 'Validálás', json_valid: 'Érvényes JSON', json_invalid: 'Érvénytelen JSON',
    complex_only_json: 'Néhány összetett mező csak JSON-ban szerkeszthető'
  },
  leader_section: { edit_identity_hint: 'Identitás szerkesztése (kattintás)' },
  replay: {
    title: 'Visszajátszás (időgép)', load_run: 'Futtatás betöltése', play: 'Lejátszás', stop: 'Leállítás',
    error_runs: 'Futtatások betöltése sikertelen', error_steps: 'Lépések betöltése sikertelen',
    view_node: 'Csomópont megtekintése', live_announce_step: 'Lépés lejátszása {idx}/{total}: {nodeId}'
  }
};
