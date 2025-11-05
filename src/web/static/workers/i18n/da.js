export const __meta = { standalone: true, code: 'da', flag: '🇩🇰', native: 'Dansk' };
export default {
  lang: { da: 'Dansk' },
  common: {
    process: 'Proces', details: 'Detaljer', tools_mcp: 'MCP-værktøjer:', last_step: 'Sidste trin',
    edit_identity: 'Vis/rediger identitet', close: 'Luk', start_debug: 'Start (fejlfinding)', start_observe: 'Start (observer)',
    step: 'Trin', continue: 'Fortsæt', stop: 'Stop', copy_in: 'Kopier IN', copy_out: 'Kopier OUT', copy_err: 'Kopier fejl',
    error_network: 'Netværksfejl', error_action: 'Handling mislykkedes', ok: 'OK', current_sg: 'Nuværende delgraf',
    chat: 'Chat', worker_status: 'Worker-status', save: 'Gem', send: 'Send'
  },
  header: { title: 'Arbejdere og ledere', add_leader: '+ Tilføj leder', add_worker: '+ Tilføj arbejder', leader: 'Leder:' },
  kpis: { workers: 'ARBEJDERE', actifs: 'AKTIVE', steps24h: 'TRIN (24T)', tokens24h: 'TOKENS (24T)', qualite7j: 'KVALITET (7D)' },
  toolbar: {
    process: 'Proces', current: 'Nuværende delgraf', overview: 'Oversigt', hide_start: 'skjul START', hide_end: 'skjul END',
    labels: 'etiketter', follow_sg: 'følg SG', mode_observe: 'Observer', mode_debug: 'Debug-stream',
    current_sg_btn: 'Nuværende SG', display: 'Visning:', mode: 'Tilstand:'
  },
  modal: { process_title: 'Proces —' },
  status: {
    panel_title: 'Status og metrikker', running: 'Kører', starting: 'Starter', failed: 'Fejlede',
    completed: 'Færdig', canceled: 'Annulleret', idle: 'Inaktiv', unknown: 'Ukendt'
  },
  io: { title: 'Node input/output', in: 'IN', out: 'OUT', error: 'FEJL' },
  config: {
    title: 'Proceskonfiguration', general: 'Generelt', params: 'Parametre', docs: 'Dokumentation',
    doc_title: 'Titel', doc_desc: 'Beskrivelse', none: 'Ingen konfiguration tilgængelig'
  },
  graph: {
    error_title: 'Graf', unavailable: 'Graf utilgængelig', aria_label: 'Mermaid-graf',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'renderingsfejl'
  },
  node_menu: {
    aria_actions: 'Node-handlinger', open_sg: 'Åbn delgraf', run_until: 'Kør indtil',
    break_add: 'Tilføj breakpoint', break_remove: 'Fjern breakpoint', inspect: 'Inspicer'
  },
  control_inputs: {
    debug_label: 'Debug:', node_id: 'Node-ID', when: 'Betingelse', when_always: 'altid',
    when_success: 'succes', when_fail: 'fejl', when_retry: 'genprøv',
    run_until: 'Kør indtil', break_add: 'Tilføj breakpoint', break_remove: 'Fjern breakpoint'
  },
  chat: {
    leader_panel_title: 'Leder — Chat', placeholder: 'Besked...', tools_trace: 'Vis værktøjsspor',
    error_history: 'Kunne ikke indlæse historik', empty_reply: '(tomt svar)', global: 'Global chat',
    error_history_global: 'Kunne ikke indlæse global historik', you: 'Dig', assistant: 'LLM'
  },
  leader_global: {
    title: 'Leder — Global chat', select_label: 'Leder:', select_aria: 'Vælg en leder',
    display: 'Visningsnavn', role: 'Rolle', persona: 'Persona', persona_ph: 'Worker-orkestrator',
    none_detected: '(ingen leder)'
  },
  leader_identity_panel: {
    no_leader: 'Ingen leder tildelt', error_read: 'Kunne ikke læse identitet', refresh: 'Opdater',
    display: 'Visningsnavn', role: 'Rolle', persona: 'Persona', persona_ph: 'Worker-orkestrator',
    global_chat: 'Global chat', leader_workers: 'Leder-workers', loading: 'Indlæser…',
    none_attached: 'Ingen tilknyttet worker', error_load: 'Indlæsningsfejl'
  },
  list: { title: 'Arbejdere', view: 'Vis' },
  config_editor: {
    tabs_simple: 'Simpel', tabs_json: 'JSON', beautify: 'Forskønne', minify: 'Minimer',
    validate: 'Valider', json_valid: 'Gyldig JSON', json_invalid: 'Ugyldig JSON',
    complex_only_json: 'Nogle komplekse felter kan kun redigeres i JSON'
  },
  leader_section: { edit_identity_hint: 'Rediger identitet (klik)' },
  replay: {
    title: 'Genafspilning (tidsmaskine)', load_run: 'Indlæs kørsel', play: 'Afspil', stop: 'Stop',
    error_runs: 'Kunne ikke indlæse kørsler', error_steps: 'Kunne ikke indlæse trin',
    view_node: 'Vis denne node', live_announce_step: 'Afspiller trin {idx}/{total}: {nodeId}'
  }
};
