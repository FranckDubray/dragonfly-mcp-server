export const __meta = { standalone: true, code: 'sw', flag: '🇹🇿', native: 'Kiswahili' };
export default {
  lang: { sw: 'Kiswahili' },
  common: {
    process: 'Mchakato', details: 'Maelezo', tools_mcp: 'Zana za MCP:', last_step: 'Hatua ya mwisho',
    edit_identity: 'Angalia/hariri utambulisho', close: 'Funga', start_debug: 'Anza (utatuzi)', start_observe: 'Anza (chunguza)',
    step: 'Hatua', continue: 'Endelea', stop: 'Simama', copy_in: 'Nakili IN', copy_out: 'Nakili OUT', copy_err: 'Nakili hitilafu',
    error_network: 'Hitilafu ya mtandao', error_action: 'Kitendo kimeshindwa', ok: 'Sawa', current_sg: 'Grafu ndogo ya sasa',
    chat: 'Mazungumzo', worker_status: 'Hali ya mfanyakazi', save: 'Hifadhi', send: 'Tuma'
  },
  header: { title: 'Wafanyakazi na Viongozi', add_leader: '+ Ongeza kiongozi', add_worker: '+ Ongeza mfanyakazi', leader: 'Kiongozi:' },
  kpis: { workers: 'WAFANYAKAZI', actifs: 'HAI', steps24h: 'HATUA (24H)', tokens24h: 'ALAMA (24H)', qualite7j: 'UBORA (7S)' },
  toolbar: {
    process: 'Mchakato', current: 'Grafu ndogo ya sasa', overview: 'Muhtasari', hide_start: 'ficha START', hide_end: 'ficha END',
    labels: 'lebo', follow_sg: 'fuata SG', mode_observe: 'Chunguza', mode_debug: 'Mtiririko wa utatuzi',
    current_sg_btn: 'SG ya sasa', display: 'Onyesho:', mode: 'Hali:'
  },
  modal: { process_title: 'Mchakato —' },
  status: {
    panel_title: 'Hali na vipimo', running: 'Inafanya kazi', starting: 'Inaanza', failed: 'Imeshindwa',
    completed: 'Imekamilika', canceled: 'Imefutwa', idle: 'Tulivu', unknown: 'Haijulikani'
  },
  io: { title: 'Ingizo/Matokeo ya nodi', in: 'IN', out: 'OUT', error: 'HITILAFU' },
  config: {
    title: 'Usanidi wa mchakato', general: 'Jumla', params: 'Vigezo', docs: 'Nyaraka',
    doc_title: 'Kichwa', doc_desc: 'Maelezo', none: 'Hakuna usanidi unapatikana'
  },
  graph: {
    error_title: 'Grafu', unavailable: 'Grafu haipatikani', aria_label: 'Grafu ya Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'hitilafu ya uonyeshaji'
  },
  node_menu: {
    aria_actions: 'Vitendo vya nodi', open_sg: 'Fungua grafu ndogo', run_until: 'Endesha hadi',
    break_add: 'Ongeza sehemu ya kusimamisha', break_remove: 'Ondoa sehemu ya kusimamisha', inspect: 'Kagua'
  },
  control_inputs: {
    debug_label: 'Utatuzi:', node_id: 'Kitambulisho cha nodi', when: 'Masharti', when_always: 'kila wakati',
    when_success: 'mafanikio', when_fail: 'kushindwa', when_retry: 'jaribu tena',
    run_until: 'Endesha hadi', break_add: 'Ongeza kusimamisha', break_remove: 'Ondoa kusimamisha'
  },
  chat: {
    leader_panel_title: 'Kiongozi — Mazungumzo', placeholder: 'Ujumbe...', tools_trace: 'Tazama alama za zana',
    error_history: 'Imeshindwa kupakia historia', empty_reply: '(jibu tupu)', global: 'Mazungumzo ya kimataifa',
    error_history_global: 'Imeshindwa kupakia historia ya kimataifa', you: 'Wewe', assistant: 'LLM'
  },
  leader_global: {
    title: 'Kiongozi — Mazungumzo ya kimataifa', select_label: 'Kiongozi:', select_aria: 'Chagua kiongozi',
    display: 'Jina la kuonyesha', role: 'Jukumu', persona: 'Utu', persona_ph: 'Mratibu wa wafanyakazi',
    none_detected: '(hakuna kiongozi)'
  },
  leader_identity_panel: {
    no_leader: 'Hakuna kiongozi kilichopangwa', error_read: 'Imeshindwa kusoma utambulisho', refresh: 'Sasisha',
    display: 'Jina la kuonyesha', role: 'Jukumu', persona: 'Utu', persona_ph: 'Mratibu wa wafanyakazi',
    global_chat: 'Mazungumzo ya kimataifa', leader_workers: 'Wafanyakazi wa kiongozi', loading: 'Inapakia…',
    none_attached: 'Hakuna mfanyakazi aliyeambatanishwa', error_load: 'Hitilafu ya upakiaji'
  },
  list: { title: 'Wafanyakazi', view: 'Angalia' },
  config_editor: {
    tabs_simple: 'Rahisi', tabs_json: 'JSON', beautify: 'Pamba', minify: 'Punguza',
    validate: 'Thibitisha', json_valid: 'JSON sahihi', json_invalid: 'JSON si sahihi',
    complex_only_json: 'Baadhi ya sehemu ngumu zinaweza kuhaririwa tu katika JSON'
  },
  leader_section: { edit_identity_hint: 'Hariri utambulisho (bofya)' },
  replay: {
    title: 'Rudia (mashine ya wakati)', load_run: 'Pakia utekelezaji', play: 'Cheza', stop: 'Simama',
    error_runs: 'Imeshindwa kupakia utekelezaji', error_steps: 'Imeshindwa kupakia hatua',
    view_node: 'Angalia nodi hii', live_announce_step: 'Inacheza hatua {idx}/{total}: {nodeId}'
  }
};
