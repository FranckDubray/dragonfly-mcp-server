export const __meta = { standalone: true, code: 'sv', flag: '🇸🇪', native: 'Svenska' };
export default {
  lang: { sv: 'Svenska' },
  common: {
    process: 'Process', details: 'Detaljer', tools_mcp: 'MCP-verktyg:', last_step: 'Sista steget',
    edit_identity: 'Visa/redigera identitet', close: 'Stäng', start_debug: 'Starta (felsök)', start_observe: 'Starta (observera)',
    step: 'Steg', continue: 'Fortsätt', stop: 'Stoppa', copy_in: 'Kopiera IN', copy_out: 'Kopiera OUT', copy_err: 'Kopiera fel',
    error_network: 'Nätverksfel', error_action: 'Åtgärd misslyckades', ok: 'OK', current_sg: 'Aktuellt delgraf',
    chat: 'Chatt', worker_status: 'Worker-status', save: 'Spara', send: 'Skicka'
  },
  header: { title: 'Arbetare och ledare', add_leader: '+ Lägg till ledare', add_worker: '+ Lägg till arbetare', leader: 'Ledare:' },
  kpis: { workers: 'ARBETARE', actifs: 'AKTIVA', steps24h: 'STEG (24H)', tokens24h: 'TOKEN (24H)', qualite7j: 'KVALITET (7D)' },
  toolbar: {
    process: 'Process', current: 'Aktuellt delgraf', overview: 'Översikt', hide_start: 'dölj START', hide_end: 'dölj END',
    labels: 'etiketter', follow_sg: 'följ SG', mode_observe: 'Observera', mode_debug: 'Felsökningsström',
    current_sg_btn: 'Aktuellt SG', display: 'Visning:', mode: 'Läge:'
  },
  modal: { process_title: 'Process —' },
  status: {
    panel_title: 'Status och mått', running: 'Kör', starting: 'Startar', failed: 'Misslyckades',
    completed: 'Slutförd', canceled: 'Avbruten', idle: 'Inaktiv', unknown: 'Okänd'
  },
  io: { title: 'Nod in-/utdata', in: 'IN', out: 'OUT', error: 'FEL' },
  config: {
    title: 'Processkonfiguration', general: 'Allmänt', params: 'Parametrar', docs: 'Dokumentation',
    doc_title: 'Titel', doc_desc: 'Beskrivning', none: 'Ingen konfiguration tillgänglig'
  },
  graph: {
    error_title: 'Graf', unavailable: 'Graf otillgänglig', aria_label: 'Mermaid-graf',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'renderingsfel'
  },
  node_menu: {
    aria_actions: 'Nodåtgärder', open_sg: 'Öppna delgraf', run_until: 'Kör tills',
    break_add: 'Lägg till brytpunkt', break_remove: 'Ta bort brytpunkt', inspect: 'Inspektera'
  },
  control_inputs: {
    debug_label: 'Felsök:', node_id: 'Nod-ID', when: 'Villkor', when_always: 'alltid',
    when_success: 'framgång', when_fail: 'misslyckande', when_retry: 'återförsök',
    run_until: 'Kör tills', break_add: 'Lägg till brytpunkt', break_remove: 'Ta bort brytpunkt'
  },
  chat: {
    leader_panel_title: 'Ledare — Chatt', placeholder: 'Meddelande...', tools_trace: 'Visa verktygsspår',
    error_history: 'Kunde inte ladda historik', empty_reply: '(tomt svar)', global: 'Global chatt',
    error_history_global: 'Kunde inte ladda global historik', you: 'Du', assistant: 'LLM'
  },
  leader_global: {
    title: 'Ledare — Global chatt', select_label: 'Ledare:', select_aria: 'Välj en ledare',
    display: 'Visningsnamn', role: 'Roll', persona: 'Persona', persona_ph: 'Worker-orkestrator',
    none_detected: '(ingen ledare)'
  },
  leader_identity_panel: {
    no_leader: 'Ingen ledare tilldelad', error_read: 'Kunde inte läsa identitet', refresh: 'Uppdatera',
    display: 'Visningsnamn', role: 'Roll', persona: 'Persona', persona_ph: 'Worker-orkestrator',
    global_chat: 'Global chatt', leader_workers: 'Ledar-workers', loading: 'Laddar…',
    none_attached: 'Ingen kopplad worker', error_load: 'Laddningsfel'
  },
  list: { title: 'Arbetare', view: 'Visa' },
  config_editor: {
    tabs_simple: 'Enkel', tabs_json: 'JSON', beautify: 'Försköna', minify: 'Minimera',
    validate: 'Validera', json_valid: 'Giltig JSON', json_invalid: 'Ogiltig JSON',
    complex_only_json: 'Vissa komplexa fält kan bara redigeras i JSON'
  },
  leader_section: { edit_identity_hint: 'Redigera identitet (klicka)' },
  replay: {
    title: 'Uppspelning (tidsmaskin)', load_run: 'Ladda körning', play: 'Spela', stop: 'Stoppa',
    error_runs: 'Kunde inte ladda körningar', error_steps: 'Kunde inte ladda steg',
    view_node: 'Visa denna nod', live_announce_step: 'Spelar steg {idx}/{total}: {nodeId}'
  }
};
