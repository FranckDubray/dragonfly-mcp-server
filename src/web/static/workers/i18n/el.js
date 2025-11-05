export const __meta = { standalone: true, code: 'el', flag: '🇬🇷', native: 'Ελληνικά' };
export default {
  lang: { el: 'Ελληνικά' },
  common: {
    process: 'Διαδικασία', details: 'Λεπτομέρειες', tools_mcp: 'Εργαλεία MCP:', last_step: 'Τελευταίο βήμα',
    edit_identity: 'Προβολή/επεξεργασία ταυτότητας', close: 'Κλείσιμο', start_debug: 'Έναρξη (αποσφαλμάτωση)', start_observe: 'Έναρξη (παρατήρηση)',
    step: 'Βήμα', continue: 'Συνέχεια', stop: 'Διακοπή', copy_in: 'Αντιγραφή IN', copy_out: 'Αντιγραφή OUT', copy_err: 'Αντιγραφή σφάλματος',
    error_network: 'Σφάλμα δικτύου', error_action: 'Η ενέργεια απέτυχε', ok: 'Εντάξει', current_sg: 'Τρέχον υπογράφημα',
    chat: 'Συνομιλία', worker_status: 'Κατάσταση εργαζομένου', save: 'Αποθήκευση', send: 'Αποστολή'
  },
  header: { title: 'Εργαζόμενοι & Ηγέτες', add_leader: '+ Προσθήκη ηγέτη', add_worker: '+ Προσθήκη εργαζόμενου', leader: 'Ηγέτης:' },
  kpis: { workers: 'ΕΡΓΑΖΟΜΕΝΟΙ', actifs: 'ΕΝΕΡΓΟΙ', steps24h: 'ΒΗΜΑΤΑ (24Ω)', tokens24h: 'ΔΙΑΚΡΙΤΙΚΑ (24Ω)', qualite7j: 'ΠΟΙΟΤΗΤΑ (7Η)' },
  toolbar: {
    process: 'Διαδικασία', current: 'Τρέχον υπογράφημα', overview: 'Επισκόπηση', hide_start: 'απόκρυψη START', hide_end: 'απόκρυψη END',
    labels: 'ετικέτες', follow_sg: 'ακολουθήστε SG', mode_observe: 'Παρατήρηση', mode_debug: 'Ροή αποσφαλμάτωσης',
    current_sg_btn: 'Τρέχον SG', display: 'Εμφάνιση:', mode: 'Λειτουργία:'
  },
  modal: { process_title: 'Διαδικασία —' },
  status: {
    panel_title: 'Κατάσταση και μετρήσεις', running: 'Σε εξέλιξη', starting: 'Εκκίνηση', failed: 'Απέτυχε',
    completed: 'Ολοκληρώθηκε', canceled: 'Ακυρώθηκε', idle: 'Σε αναμονή', unknown: 'Άγνωστο'
  },
  io: { title: 'Είσοδοι/έξοδοι κόμβου', in: 'IN', out: 'OUT', error: 'ΣΦΑΛΜΑ' },
  config: {
    title: 'Διαμόρφωση διαδικασίας', general: 'Γενικά', params: 'Παράμετροι', docs: 'Τεκμηρίωση',
    doc_title: 'Τίτλος', doc_desc: 'Περιγραφή', none: 'Δεν υπάρχει διαθέσιμη διαμόρφωση'
  },
  graph: {
    error_title: 'Γράφημα', unavailable: 'Το γράφημα δεν είναι διαθέσιμο', aria_label: 'Γράφημα Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'σφάλμα απόδοσης'
  },
  node_menu: {
    aria_actions: 'Ενέργειες κόμβου', open_sg: 'Άνοιγμα υπογραφήματος', run_until: 'Εκτέλεση έως',
    break_add: 'Προσθήκη σημείου διακοπής', break_remove: 'Αφαίρεση σημείου διακοπής', inspect: 'Έλεγχος'
  },
  control_inputs: {
    debug_label: 'Αποσφαλμάτωση:', node_id: 'ID κόμβου', when: 'Συνθήκη', when_always: 'πάντα',
    when_success: 'επιτυχία', when_fail: 'αποτυχία', when_retry: 'επανάληψη',
    run_until: 'Εκτέλεση έως', break_add: 'Προσθήκη διακοπής', break_remove: 'Αφαίρεση διακοπής'
  },
  chat: {
    leader_panel_title: 'Ηγέτης — Συνομιλία', placeholder: 'Μήνυμα...', tools_trace: 'Προβολή ιχνών εργαλείων',
    error_history: 'Αποτυχία φόρτωσης ιστορικού', empty_reply: '(κενή απάντηση)', global: 'Καθολική συνομιλία',
    error_history_global: 'Αποτυχία φόρτωσης καθολικού ιστορικού', you: 'Εσείς', assistant: 'LLM'
  },
  leader_global: {
    title: 'Ηγέτης — Καθολική συνομιλία', select_label: 'Ηγέτης:', select_aria: 'Επιλέξτε ηγέτη',
    display: 'Εμφανιζόμενο όνομα', role: 'Ρόλος', persona: 'Προσωπικότητα', persona_ph: 'Ενορχηστρωτής εργαζομένων',
    none_detected: '(δεν υπάρχει ηγέτης)'
  },
  leader_identity_panel: {
    no_leader: 'Δεν έχει ανατεθεί ηγέτης', error_read: 'Αποτυχία ανάγνωσης ταυτότητας', refresh: 'Ανανέωση',
    display: 'Εμφανιζόμενο όνομα', role: 'Ρόλος', persona: 'Προσωπικότητα', persona_ph: 'Ενορχηστρωτής εργαζομένων',
    global_chat: 'Καθολική συνομιλία', leader_workers: 'Εργαζόμενοι ηγέτη', loading: 'Φόρτωση…',
    none_attached: 'Δεν υπάρχει συνδεδεμένος εργαζόμενος', error_load: 'Σφάλμα φόρτωσης'
  },
  list: { title: 'Εργαζόμενοι', view: 'Προβολή' },
  config_editor: {
    tabs_simple: 'Απλό', tabs_json: 'JSON', beautify: 'Ομορφοποίηση', minify: 'Ελαχιστοποίηση',
    validate: 'Επικύρωση', json_valid: 'Έγκυρο JSON', json_invalid: 'Μη έγκυρο JSON',
    complex_only_json: 'Ορισμένα σύνθετα πεδία μπορούν να επεξεργαστούν μόνο σε JSON'
  },
  leader_section: { edit_identity_hint: 'Επεξεργασία ταυτότητας (κλικ)' },
  replay: {
    title: 'Αναπαραγωγή (μηχανή του χρόνου)', load_run: 'Φόρτωση εκτέλεσης', play: 'Αναπαραγωγή', stop: 'Διακοπή',
    error_runs: 'Αποτυχία φόρτωσης εκτελέσεων', error_steps: 'Αποτυχία φόρτωσης βημάτων',
    view_node: 'Προβολή αυτού του κόμβου', live_announce_step: 'Αναπαραγωγή βήματος {idx}/{total}: {nodeId}'
  }
};
