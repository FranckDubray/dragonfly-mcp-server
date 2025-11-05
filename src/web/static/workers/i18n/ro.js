export const __meta = { standalone: true, code: 'ro', flag: '🇷🇴', native: 'Română' };
export default {
  lang: { ro: 'Română' },
  common: {
    process: 'Proces', details: 'Detalii', tools_mcp: 'Instrumente MCP:', last_step: 'Ultimul pas',
    edit_identity: 'Vizualizare/editare identitate', close: 'Închide', start_debug: 'Pornește (depanare)', start_observe: 'Pornește (observare)',
    step: 'Pas', continue: 'Continuă', stop: 'Oprește', copy_in: 'Copiază IN', copy_out: 'Copiază OUT', copy_err: 'Copiază eroare',
    error_network: 'Eroare de rețea', error_action: 'Acțiune eșuată', ok: 'OK', current_sg: 'Subgraf curent',
    chat: 'Chat', worker_status: 'Status worker', save: 'Salvează', send: 'Trimite'
  },
  header: { title: 'Lucrători și lideri', add_leader: '+ Adaugă lider', add_worker: '+ Adaugă lucrător', leader: 'Lider:' },
  kpis: { workers: 'LUCRĂTORI', actifs: 'ACTIVI', steps24h: 'PAȘI (24H)', tokens24h: 'TOKENI (24H)', qualite7j: 'CALITATE (7Z)' },
  toolbar: {
    process: 'Proces', current: 'Subgraf curent', overview: 'Prezentare', hide_start: 'ascunde START', hide_end: 'ascunde END',
    labels: 'etichete', follow_sg: 'urmărește SG', mode_observe: 'Observare', mode_debug: 'Flux depanare',
    current_sg_btn: 'SG curent', display: 'Afișare:', mode: 'Mod:'
  },
  modal: { process_title: 'Proces —' },
  status: {
    panel_title: 'Stare și metrici', running: 'Rulează', starting: 'Pornire', failed: 'Eșuat',
    completed: 'Finalizat', canceled: 'Anulat', idle: 'În repaus', unknown: 'Necunoscut'
  },
  io: { title: 'Intrări/ieșiri nod', in: 'IN', out: 'OUT', error: 'EROARE' },
  config: {
    title: 'Configurație proces', general: 'General', params: 'Parametri', docs: 'Documentație',
    doc_title: 'Titlu', doc_desc: 'Descriere', none: 'Nicio configurație disponibilă'
  },
  graph: {
    error_title: 'Graf', unavailable: 'Graf indisponibil', aria_label: 'Graf Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'eroare de randare'
  },
  node_menu: {
    aria_actions: 'Acțiuni nod', open_sg: 'Deschide subgraf', run_until: 'Rulează până la',
    break_add: 'Adaugă punct de întrerupere', break_remove: 'Elimină punct de întrerupere', inspect: 'Inspectează'
  },
  control_inputs: {
    debug_label: 'Depanare:', node_id: 'ID nod', when: 'Condiție', when_always: 'întotdeauna',
    when_success: 'succes', when_fail: 'eșec', when_retry: 'reîncercare',
    run_until: 'Rulează până la', break_add: 'Adaugă întrerupere', break_remove: 'Elimină întrerupere'
  },
  chat: {
    leader_panel_title: 'Lider — Chat', placeholder: 'Mesaj...', tools_trace: 'Vezi urmele instrumentelor',
    error_history: 'Eșec la încărcarea istoricului', empty_reply: '(răspuns gol)', global: 'Chat global',
    error_history_global: 'Eșec la încărcarea istoricului global', you: 'Tu', assistant: 'LLM'
  },
  leader_global: {
    title: 'Lider — Chat global', select_label: 'Lider:', select_aria: 'Selectează un lider',
    display: 'Nume afișat', role: 'Rol', persona: 'Persona', persona_ph: 'Orchestrator de lucrători',
    none_detected: '(niciun lider)'
  },
  leader_identity_panel: {
    no_leader: 'Niciun lider atribuit', error_read: 'Eșec la citirea identității', refresh: 'Reîmprospătare',
    display: 'Nume afișat', role: 'Rol', persona: 'Persona', persona_ph: 'Orchestrator de lucrători',
    global_chat: 'Chat global', leader_workers: 'Lucrători lider', loading: 'Se încarcă…',
    none_attached: 'Niciun lucrător atașat', error_load: 'Eroare de încărcare'
  },
  list: { title: 'Lucrători', view: 'Vizualizare' },
  config_editor: {
    tabs_simple: 'Simplu', tabs_json: 'JSON', beautify: 'Formatare', minify: 'Minimizare',
    validate: 'Validare', json_valid: 'JSON valid', json_invalid: 'JSON invalid',
    complex_only_json: 'Unele câmpuri complexe pot fi editate doar în JSON'
  },
  leader_section: { edit_identity_hint: 'Editează identitatea (clic)' },
  replay: {
    title: 'Redare (mașina timpului)', load_run: 'Încarcă rulare', play: 'Redare', stop: 'Oprire',
    error_runs: 'Eșec la încărcarea rulărilor', error_steps: 'Eșec la încărcarea pașilor',
    view_node: 'Vezi acest nod', live_announce_step: 'Redare pas {idx}/{total}: {nodeId}'
  }
};
