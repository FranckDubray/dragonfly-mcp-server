export const __meta = { standalone: true, code: 'grc', flag: '🏛️', native: 'Ἑλληνική (ἀρχαία)' };
export default {
  lang: { grc: 'Ἑλληνική (ἀρχαία)' },
  header: { title: 'ἐργάται καὶ ἡγέται', add_leader: '+ πρόσθες ἡγεμόνα', add_worker: '+ πρόσθες ἐργάτην', leader: 'ἡγεμών:' },
  common: {
    process: 'διαδικασία', details: 'λεπτομέρειαι', tools_mcp: 'MCP ἐργαλεῖα:', last_step: 'τελευταῖον βῆμα',
    edit_identity: 'ἰδιότης διορθοῦν', close: 'κλεῖε', start_debug: 'ἀρχή (διόρθωσις)', start_observe: 'ἀρχή (παρατήρησις)',
    step: 'βῆμα', continue: 'συνέχισε', stop: 'παῦε', copy_in: 'ἀντίγραφε IN', copy_out: 'ἀντίγραφε OUT', copy_err: 'ἀντίγραφε σφάλμα',
    error_network: 'σφάλμα δικτύου', error_action: 'πρᾶξις ἁμαρτία', ok: 'εὖ', current_sg: 'νῦν ὑπογράφημα',
    chat: 'διάλογος', worker_status: 'κατάστασις', save: 'σῴζειν', send: 'πέμπειν'
  },
  kpis: { workers: 'ἐργάται', actifs: 'ἐνεργοί', steps24h: 'βήματα (24h)', tokens24h: 'σύμβολα (24h)', qualite7j: 'ποιότης (7d)' },
  toolbar: {
    process: 'διαδικασία', current: 'νῦν ὑπογράφημα', overview: 'ἐπισκόπησις', hide_start: 'κρύψον START', hide_end: 'κρύψον END',
    labels: 'ἐπιγραφαί', follow_sg: 'ἕπου SG', mode_observe: 'παρατήρησις', mode_debug: 'διόρθωσις',
    current_sg_btn: 'SG νῦν', display: 'θέα:', mode: 'τρόπος:'
  },
  modal: { process_title: 'διαδικασία —' },
  status: {
    panel_title: 'κατάστασις καὶ μέτρα', running: 'ἐργαζόμενον', starting: 'ἀρχόμενον', failed: 'ἡμαρτημένον',
    completed: 'τετελεσμένον', canceled: 'ἀκυρωθέν', idle: 'ἀργόν', unknown: 'ἄγνωστον'
  },
  io: { title: 'εἰσροαὶ καὶ ἐκροαὶ κόμβου', in: 'IN', out: 'OUT', error: 'σφάλμα' },
  config: {
    title: 'διαδικασία παραμετροποίησις', general: 'γενικός', params: 'παράμετροι', docs: 'ἔγγραφα',
    doc_title: 'τίτλος', doc_desc: 'περιγραφή', none: 'οὐδεμία παραμετροποίησις'
  },
  graph: {
    error_title: 'γραφεῖον', unavailable: 'γραφεῖον οὐ διαθέσιμον', aria_label: 'Mermaid γραφεῖον',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'σφάλμα ἀποδόσεως'
  },
  node_menu: {
    aria_actions: 'πράξεις κόμβου', open_sg: 'ἄνοιξον ὑπογράφημα', run_until: 'τρέχε μέχρι',
    break_add: 'πρόσθες σημεῖον παύσεως', break_remove: 'ἀφαίρει σημεῖον παύσεως', inspect: 'ἐπισκέπτου'
  },
  control_inputs: {
    debug_label: 'διόρθωσις:', node_id: 'κόμβος ID', when: 'ὅταν', when_always: 'ἀεί',
    when_success: 'ἐπιτυχία', when_fail: 'ἀποτυχία', when_retry: 'ἐπανάληψις',
    run_until: 'τρέχε μέχρι', break_add: 'πρόσθες παῦσιν', break_remove: 'ἀφαίρει παῦσιν'
  },
  chat: {
    leader_panel_title: 'ἡγεμών — διάλογος', placeholder: 'μήνυμα...', tools_trace: 'θεώρησον ἴχνη ἐργαλείων',
    error_history: 'ἱστορία φόρτωσις ἀποτυχία', empty_reply: '(κενὴ ἀπάντησις)', global: 'παγκόσμιος διάλογος',
    error_history_global: 'παγκόσμια ἱστορία φόρτωσις ἀποτυχία', you: 'σύ', assistant: 'LLM'
  },
  leader_global: {
    title: 'ἡγεμών — παγκόσμιος διάλογος', select_label: 'ἡγεμών:', select_aria: 'ἐκλέξαι ἡγεμόνα',
    display: 'ὄνομα θέας', role: 'ρόλος', persona: 'πρόσωπον', persona_ph: 'ὀρχηστρωτὴς ἐργατῶν',
    none_detected: '(οὐδεὶς ἡγεμών)'
  },
  leader_identity_panel: {
    no_leader: 'οὐδεὶς ἡγεμὼν διορισμένος', error_read: 'ἰδιότης ἀνάγνωσις ἀποτυχία', refresh: 'ἀνανέωσον',
    display: 'ὄνομα θέας', role: 'ρόλος', persona: 'πρόσωπον', persona_ph: 'ὀρχηστρωτὴς ἐργατῶν',
    global_chat: 'παγκόσμιος διάλογος', leader_workers: 'ἐργάται ἡγεμόνος', loading: 'φορτοῦται…',
    none_attached: 'οὐδεὶς συνημμένος ἐργάτης', error_load: 'σφάλμα φορτώσεως'
  },
  list: { title: 'ἐργάται', view: 'θεώρησον' },
  config_editor: {
    tabs_simple: 'ἁπλοῦς', tabs_json: 'JSON', beautify: 'καλλωπισμός', minify: 'σμίκρυνσις',
    validate: 'ἐπικυρῶσαι', json_valid: 'ἔγκυρον JSON', json_invalid: 'ἄκυρον JSON',
    complex_only_json: 'πολύπλοκα πεδία ἐν JSON μόνον ἐπεξεργάζονται'
  },
  leader_section: { edit_identity_hint: 'ἰδιότης διόρθωσον (κλίκ)' },
  replay: {
    title: 'ἐπαναληψις (μηχανὴ χρόνου)', load_run: 'φόρτωσον δρόμον', play: 'παίζειν', stop: 'παῦε',
    error_runs: 'δρόμοι φόρτωσις ἀποτυχία', error_steps: 'βήματα φόρτωσις ἀποτυχία',
    view_node: 'θεώρησον τοῦτον κόμβον', live_announce_step: 'παίζων βῆμα {idx}/{total}: {nodeId}'
  }
};
