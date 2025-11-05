export const __meta = { standalone: true, code: 'nl', flag: '🇳🇱', native: 'Nederlands' };
export default {
  lang: { nl: 'Nederlands' },
  common: {
    process: 'Proces', details: 'Details', tools_mcp: 'MCP-tools:', last_step: 'Laatste stap',
    edit_identity: 'Identiteit bekijken/bewerken', close: 'Sluiten', start_debug: 'Start (debuggen)', start_observe: 'Start (observeren)',
    step: 'Stap', continue: 'Doorgaan', stop: 'Stoppen', copy_in: 'IN kopiëren', copy_out: 'OUT kopiëren', copy_err: 'Fout kopiëren',
    error_network: 'Netwerkfout', error_action: 'Actie mislukt', ok: 'OK', current_sg: 'Huidige subgrafiek',
    chat: 'Chat', worker_status: 'Worker-status', save: 'Opslaan', send: 'Verzenden'
  },
  header: { title: 'Werknemers en leiders', add_leader: '+ Leider toevoegen', add_worker: '+ Werknemer toevoegen', leader: 'Leider:' },
  kpis: { workers: 'WERKNEMERS', actifs: 'ACTIEF', steps24h: 'STAPPEN (24H)', tokens24h: 'TOKENS (24H)', qualite7j: 'KWALITEIT (7D)' },
  toolbar: {
    process: 'Proces', current: 'Huidige subgrafiek', overview: 'Overzicht', hide_start: 'START verbergen', hide_end: 'END verbergen',
    labels: 'labels', follow_sg: 'SG volgen', mode_observe: 'Observeren', mode_debug: 'Debug-stream',
    current_sg_btn: 'Huidige SG', display: 'Weergave:', mode: 'Modus:'
  },
  modal: { process_title: 'Proces —' },
  status: {
    panel_title: 'Status en statistieken', running: 'Actief', starting: 'Starten', failed: 'Mislukt',
    completed: 'Voltooid', canceled: 'Geannuleerd', idle: 'Inactief', unknown: 'Onbekend'
  },
  io: { title: 'Node in-/uitvoer', in: 'IN', out: 'OUT', error: 'FOUT' },
  config: {
    title: 'Procesconfiguratie', general: 'Algemeen', params: 'Parameters', docs: 'Documentatie',
    doc_title: 'Titel', doc_desc: 'Beschrijving', none: 'Geen configuratie beschikbaar'
  },
  graph: {
    error_title: 'Grafiek', unavailable: 'Grafiek niet beschikbaar', aria_label: 'Mermaid-grafiek',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'renderfout'
  },
  node_menu: {
    aria_actions: 'Node-acties', open_sg: 'Subgrafiek openen', run_until: 'Uitvoeren tot',
    break_add: 'Breekpunt toevoegen', break_remove: 'Breekpunt verwijderen', inspect: 'Inspecteren'
  },
  control_inputs: {
    debug_label: 'Debug:', node_id: 'Node-ID', when: 'Voorwaarde', when_always: 'altijd',
    when_success: 'succes', when_fail: 'fout', when_retry: 'opnieuw',
    run_until: 'Uitvoeren tot', break_add: 'Breekpunt toevoegen', break_remove: 'Breekpunt verwijderen'
  },
  chat: {
    leader_panel_title: 'Leider — Chat', placeholder: 'Bericht...', tools_trace: 'Tool-traces bekijken',
    error_history: 'Geschiedenis laden mislukt', empty_reply: '(leeg antwoord)', global: 'Globale chat',
    error_history_global: 'Globale geschiedenis laden mislukt', you: 'U', assistant: 'LLM'
  },
  leader_global: {
    title: 'Leider — Globale chat', select_label: 'Leider:', select_aria: 'Selecteer een leider',
    display: 'Weergavenaam', role: 'Rol', persona: 'Persona', persona_ph: 'Worker-orchestrator',
    none_detected: '(geen leider)'
  },
  leader_identity_panel: {
    no_leader: 'Geen leider toegewezen', error_read: 'Identiteit lezen mislukt', refresh: 'Vernieuwen',
    display: 'Weergavenaam', role: 'Rol', persona: 'Persona', persona_ph: 'Worker-orchestrator',
    global_chat: 'Globale chat', leader_workers: 'Leider workers', loading: 'Laden…',
    none_attached: 'Geen worker gekoppeld', error_load: 'Laadfout'
  },
  list: { title: 'Werknemers', view: 'Bekijken' },
  config_editor: {
    tabs_simple: 'Eenvoudig', tabs_json: 'JSON', beautify: 'Mooi opmaken', minify: 'Minimaliseren',
    validate: 'Valideren', json_valid: 'Geldige JSON', json_invalid: 'Ongeldige JSON',
    complex_only_json: 'Sommige complexe velden kunnen alleen in JSON bewerkt worden'
  },
  leader_section: { edit_identity_hint: 'Identiteit bewerken (klik)' },
  replay: {
    title: 'Herhaling (tijdmachine)', load_run: 'Run laden', play: 'Afspelen', stop: 'Stoppen',
    error_runs: 'Runs laden mislukt', error_steps: 'Stappen laden mislukt',
    view_node: 'Deze node bekijken', live_announce_step: 'Stap {idx}/{total} afspelen: {nodeId}'
  }
};
