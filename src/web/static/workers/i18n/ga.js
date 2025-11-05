export const __meta = { standalone: true, code: 'ga', flag: '🇮🇪', native: 'Gaeilge' };
export default {
  lang: { ga: 'Gaeilge' },
  common: {
    process: 'Próiseas', details: 'Sonraí', tools_mcp: 'Uirlisí MCP:', last_step: 'Céim dheiridh',
    edit_identity: 'Amharc/cuir in eagar céannacht', close: 'Dún', start_debug: 'Tosaigh (dífhabhtú)', start_observe: 'Tosaigh (faireachán)',
    step: 'Céim', continue: 'Lean ar aghaidh', stop: 'Stop', copy_in: 'Cóipeáil IN', copy_out: 'Cóipeáil OUT', copy_err: 'Cóipeáil earráid',
    error_network: 'Earráid líonra', error_action: 'Theip ar an ngníomh', ok: 'Ceart go leor', current_sg: 'Fo-ghraf reatha',
    chat: 'Comhrá', worker_status: 'Stádas oibrí', save: 'Sábháil', send: 'Seol'
  },
  header: { title: 'Oibrithe & Ceannairí', add_leader: '+ Cuir ceannaire leis', add_worker: '+ Cuir oibrí leis', leader: 'Ceannaire:' },
  kpis: { workers: 'OIBRITHE', actifs: 'GNÍOMHACHA', steps24h: 'CÉIMEANNA (24U)', tokens24h: 'TOKENS (24U)', qualite7j: 'CÁILÍOCHT (7L)' },
  toolbar: {
    process: 'Próiseas', current: 'Fo-ghraf reatha', overview: 'Foramharc', hide_start: 'folaigh START', hide_end: 'folaigh END',
    labels: 'lipéid', follow_sg: 'lean SG', mode_observe: 'Faireachán', mode_debug: 'Sruth dífhabhtaithe',
    current_sg_btn: 'SG reatha', display: 'Taispeáin:', mode: 'Mód:'
  },
  modal: { process_title: 'Próiseas —' },
  status: {
    panel_title: 'Stádas & méadrachtaí', running: 'Ag rith', starting: 'Ag tosú', failed: 'Teipthe',
    completed: 'Críochnaithe', canceled: 'Cealaithe', idle: 'Díomhaoin', unknown: 'Anaithnid'
  },
  io: { title: 'Ionchuir/Aschuir nóid', in: 'IN', out: 'OUT', error: 'EARRÁID' },
  config: {
    title: 'Cumraíocht próisis', general: 'Ginearálta', params: 'Paraiméadair', docs: 'Doiciméadú',
    doc_title: 'Teideal', doc_desc: 'Cur síos', none: 'Níl aon chumraíocht ar fáil'
  },
  graph: {
    error_title: 'Graf', unavailable: 'Níl an graf ar fáil', aria_label: 'Graf Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'earráid rindreála'
  },
  node_menu: {
    aria_actions: 'Gníomhartha nóid', open_sg: 'Oscail fo-ghraf', run_until: 'Rith go dtí',
    break_add: 'Cuir brisphoinnte leis', break_remove: 'Bain brisphoinnte', inspect: 'Iniúchadh'
  },
  control_inputs: {
    debug_label: 'Dífhabhtú:', node_id: 'Aitheantas nóid', when: 'Coinníoll', when_always: 'i gcónaí',
    when_success: 'rath', when_fail: 'teip', when_retry: 'atriail',
    run_until: 'Rith go dtí', break_add: 'Cuir brisphoinnte leis', break_remove: 'Bain brisphoinnte'
  },
  chat: {
    leader_panel_title: 'Ceannaire — Comhrá', placeholder: 'Teachtaireacht...', tools_trace: 'Féach ar lorg na n-uirlisí',
    error_history: 'Theip ar luchtú na staire', empty_reply: '(freagra folamh)', global: 'Comhrá domhanda',
    error_history_global: 'Theip ar luchtú na staire domhanda', you: 'Tú', assistant: 'LLM'
  },
  leader_global: {
    title: 'Ceannaire — Comhrá domhanda', select_label: 'Ceannaire:', select_aria: 'Roghnaigh ceannaire',
    display: 'Ainm taispeána', role: 'Ról', persona: 'Pearsantacht', persona_ph: 'Ceolchoirmeoir oibrithe',
    none_detected: '(níl aon cheannaire)'
  },
  leader_identity_panel: {
    no_leader: 'Níl aon cheannaire sannta', error_read: 'Theip ar léamh céannachta', refresh: 'Athnuaigh',
    display: 'Ainm taispeána', role: 'Ról', persona: 'Pearsantacht', persona_ph: 'Ceolchoirmeoir oibrithe',
    global_chat: 'Comhrá domhanda', leader_workers: 'Oibrithe an cheannaire', loading: 'Ag luchtú…',
    none_attached: 'Níl aon oibrí ceangailte', error_load: 'Earráid luchtaithe'
  },
  list: { title: 'Oibrithe', view: 'Amharc' },
  config_editor: {
    tabs_simple: 'Simplí', tabs_json: 'JSON', beautify: 'Áilleachtaigh', minify: 'Íoslaghdaigh',
    validate: 'Bailíochtaigh', json_valid: 'JSON bailí', json_invalid: 'JSON neamhbhailí',
    complex_only_json: 'Ní féidir roinnt réimsí casta a chur in eagar ach i JSON'
  },
  leader_section: { edit_identity_hint: 'Cuir céannacht in eagar (cliceáil)' },
  replay: {
    title: 'Athsheinm (meaisín ama)', load_run: 'Luchtaigh rith', play: 'Seinn', stop: 'Stop',
    error_runs: 'Theip ar luchtú na rithí', error_steps: 'Theip ar luchtú na gcéimeanna',
    view_node: 'Amharc ar an nód seo', live_announce_step: 'Ag seinm céim {idx}/{total}: {nodeId}'
  }
};
