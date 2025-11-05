export const __meta = { standalone: true, code: 'ha-Latn', flag: '🇳🇬', native: 'Hausa' };
export default {
  lang: { 'ha-Latn': 'Hausa' },
  common: {
    process: 'Tsari', details: 'Cikakkun bayanai', tools_mcp: 'Kayan aiki na MCP:', last_step: 'Mataki na ƙarshe',
    edit_identity: 'Duba/gyara asali', close: 'Rufe', start_debug: 'Fara (gyara kuskure)', start_observe: 'Fara (kallo)',
    step: 'Mataki', continue: 'Ci gaba', stop: 'Tsaya', copy_in: 'Kwafi IN', copy_out: 'Kwafi OUT', copy_err: 'Kwafi kuskure',
    error_network: 'Kuskuren cibiyar sadarwa', error_action: 'Aiki ya gaza', ok: 'To', current_sg: 'Subgraf na yanzu',
    chat: 'Hira', worker_status: 'Matsayin ma'aikaci', save: 'Ajiye', send: 'Aika'
  },
  header: { title: 'Ma'aikata & Shugabanni', add_leader: '+ Ƙara shugaba', add_worker: '+ Ƙara ma'aikaci', leader: 'Shugaba:' },
  kpis: { workers: 'MA'AIKATA', actifs: 'MASU AIKI', steps24h: 'MATAKAI (24S)', tokens24h: 'TOKENS (24S)', qualite7j: 'INGANCI (7K)' },
  toolbar: {
    process: 'Tsari', current: 'Subgraf na yanzu', overview: 'Bayyani', hide_start: 'ɓoye START', hide_end: 'ɓoye END',
    labels: 'alamomi', follow_sg: 'bi SG', mode_observe: 'Kallo', mode_debug: 'Kwararan gyara kuskure',
    current_sg_btn: 'SG na yanzu', display: 'Nuni:', mode: 'Yanayi:'
  },
  modal: { process_title: 'Tsari —' },
  status: {
    panel_title: 'Matsayi da ma'auni', running: 'Yana gudana', starting: 'Yana farawa', failed: 'Ya gaza',
    completed: 'An kammala', canceled: 'An soke', idle: 'Yana jiɓi', unknown: 'Ba a sani ba'
  },
  io: { title: 'Shigarwa/Fitarwa na node', in: 'IN', out: 'OUT', error: 'KUSKURE' },
  config: {
    title: 'Tsarin tsari', general: 'Gaba ɗaya', params: 'Sigogi', docs: 'Takardun bayanai',
    doc_title: 'Taken', doc_desc: 'Bayani', none: 'Babu tsari'
  },
  graph: {
    error_title: 'Graph', unavailable: 'Graph bai samuwa ba', aria_label: 'Mermaid graph',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'kuskuren nunawa'
  },
  node_menu: {
    aria_actions: 'Ayyukan node', open_sg: 'Buɗe subgraf', run_until: 'Gudanar har',
    break_add: 'Ƙara wurin tsayawa', break_remove: 'Cire wurin tsayawa', inspect: 'Bincika'
  },
  control_inputs: {
    debug_label: 'Gyara kuskure:', node_id: 'ID node', when: 'Sharadi', when_always: 'koyaushe',
    when_success: 'nasara', when_fail: 'gazawa', when_retry: 'sake gwadawa',
    run_until: 'Gudanar har', break_add: 'Ƙara tsayawa', break_remove: 'Cire tsayawa'
  },
  chat: {
    leader_panel_title: 'Shugaba — Hira', placeholder: 'Saƙo...', tools_trace: 'Duba sawun kayan aiki',
    error_history: 'Loda tarihi ya gaza', empty_reply: '(amsa mara kyau)', global: 'Hira ta duniya',
    error_history_global: 'Loda tarihin duniya ya gaza', you: 'Kai', assistant: 'LLM'
  },
  leader_global: {
    title: 'Shugaba — Hira ta duniya', select_label: 'Shugaba:', select_aria: 'Zaɓi shugaba',
    display: 'Sunan nuni', role: 'Matsayi', persona: 'Hali', persona_ph: 'Mai tsara ma'aikata',
    none_detected: '(babu shugaba)'
  },
  leader_identity_panel: {
    no_leader: 'Ba a sanya shugaba ba', error_read: 'Karanta asali ya gaza', refresh: 'Sabunta',
    display: 'Sunan nuni', role: 'Matsayi', persona: 'Hali', persona_ph: 'Mai tsara ma'aikata',
    global_chat: 'Hira ta duniya', leader_workers: 'Ma'aikatan shugaba', loading: 'Ana lodawa…',
    none_attached: 'Babu ma'aikaci da aka haɗa', error_load: 'Kuskuren lodawa'
  },
  list: { title: 'Ma'aikata', view: 'Duba' },
  config_editor: {
    tabs_simple: 'Mai sauƙi', tabs_json: 'JSON', beautify: 'Kyautata', minify: 'Rage',
    validate: 'Tabbatar', json_valid: 'JSON daidai', json_invalid: 'JSON ba daidai ba',
    complex_only_json: 'Wasu filayen hadaddun ana iya gyara su a cikin JSON kawai'
  },
  leader_section: { edit_identity_hint: 'Gyara asali (danna)' },
  replay: {
    title: 'Sake kunna (injin lokaci)', load_run: 'Loda aiki', play: 'Kunna', stop: 'Tsaya',
    error_runs: 'Loda ayyuka ya gaza', error_steps: 'Loda matakai ya gaza',
    view_node: 'Duba wannan node', live_announce_step: 'Ana kunna mataki {idx}/{total}: {nodeId}'
  }
};
