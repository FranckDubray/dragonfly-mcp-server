export const __meta = { standalone: true, code: 'it', flag: '🇮🇹', native: 'Italiano' };
export default {
  lang: { it: 'Italiano' },
  header: { title: 'Lavoratori e leader', add_leader: '+ Aggiungi leader', add_worker: '+ Aggiungi lavoratore', leader: 'Leader:' },
  common: {
    process: 'Processo', details: 'Dettagli', tools_mcp: 'Strumenti MCP:', last_step: 'Ultimo passo',
    edit_identity: 'Visualizza/modifica identità', close: 'Chiudi', start_observe: 'Avvia (osserva)', start_debug: 'Avvia (debug)',
    step: 'Passo', continue: 'Continua', stop: 'Ferma', copy_in: 'Copia IN', copy_out: 'Copia OUT', copy_err: 'Copia errore',
    error_network: 'Errore di rete', error_action: 'Azione non riuscita', ok: 'OK', current_sg: 'Sottografo corrente',
    chat: 'Chat', worker_status: 'Stato', save: 'Salva', send: 'Invia',
    status_metrics: 'Stato e metriche', running: 'In esecuzione', starting: 'Avvio', failed: 'Fallito', completed: 'Completato', canceled: 'Annullato', idle: 'Inattivo', unknown: 'Sconosciuto'
  },
  kpis: { workers: 'LAVORATORI', actifs: 'ATTIVI', steps24h: 'PASSI (24H)', tokens24h: 'TOKEN (24H)', qualite7j: 'QUALITÀ (7G)' },
  toolbar: {
    process: 'Processo', current: 'Sottografo corrente', overview: 'Panoramica', hide_start: 'nascondi START', hide_end: 'nascondi END',
    labels: 'etichette', follow_sg: 'segui SG', mode_observe: 'Osserva', mode_debug: 'Flusso di debug', current_sg_btn: 'SG corrente',
    display: 'Visualizza:', mode: 'Modalità:'
  },
  modal: { process_title: 'Processo —' },
  status: { panel_title: 'Stato e metriche', running: 'In esecuzione', starting: 'Avvio', failed: 'Fallito', completed: 'Completato', canceled: 'Annullato', idle: 'Inattivo', unknown: 'Sconosciuto' },
  io: { title: 'Ingressi/Uscite del nodo', in: 'IN', out: 'OUT', error: 'ERRORE' },
  config: { title: 'Configurazione del processo', general: 'Generale', params: 'Parametri', docs: 'Documentazione', doc_title: 'Titolo', doc_desc: 'Descrizione', none: 'Nessuna configurazione disponibile' },
  graph: { error_title: 'Grafo', unavailable: 'Grafo non disponibile', aria_label: 'Grafo Mermaid', mermaid_error_prefix: 'Mermaid — ', render_error: 'errore di rendering' },
  node_menu: { aria_actions: 'Azioni del nodo', open_sg: 'Apri sottografo', run_until: 'Esegui fino a', break_add: 'Aggiungi breakpoint', break_remove: 'Rimuovi breakpoint', inspect: 'Ispeziona' },
  control_inputs: { debug_label: 'Debug:', node_id: 'ID nodo', when: 'Condizione', when_always: 'sempre', when_success: 'successo', when_fail: 'errore', when_retry: 'riprova', run_until: 'Esegui fino a', break_add: 'Aggiungi breakpoint', break_remove: 'Rimuovi breakpoint' },
  chat: { leader_panel_title: 'Leader — Chat', placeholder: 'Messaggio...', tools_trace: 'Vedi tracce degli strumenti', error_history: 'Impossibile caricare la cronologia', empty_reply: '(risposta vuota)', global: 'Chat globale', error_history_global: 'Impossibile caricare la cronologia globale', you: 'Tu', assistant: 'LLM' },
  leader_global: { title: 'Leader — Chat globale', select_label: 'Leader:', select_aria: 'Seleziona un leader', display: 'Nome visualizzato', role: 'Ruolo', persona: 'Persona', persona_ph: 'Orchestratore dei workers', none_detected: '(nessun leader)' },
  leader_identity_panel: { no_leader: 'Nessun leader assegnato', error_read: 'Impossibile leggere l’identità', refresh: 'Aggiorna', display: 'Nome visualizzato', role: 'Ruolo', persona: 'Persona', persona_ph: 'Orchestratore dei workers', global_chat: 'Chat globale', leader_workers: 'Workers del leader', loading: 'Caricamento…', none_attached: 'Nessun worker collegato', error_load: 'Errore di caricamento' },
  list: { title: 'Lavoratori', view: 'Vedi' },
  config_editor: { tabs_simple: 'Semplice', tabs_json: 'JSON', beautify: 'Formatta', minify: 'Minimizza', validate: 'Valida', json_valid: 'JSON valido', json_invalid: 'JSON non valido', complex_only_json: 'Alcuni campi complessi sono modificabili solo in JSON' },
  leader_section: { edit_identity_hint: 'Modifica identità (clic)' },
  replay: { title: 'Riproduzione (macchina del tempo)', load_run: 'Carica run', play: 'Riproduci', stop: 'Ferma', error_runs: 'Impossibile caricare i run', error_steps: 'Impossibile caricare i passi', view_node: 'Vedi questo nodo', live_announce_step: 'Riproduzione passo {idx}/{total}: {nodeId}' }
};
