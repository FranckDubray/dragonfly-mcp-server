export const __meta = { standalone: true, code: 'et', flag: '🇪🇪', native: 'Eesti' };
export default {
  lang: { et: 'Eesti' },
  common: {
    process: 'Protsess', details: 'Üksikasjad', tools_mcp: 'MCP tööriistad:', last_step: 'Viimane samm',
    edit_identity: 'Vaata/muuda identiteeti', close: 'Sulge', start_debug: 'Alusta (silumine)', start_observe: 'Alusta (jälgimine)',
    step: 'Samm', continue: 'Jätka', stop: 'Peata', copy_in: 'Kopeeri IN', copy_out: 'Kopeeri OUT', copy_err: 'Kopeeri viga',
    error_network: 'Võrgu viga', error_action: 'Tegevus ebaõnnestus', ok: 'OK', current_sg: 'Praegune alamgraaf',
    chat: 'Vestlus', worker_status: 'Töötaja olek', save: 'Salvesta', send: 'Saada'
  },
  header: { title: 'Töötajad ja juhid', add_leader: '+ Lisa juht', add_worker: '+ Lisa töötaja', leader: 'Juht:' },
  kpis: { workers: 'TÖÖTAJAD', actifs: 'AKTIIVSED', steps24h: 'SAMME (24H)', tokens24h: 'TOKENID (24H)', qualite7j: 'KVALITEET (7P)' },
  toolbar: {
    process: 'Protsess', current: 'Praegune alamgraaf', overview: 'Ülevaade', hide_start: 'peida START', hide_end: 'peida END',
    labels: 'sildid', follow_sg: 'jälgi SG', mode_observe: 'Jälgimine', mode_debug: 'Silumise voog',
    current_sg_btn: 'Praegune SG', display: 'Kuva:', mode: 'Režiim:'
  },
  modal: { process_title: 'Protsess —' },
  status: {
    panel_title: 'Olek ja mõõdikud', running: 'Töötab', starting: 'Käivitub', failed: 'Ebaõnnestus',
    completed: 'Lõpetatud', canceled: 'Tühistatud', idle: 'Seisak', unknown: 'Tundmatu'
  },
  io: { title: 'Sõlme sisendid/väljundid', in: 'IN', out: 'OUT', error: 'VIGA' },
  config: {
    title: 'Protsessi konfiguratsioon', general: 'Üldine', params: 'Parameetrid', docs: 'Dokumentatsioon',
    doc_title: 'Pealkiri', doc_desc: 'Kirjeldus', none: 'Konfiguratsioon puudub'
  },
  graph: {
    error_title: 'Graaf', unavailable: 'Graaf pole saadaval', aria_label: 'Mermaid graaf',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'renderdamise viga'
  },
  node_menu: {
    aria_actions: 'Sõlme tegevused', open_sg: 'Ava alamgraaf', run_until: 'Käivita kuni',
    break_add: 'Lisa katkestuspunkt', break_remove: 'Eemalda katkestuspunkt', inspect: 'Kontrolli'
  },
  control_inputs: {
    debug_label: 'Silumine:', node_id: 'Sõlme ID', when: 'Tingimus', when_always: 'alati',
    when_success: 'õnnestumine', when_fail: 'ebaõnnestumine', when_retry: 'uuesti proovimine',
    run_until: 'Käivita kuni', break_add: 'Lisa katkestus', break_remove: 'Eemalda katkestus'
  },
  chat: {
    leader_panel_title: 'Juht — Vestlus', placeholder: 'Sõnum...', tools_trace: 'Vaata tööriista jälgi',
    error_history: 'Ajaloo laadimine ebaõnnestus', empty_reply: '(tühi vastus)', global: 'Globaalne vestlus',
    error_history_global: 'Globaalse ajaloo laadimine ebaõnnestus', you: 'Sina', assistant: 'LLM'
  },
  leader_global: {
    title: 'Juht — Globaalne vestlus', select_label: 'Juht:', select_aria: 'Vali juht',
    display: 'Kuvatav nimi', role: 'Roll', persona: 'Persoon', persona_ph: 'Töötajate orkestreerimise',
    none_detected: '(juhti ei ole)'
  },
  leader_identity_panel: {
    no_leader: 'Juhti pole määratud', error_read: 'Identiteedi lugemine ebaõnnestus', refresh: 'Värskenda',
    display: 'Kuvatav nimi', role: 'Roll', persona: 'Persoon', persona_ph: 'Töötajate orkestreerimise',
    global_chat: 'Globaalne vestlus', leader_workers: 'Juhi töötajad', loading: 'Laadimine…',
    none_attached: 'Töötajat pole lisatud', error_load: 'Laadimise viga'
  },
  list: { title: 'Töötajad', view: 'Vaata' },
  config_editor: {
    tabs_simple: 'Lihtne', tabs_json: 'JSON', beautify: 'Ilusta', minify: 'Minimeeri',
    validate: 'Valideeri', json_valid: 'Kehtiv JSON', json_invalid: 'Kehtetu JSON',
    complex_only_json: 'Mõned keerulised väljad on muudetavad ainult JSON-is'
  },
  leader_section: { edit_identity_hint: 'Muuda identiteeti (klõpsa)' },
  replay: {
    title: 'Taasesitus (ajamašin)', load_run: 'Laadi käivitus', play: 'Esita', stop: 'Peata',
    error_runs: 'Käivituste laadimine ebaõnnestus', error_steps: 'Sammude laadimine ebaõnnestus',
    view_node: 'Vaata seda sõlme', live_announce_step: 'Esitatakse sammu {idx}/{total}: {nodeId}'
  }
};
