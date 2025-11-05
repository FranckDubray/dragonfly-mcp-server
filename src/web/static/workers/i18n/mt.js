export const __meta = { standalone: true, code: 'mt', flag: '🇲🇹', native: 'Malti' };
export default {
  lang: { mt: 'Malti' },
  common: {
    process: 'Proċess', details: 'Dettalji', tools_mcp: 'Għodod MCP:', last_step: 'L-aħħar pass',
    edit_identity: 'Ara/editja identità', close: 'Agħlaq', start_debug: 'Ibda (debug)', start_observe: 'Ibda (osserva)',
    step: 'Pass', continue: 'Kompli', stop: 'Waqqa', copy_in: 'Ikkopja IN', copy_out: 'Ikkopja OUT', copy_err: 'Ikkopja żball',
    error_network: 'Żball tan-network', error_action: 'L-azzjoni falliet', ok: 'Okay', current_sg: 'Sottograf attwali',
    chat: 'Chat', worker_status: 'Status tal-ħaddiem', save: 'Issejvja', send: 'Ibgħat'
  },
  header: { title: 'Ħaddiema u Mexxejja', add_leader: '+ Żid mexxej', add_worker: '+ Żid ħaddiem', leader: 'Mexxej:' },
  kpis: { workers: 'ĦADDIEMA', actifs: 'ATTIVI', steps24h: 'PASSI (24S)', tokens24h: 'TOKENS (24S)', qualite7j: 'KWALITÀ (7J)' },
  toolbar: {
    process: 'Proċess', current: 'Sottograf attwali', overview: 'Ħarsa ġenerali', hide_start: 'aħbi START', hide_end: 'aħbi END',
    labels: 'tikketti', follow_sg: 'segwi SG', mode_observe: 'Osserva', mode_debug: 'Stream debug',
    current_sg_btn: 'SG attwali', display: 'Uri:', mode: 'Modalità:'
  },
  modal: { process_title: 'Proċess —' },
  status: {
    panel_title: 'Status u metriċi', running: 'Qed jaħdem', starting: 'Qed jibda', failed: 'Falliet',
    completed: 'Komplet', canceled: 'Ikkanċellat', idle: 'Wieqaf', unknown: 'Mhux magħruf'
  },
  io: { title: 'Inputs/outputs tan-nodu', in: 'IN', out: 'OUT', error: 'ŻBALL' },
  config: {
    title: 'Konfigurazzjoni tal-proċess', general: 'Ġenerali', params: 'Parametri', docs: 'Dokumentazzjoni',
    doc_title: 'Titolu', doc_desc: 'Deskrizzjoni', none: 'Ebda konfigurazzjoni disponibbli'
  },
  graph: {
    error_title: 'Graff', unavailable: 'Graff mhux disponibbli', aria_label: 'Graff Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'żball fir-rendering'
  },
  node_menu: {
    aria_actions: 'Azzjonijiet tan-nodu', open_sg: 'Iftaħ sottograf', run_until: 'Mexxi sa',
    break_add: 'Żid breakpoint', break_remove: 'Neħħi breakpoint', inspect: 'Ispezzjona'
  },
  control_inputs: {
    debug_label: 'Debug:', node_id: 'ID tan-nodu', when: 'Meta', when_always: 'dejjem',
    when_success: 'suċċess', when_fail: 'falliment', when_retry: 'erġa pprova',
    run_until: 'Mexxi sa', break_add: 'Żid breakpoint', break_remove: 'Neħħi breakpoint'
  },
  chat: {
    leader_panel_title: 'Mexxej — Chat', placeholder: 'Messaġġ...', tools_trace: 'Ara traċċi tal-għodod',
    error_history: 'Ma setax jitgħabba l-istorja', empty_reply: '(tweġiba vojta)', global: 'Chat globali',
    error_history_global: 'Ma setax jitgħabba l-istorja globali', you: 'Inti', assistant: 'LLM'
  },
  leader_global: {
    title: 'Mexxej — Chat globali', select_label: 'Mexxej:', select_aria: 'Agħżel mexxej',
    display: 'Isem tal-uri', role: 'Rwol', persona: 'Persona', persona_ph: 'Orkestrator tal-ħaddiema',
    none_detected: '(ebda mexxej)'
  },
  leader_identity_panel: {
    no_leader: 'Ebda mexxej assenjat', error_read: 'Ma setax jinqara l-identità', refresh: 'Aġġorna',
    display: 'Isem tal-uri', role: 'Rwol', persona: 'Persona', persona_ph: 'Orkestrator tal-ħaddiema',
    global_chat: 'Chat globali', leader_workers: 'Ħaddiema tal-mexxej', loading: 'Qed jitgħabba…',
    none_attached: 'Ebda ħaddiem mehmuż', error_load: 'Żball fit-tagħbija'
  },
  list: { title: 'Ħaddiema', view: 'Ara' },
  config_editor: {
    tabs_simple: 'Sempliċi', tabs_json: 'JSON', beautify: 'Issiġilla', minify: 'Iċċekken',
    validate: 'Valida', json_valid: 'JSON validu', json_invalid: 'JSON invalidu',
    complex_only_json: 'Xi oqsma kumplessi jistgħu jiġu editjati biss f'JSON'
  },
  leader_section: { edit_identity_hint: 'Editja l-identità (ikklikkja)' },
  replay: {
    title: 'Replay (magni taż-żmien)', load_run: 'Agħbbi run', play: 'Ipplejja', stop: 'Waqqa',
    error_runs: 'Ma setgħux jitgħabbew runs', error_steps: 'Ma setgħux jitgħabbew passi',
    view_node: 'Ara dan in-nodu', live_announce_step: 'Qed jipplejja l-pass {idx}/{total}: {nodeId}'
  }
};
