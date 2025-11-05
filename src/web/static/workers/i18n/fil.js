export const __meta = { standalone: true, code: 'fil', flag: '🇵🇭', native: 'Filipino' };
export default {
  lang: { fil: 'Filipino' },
  header: { title: 'Mga manggagawa at pinuno', add_leader: '+ Magdagdag ng pinuno', add_worker: '+ Magdagdag ng manggagawa', leader: 'Pinuno:' },
  common: {
    process: 'Proseso', details: 'Mga detalye', tools_mcp: 'Mga gamit MCP:', last_step: 'Huling hakbang',
    edit_identity: 'Tingnan/I-edit ang pagkakakilanlan', close: 'Isara', start_observe: 'Simulan (obserbahan)', start_debug: 'Simulan (debug)',
    step: 'Hakbang', continue: 'Magpatuloy', stop: 'Itigil', copy_in: 'Kopyahin ang IN', copy_out: 'Kopyahin ang OUT', copy_err: 'Kopyahin ang error',
    error_network: 'Error sa network', error_action: 'Nabigo ang aksyon', ok: 'OK', current_sg: 'Kasalukuyang subgraph',
    chat: 'Chat', worker_status: 'Katayuan', save: 'I-save', send: 'Ipadala',
    status_metrics: 'Katayuan at sukatan', running: 'Tumatakbo', starting: 'Sinisimulan', failed: 'Nabigo', completed: 'Kumpleto', canceled: 'Kanselado', idle: 'Hindi aktibo', unknown: 'Hindi alam'
  },
  kpis: { workers: 'MGA MANGGAGAWA', actifs: 'AKTIBO', steps24h: 'MGA HAKBANG (24H)', tokens24h: 'MGA TOKEN (24H)', qualite7j: 'KALIDAD (7D)' },
  toolbar: {
    process: 'Proseso', current: 'Kasalukuyang subgraph', overview: 'Pangkalahatang-ideya', hide_start: 'itago ang START', hide_end: 'itago ang END',
    labels: 'mga label', follow_sg: 'sundan ang SG', mode_observe: 'Obserbahan', mode_debug: 'Daloy ng debug', current_sg_btn: 'Kasalukuyang SG',
    display: 'Ipakita:', mode: 'Mode:'
  },
  modal: { process_title: 'Proseso —' },
  status: { panel_title: 'Katayuan at sukatan', running: 'Tumatakbo', starting: 'Sinisimulan', failed: 'Nabigo', completed: 'Kumpleto', canceled: 'Kanselado', idle: 'Hindi aktibo', unknown: 'Hindi alam' },
  io: { title: 'Mga input/output ng node', in: 'IN', out: 'OUT', error: 'ERROR' },
  config: { title: 'Konfigurasyon ng proseso', general: 'Pangkalahatan', params: 'Mga parameter', docs: 'Dokumentasyon', doc_title: 'Pamagat', doc_desc: 'Paglalarawan', none: 'Walang magagamit na konfigurasyon' },
  graph: { error_title: 'Grap', unavailable: 'Hindi magagamit ang grap', aria_label: 'Grap ng Mermaid', mermaid_error_prefix: 'Mermaid — ', render_error: 'error sa render' },
  node_menu: { aria_actions: 'Mga aksyon ng node', open_sg: 'Buksan ang subgraph', run_until: 'Patakbuhin hanggang', break_add: 'Magdagdag ng breakpoint', break_remove: 'Alisin ang breakpoint', inspect: 'Suriin' },
  control_inputs: { debug_label: 'Debug:', node_id: 'ID ng node', when: 'Kondisyon', when_always: 'palagi', when_success: 'tagumpay', when_fail: 'kabiguan', when_retry: 'subukang muli', run_until: 'Patakbuhin hanggang', break_add: 'Magdagdag ng breakpoint', break_remove: 'Alisin ang breakpoint' },
  chat: { leader_panel_title: 'Pinuno — Chat', placeholder: 'Mensahe...', tools_trace: 'Tingnan ang mga bakas ng gamit', error_history: 'Hindi ma-load ang kasaysayan', empty_reply: '(walang laman na tugon)', global: 'Global na chat', error_history_global: 'Hindi ma-load ang global na kasaysayan', you: 'Ikaw', assistant: 'LLM' },
  leader_global: { title: 'Pinuno — Global na chat', select_label: 'Pinuno:', select_aria: 'Pumili ng pinuno', display: 'Pangalan sa display', role: 'Gampanin', persona: 'Persona', persona_ph: 'Orkestrador ng mga worker', none_detected: '(walang pinuno)' },
  leader_identity_panel: { no_leader: 'Walang nakatalagang pinuno', error_read: 'Hindi mabasa ang pagkakakilanlan', refresh: 'I-refresh', display: 'Pangalan sa display', role: 'Gampanin', persona: 'Persona', persona_ph: 'Orkestrador ng mga worker', global_chat: 'Global na chat', leader_workers: 'Mga worker ng pinuno', loading: 'Naglo-load…', none_attached: 'Walang nakalakip na worker', error_load: 'Error sa paglo-load' },
  list: { title: 'Mga manggagawa', view: 'Tingnan' },
  config_editor: { tabs_simple: 'Simple', tabs_json: 'JSON', beautify: 'Ayusin', minify: 'Paliitin', validate: 'Beripikahin', json_valid: 'Balidong JSON', json_invalid: 'Hindi balidong JSON', complex_only_json: 'Ang ilang kumplikadong field ay mae-edit lamang sa JSON' },
  leader_section: { edit_identity_hint: 'I-edit ang pagkakakilanlan (i-click)' },
  replay: { title: 'Pag-replay (time machine)', load_run: 'I-load ang run', play: 'I-play', stop: 'Itigil', error_runs: 'Hindi ma-load ang mga run', error_steps: 'Hindi ma-load ang mga hakbang', view_node: 'Tingnan ang node na ito', live_announce_step: 'Pinapatugtog ang hakbang {idx}/{total}: {nodeId}' }
};
