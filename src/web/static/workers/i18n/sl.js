export const __meta = { standalone: true, code: 'sl', flag: '🇸🇮', native: 'Slovenščina' };
export default {
  lang: { sl: 'Slovenščina' },
  common: {
    process: 'Postopek', details: 'Podrobnosti', tools_mcp: 'MCP orodja:', last_step: 'Zadnji korak',
    edit_identity: 'Prikaži/uredi identiteto', close: 'Zapri', start_debug: 'Začni (razhroščevanje)', start_observe: 'Začni (opazuj)',
    step: 'Korak', continue: 'Nadaljuj', stop: 'Ustavi', copy_in: 'Kopiraj IN', copy_out: 'Kopiraj OUT', copy_err: 'Kopiraj napako',
    error_network: 'Omrežna napaka', error_action: 'Dejanje ni uspelo', ok: 'V redu', current_sg: 'Trenutni podgraf',
    chat: 'Klepet', worker_status: 'Status delavca', save: 'Shrani', send: 'Pošlji'
  },
  header: { title: 'Delavci in vodje', add_leader: '+ Dodaj vodjo', add_worker: '+ Dodaj delavca', leader: 'Vodja:' },
  kpis: { workers: 'DELAVCI', actifs: 'AKTIVNI', steps24h: 'KORAKI (24U)', tokens24h: 'ŽETONI (24U)', qualite7j: 'KAKOVOST (7D)' },
  toolbar: {
    process: 'Postopek', current: 'Trenutni podgraf', overview: 'Pregled', hide_start: 'skrij START', hide_end: 'skrij END',
    labels: 'oznake', follow_sg: 'sledi SG', mode_observe: 'Opazovanje', mode_debug: 'Razhroščevalni tok',
    current_sg_btn: 'Trenutni SG', display: 'Prikaz:', mode: 'Način:'
  },
  modal: { process_title: 'Postopek —' },
  status: {
    panel_title: 'Stanje in metrike', running: 'Teče', starting: 'Se zaganja', failed: 'Neuspešno',
    completed: 'Zaključeno', canceled: 'Preklicano', idle: 'Nedejavno', unknown: 'Neznano'
  },
  io: { title: 'Vhodi/izhodi vozlišča', in: 'IN', out: 'OUT', error: 'NAPAKA' },
  config: {
    title: 'Konfiguracija postopka', general: 'Splošno', params: 'Parametri', docs: 'Dokumentacija',
    doc_title: 'Naslov', doc_desc: 'Opis', none: 'Ni na voljo nobene konfiguracije'
  },
  graph: {
    error_title: 'Graf', unavailable: 'Graf ni na voljo', aria_label: 'Mermaid graf',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'napaka pri upodabljanju'
  },
  node_menu: {
    aria_actions: 'Dejanja vozlišča', open_sg: 'Odpri podgraf', run_until: 'Zaženi do',
    break_add: 'Dodaj prekinitveno točko', break_remove: 'Odstrani prekinitveno točko', inspect: 'Preveri'
  },
  control_inputs: {
    debug_label: 'Razhroščevanje:', node_id: 'ID vozlišča', when: 'Pogoj', when_always: 'vedno',
    when_success: 'uspeh', when_fail: 'neuspeh', when_retry: 'ponovni poskus',
    run_until: 'Zaženi do', break_add: 'Dodaj prekinitev', break_remove: 'Odstrani prekinitev'
  },
  chat: {
    leader_panel_title: 'Vodja — Klepet', placeholder: 'Sporočilo...', tools_trace: 'Prikaži sledi orodij',
    error_history: 'Ni bilo mogoče naložiti zgodovine', empty_reply: '(prazen odgovor)', global: 'Globalni klepet',
    error_history_global: 'Ni bilo mogoče naložiti globalne zgodovine', you: 'Vi', assistant: 'LLM'
  },
  leader_global: {
    title: 'Vodja — Globalni klepet', select_label: 'Vodja:', select_aria: 'Izberite vodjo',
    display: 'Prikazno ime', role: 'Vloga', persona: 'Persona', persona_ph: 'Orkestrator delavcev',
    none_detected: '(ni vodje)'
  },
  leader_identity_panel: {
    no_leader: 'Ni dodeljen noben vodja', error_read: 'Branje identitete ni uspelo', refresh: 'Osveži',
    display: 'Prikazno ime', role: 'Vloga', persona: 'Persona', persona_ph: 'Orkestrator delavcev',
    global_chat: 'Globalni klepet', leader_workers: 'Vodjevi delavci', loading: 'Nalaganje…',
    none_attached: 'Noben pripet delavec', error_load: 'Napaka pri nalaganju'
  },
  list: { title: 'Delavci', view: 'Prikaži' },
  config_editor: {
    tabs_simple: 'Preprosto', tabs_json: 'JSON', beautify: 'Polepšaj', minify: 'Minimiziraj',
    validate: 'Preveri', json_valid: 'Veljaven JSON', json_invalid: 'Neveljaven JSON',
    complex_only_json: 'Nekatera kompleksna polja je mogoče urejati samo v JSON'
  },
  leader_section: { edit_identity_hint: 'Uredi identiteto (klikni)' },
  replay: {
    title: 'Predvajanje (časovni stroj)', load_run: 'Naloži izvedbo', play: 'Predvajaj', stop: 'Ustavi',
    error_runs: 'Ni bilo mogoče naložiti izvedb', error_steps: 'Ni bilo mogoče naložiti korakov',
    view_node: 'Prikaži to vozlišče', live_announce_step: 'Predvajanje koraka {idx}/{total}: {nodeId}'
  }
};
