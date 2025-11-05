export const __meta = { standalone: true, code: 'kmr-Latn', flag: '🇹🇷', native: 'Kurdî (Kurmanjî)' };
export default {
  lang: { 'kmr-Latn': 'Kurdî (Kurmanjî)' },
  header: { title: 'Karker û Serok', add_leader: '+ Serok lê zêde bike', add_worker: '+ Karker lê zêde bike', leader: 'Serok:' },
  common: {
    process: 'Pêvajoyê', details: 'Detayên', tools_mcp: 'Amûrên MCP:', last_step: 'Gav dawîn',
    edit_identity: 'Nasname bibîne/biguherîne', close: 'Bigre', start_debug: 'Dest pê bike (debug)', start_observe: 'Dest pê bike (şopandin)',
    step: 'Gav', continue: 'Berdewam bike', stop: 'Bisekinîne', copy_in: 'IN kopî bike', copy_out: 'OUT kopî bike', copy_err: 'Xeletî kopî bike',
    error_network: 'Xeletiya torê', error_action: 'Kiryar têk çû', ok: 'Baş e', current_sg: 'Grafika binî ya niha',
    chat: 'Sohbet', worker_status: 'Rewş', save: 'Tomar bike', send: 'Bişîne'
  },
  kpis: { workers: 'KARKER', actifs: 'ÇALAK', steps24h: 'GAV (24 SAET)', tokens24h: 'TOKEN (24 SAET)', qualite7j: 'KALÎTE (7 ROJ)' },
  toolbar: {
    process: 'Pêvajoyê', current: 'Grafika binî ya niha', overview: 'Giştî', hide_start: 'START veşêre', hide_end: 'END veşêre',
    labels: 'nîşan', follow_sg: 'SG bişopîne', mode_observe: 'Şopandin', mode_debug: 'Çema debug',
    current_sg_btn: 'SG niha', display: 'Nîşandan:', mode: 'Mod:'
  },
  modal: { process_title: 'Pêvajoyê —' },
  status: {
    panel_title: 'Rewş û pîvan', running: 'Dixebite', starting: 'Dest pê dike', failed: 'Têk çû',
    completed: 'Temam bû', canceled: 'Hat betalkirin', idle: 'Vetirsî', unknown: 'Nenas'
  },
  io: { title: 'Têketin/Derketin node', in: 'IN', out: 'OUT', error: 'XELETÎ' },
  config: {
    title: 'Veavakirina pêvajoyê', general: 'Giştî', params: 'Parametreyên', docs: 'Belgename',
    doc_title: 'Sernav', doc_desc: 'Danasîn', none: 'Tu veavakirin tune'
  },
  graph: {
    error_title: 'Grafîk', unavailable: 'Grafîk tune', aria_label: 'Grafîka Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'xeletiya render'
  },
  node_menu: {
    aria_actions: 'Kiryarên node', open_sg: 'Grafika binî veke', run_until: 'Heta bixebitîne',
    break_add: 'Xala rawestandinê lê zêde bike', break_remove: 'Xala rawestandinê jê bibe', inspect: 'Lêkolîn bike'
  },
  control_inputs: {
    debug_label: 'Debug:', node_id: 'ID node', when: 'Mercek', when_always: 'her gav',
    when_success: 'serkeftin', when_fail: 'têkçûn', when_retry: 'dîsa biceribîne',
    run_until: 'Heta bixebitîne', break_add: 'Rawestandin lê zêde bike', break_remove: 'Rawestandin jê bibe'
  },
  chat: {
    leader_panel_title: 'Serok — Sohbet', placeholder: 'Peyam...', tools_trace: 'Şopên amûrên bibîne',
    error_history: 'Dîrok nehat barkirin', empty_reply: '(bersiva vala)', global: 'Sohbeta cîhanî',
    error_history_global: 'Dîroka cîhanî nehat barkirin', you: 'Tu', assistant: 'LLM'
  },
  leader_global: {
    title: 'Serok — Sohbeta cîhanî', select_label: 'Serok:', select_aria: 'Serokek hilbijêre',
    display: 'Navê xuyang', role: 'Rol', persona: 'Persona', persona_ph: 'Orkestratora karkeran',
    none_detected: '(serok tune)'
  },
  leader_identity_panel: {
    no_leader: 'Tu serok nehatiye tayînkirin', error_read: 'Nasname nehat xwendin', refresh: 'Nûve bike',
    display: 'Navê xuyang', role: 'Rol', persona: 'Persona', persona_ph: 'Orkestratora karkeran',
    global_chat: 'Sohbeta cîhanî', leader_workers: 'Karkerên serokê', loading: 'Tê barkirin…',
    none_attached: 'Tu karker pêve nehatî', error_load: 'Xeletiya barkirinê'
  },
  list: { title: 'Karker', view: 'Bibîne' },
  config_editor: {
    tabs_simple: 'Hêsan', tabs_json: 'JSON', beautify: 'Zelal bike', minify: 'Biçûk bike',
    validate: 'Rastandin bike', json_valid: 'JSON rast', json_invalid: 'JSON nerast',
    complex_only_json: 'Hin zeviyên tevlihev tenê di JSON de têne guhertin'
  },
  leader_section: { edit_identity_hint: 'Nasname biguherîne (bitikîne)' },
  replay: {
    title: 'Dîsa lêxe (makîneya demê)', load_run: 'Xebitandinê bar bike', play: 'Lêxe', stop: 'Bisekinîne',
    error_runs: 'Xebitandin nehat barkirin', error_steps: 'Gav nehat barkirin',
    view_node: 'Vê node bibîne', live_announce_step: 'Gav {idx}/{total} tê lêxistin: {nodeId}'
  }
};
