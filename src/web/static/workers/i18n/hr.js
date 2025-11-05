export const __meta = { standalone: true, code: 'hr', flag: '🇭🇷', native: 'Hrvatski' };
export default {
  lang: { hr: 'Hrvatski' },
  common: {
    process: 'Proces', details: 'Detalji', tools_mcp: 'MCP alati:', last_step: 'Posljednji korak',
    edit_identity: 'Prikaži/uredi identitet', close: 'Zatvori', start_debug: 'Pokreni (otklanjanje pogrešaka)', start_observe: 'Pokreni (promatranje)',
    step: 'Korak', continue: 'Nastavi', stop: 'Zaustavi', copy_in: 'Kopiraj IN', copy_out: 'Kopiraj OUT', copy_err: 'Kopiraj pogrešku',
    error_network: 'Mrežna pogreška', error_action: 'Akcija nije uspjela', ok: 'U redu', current_sg: 'Trenutni podgraf',
    chat: 'Chat', worker_status: 'Status radnika', save: 'Spremi', send: 'Pošalji'
  },
  header: { title: 'Radnici i vođe', add_leader: '+ Dodaj vođu', add_worker: '+ Dodaj radnika', leader: 'Vođa:' },
  kpis: { workers: 'RADNICI', actifs: 'AKTIVNI', steps24h: 'KORACI (24H)', tokens24h: 'TOKENI (24H)', qualite7j: 'KVALITETA (7D)' },
  toolbar: {
    process: 'Proces', current: 'Trenutni podgraf', overview: 'Pregled', hide_start: 'sakrij START', hide_end: 'sakrij END',
    labels: 'oznake', follow_sg: 'prati SG', mode_observe: 'Promatranje', mode_debug: 'Debug stream',
    current_sg_btn: 'Trenutni SG', display: 'Prikaz:', mode: 'Način:'
  },
  modal: { process_title: 'Proces —' },
  status: {
    panel_title: 'Status i metrike', running: 'Radi', starting: 'Pokreće se', failed: 'Neuspješno',
    completed: 'Dovršeno', canceled: 'Otkazano', idle: 'Neaktivan', unknown: 'Nepoznato'
  },
  io: { title: 'Ulazi/izlazi čvora', in: 'IN', out: 'OUT', error: 'POGREŠKA' },
  config: {
    title: 'Konfiguracija procesa', general: 'Opće', params: 'Parametri', docs: 'Dokumentacija',
    doc_title: 'Naslov', doc_desc: 'Opis', none: 'Nema dostupne konfiguracije'
  },
  graph: {
    error_title: 'Graf', unavailable: 'Graf nije dostupan', aria_label: 'Mermaid graf',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'pogreška renderiranja'
  },
  node_menu: {
    aria_actions: 'Radnje čvora', open_sg: 'Otvori podgraf', run_until: 'Pokreni do',
    break_add: 'Dodaj točku prekida', break_remove: 'Ukloni točku prekida', inspect: 'Inspekcija'
  },
  control_inputs: {
    debug_label: 'Debug:', node_id: 'ID čvora', when: 'Uvjet', when_always: 'uvijek',
    when_success: 'uspjeh', when_fail: 'neuspjeh', when_retry: 'ponovni pokušaj',
    run_until: 'Pokreni do', break_add: 'Dodaj prekid', break_remove: 'Ukloni prekid'
  },
  chat: {
    leader_panel_title: 'Vođa — Chat', placeholder: 'Poruka...', tools_trace: 'Prikaži tragove alata',
    error_history: 'Nije moguće učitati povijest', empty_reply: '(prazan odgovor)', global: 'Globalni chat',
    error_history_global: 'Nije moguće učitati globalnu povijest', you: 'Vi', assistant: 'LLM'
  },
  leader_global: {
    title: 'Vođa — Globalni chat', select_label: 'Vođa:', select_aria: 'Odaberite vođu',
    display: 'Prikazano ime', role: 'Uloga', persona: 'Persona', persona_ph: 'Orkestratorradnika',
    none_detected: '(nema vođe)'
  },
  leader_identity_panel: {
    no_leader: 'Nije dodijeljena vođa', error_read: 'Nije moguće pročitati identitet', refresh: 'Osvježi',
    display: 'Prikazano ime', role: 'Uloga', persona: 'Persona', persona_ph: 'Orkestrator radnika',
    global_chat: 'Globalni chat', leader_workers: 'Radnici vođe', loading: 'Učitavanje…',
    none_attached: 'Nema priloženog radnika', error_load: 'Pogreška učitavanja'
  },
  list: { title: 'Radnici', view: 'Prikaži' },
  config_editor: {
    tabs_simple: 'Jednostavno', tabs_json: 'JSON', beautify: 'Uljepšaj', minify: 'Minimiziraj',
    validate: 'Validiraj', json_valid: 'Validan JSON', json_invalid: 'Nevalidan JSON',
    complex_only_json: 'Neka složena polja mogu se uređivati samo u JSON-u'
  },
  leader_section: { edit_identity_hint: 'Uredi identitet (klikni)' },
  replay: {
    title: 'Reprodukcija (vremeplov)', load_run: 'Učitaj izvršavanje', play: 'Reproduciraj', stop: 'Zaustavi',
    error_runs: 'Nije moguće učitati izvršavanja', error_steps: 'Nije moguće učitati korake',
    view_node: 'Prikaži ovaj čvor', live_announce_step: 'Reprodukcija koraka {idx}/{total}: {nodeId}'
  }
};
