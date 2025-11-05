export const __meta = { standalone: true, code: 'de', flag: '🇩🇪', native: 'Deutsch' };
export default {
  lang: { de: 'Deutsch' },
  common: {
    process: 'Prozess', details: 'Details', tools_mcp: 'MCP-Tools:', last_step: 'Letzter Schritt',
    edit_identity: 'Identität ansehen/bearbeiten', close: 'Schließen', start_debug: 'Start (Debug)', start_observe: 'Start (Beobachten)',
    step: 'Schritt', continue: 'Weiter', stop: 'Stopp', copy_in: 'IN kopieren', copy_out: 'OUT kopieren', copy_err: 'Fehler kopieren',
    error_network: 'Netzwerkfehler', error_action: 'Aktion fehlgeschlagen', ok: 'OK', current_sg: 'Aktueller Untergraph',
    chat: 'Chat', worker_status: 'Worker-Status', save: 'Speichern', send: 'Senden'
  },
  header: { title: 'Worker & Leiter', add_leader: '+ Leiter hinzufügen', add_worker: '+ Worker hinzufügen', leader: 'Leiter:' },
  kpis: { workers: 'WORKER', actifs: 'AKTIV', steps24h: 'SCHRITTE (24H)', tokens24h: 'TOKENS (24H)', qualite7j: 'QUALITÄT (7T)' },
  toolbar: {
    process: 'Prozess', current: 'Aktueller Untergraph', overview: 'Übersicht', hide_start: 'START ausblenden', hide_end: 'END ausblenden',
    labels: 'Labels', follow_sg: 'SG folgen', mode_observe: 'Beobachten', mode_debug: 'Debug-Stream',
    current_sg_btn: 'Aktueller SG', display: 'Anzeige:', mode: 'Modus:'
  },
  modal: { process_title: 'Prozess —' },
  status: {
    panel_title: 'Status & Metriken', running: 'Läuft', starting: 'Startet', failed: 'Fehlgeschlagen',
    completed: 'Abgeschlossen', canceled: 'Abgebrochen', idle: 'Inaktiv', unknown: 'Unbekannt'
  },
  io: { title: 'Knoten Ein-/Ausgaben', in: 'IN', out: 'OUT', error: 'FEHLER' },
  config: {
    title: 'Prozesskonfiguration', general: 'Allgemein', params: 'Parameter', docs: 'Dokumentation',
    doc_title: 'Titel', doc_desc: 'Beschreibung', none: 'Keine Konfiguration verfügbar'
  },
  graph: {
    error_title: 'Graph', unavailable: 'Graph nicht verfügbar', aria_label: 'Mermaid-Graph',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'Render-Fehler'
  },
  node_menu: {
    aria_actions: 'Knoten-Aktionen', open_sg: 'Untergraph öffnen', run_until: 'Ausführen bis',
    break_add: 'Haltepunkt hinzufügen', break_remove: 'Haltepunkt entfernen', inspect: 'Inspizieren'
  },
  control_inputs: {
    debug_label: 'Debug:', node_id: 'Knoten-ID', when: 'Bedingung', when_always: 'immer',
    when_success: 'Erfolg', when_fail: 'Fehler', when_retry: 'Wiederholung',
    run_until: 'Ausführen bis', break_add: 'Haltepunkt hinzufügen', break_remove: 'Haltepunkt entfernen'
  },
  chat: {
    leader_panel_title: 'Leiter — Chat', placeholder: 'Nachricht...', tools_trace: 'Tool-Traces ansehen',
    error_history: 'Verlauf konnte nicht geladen werden', empty_reply: '(leere Antwort)', global: 'Globaler Chat',
    error_history_global: 'Globaler Verlauf konnte nicht geladen werden', you: 'Sie', assistant: 'LLM'
  },
  leader_global: {
    title: 'Leiter — Globaler Chat', select_label: 'Leiter:', select_aria: 'Leiter auswählen',
    display: 'Anzeigename', role: 'Rolle', persona: 'Persona', persona_ph: 'Worker-Orchestrator',
    none_detected: '(kein Leiter)'
  },
  leader_identity_panel: {
    no_leader: 'Kein Leiter zugewiesen', error_read: 'Identität konnte nicht gelesen werden', refresh: 'Aktualisieren',
    display: 'Anzeigename', role: 'Rolle', persona: 'Persona', persona_ph: 'Worker-Orchestrator',
    global_chat: 'Globaler Chat', leader_workers: 'Leiter-Worker', loading: 'Laden…',
    none_attached: 'Kein Worker zugeordnet', error_load: 'Ladefehler'
  },
  list: { title: 'Worker', view: 'Ansehen' },
  config_editor: {
    tabs_simple: 'Einfach', tabs_json: 'JSON', beautify: 'Verschönern', minify: 'Minimieren',
    validate: 'Validieren', json_valid: 'Gültiges JSON', json_invalid: 'Ungültiges JSON',
    complex_only_json: 'Einige komplexe Felder sind nur in JSON editierbar'
  },
  leader_section: { edit_identity_hint: 'Identität bearbeiten (klicken)' },
  replay: {
    title: 'Wiedergabe (Zeitmaschine)', load_run: 'Run laden', play: 'Abspielen', stop: 'Stoppen',
    error_runs: 'Runs konnten nicht geladen werden', error_steps: 'Schritte konnten nicht geladen werden',
    view_node: 'Diesen Knoten ansehen', live_announce_step: 'Schritt {idx}/{total} wird abgespielt: {nodeId}'
  }
};
