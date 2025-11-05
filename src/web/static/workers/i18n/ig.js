export const __meta = { standalone: true, code: 'ig', flag: '🇳🇬', native: 'Igbo' };
export default {
  lang: { ig: 'Igbo' },
  common: {
    process: 'Usoro', details: 'Nkọwa', tools_mcp: 'Ngwaọrụ MCP:', last_step: 'Nzọụkwụ ikpeazụ',
    edit_identity: 'Lelee/gbanwee njirimara', close: 'Mechie', start_debug: 'Malite (ndozi)', start_observe: 'Malite (lelee)',
    step: 'Nzọụkwụ', continue: 'Gaa n'ihu', stop: 'Kwụsị', copy_in: 'Depụta IN', copy_out: 'Depụta OUT', copy_err: 'Depụta njehie',
    error_network: 'Njehie netwọk', error_action: 'Omume dara ada', ok: 'Ọ dị mma', current_sg: 'Subgraph dị ugbu a',
    chat: 'Mkparịta ụka', worker_status: 'Ọnọdụ ọrụ', save: 'Chekwaa', send: 'Zipu'
  },
  header: { title: 'Ọrụ́ & ndị isi', add_leader: '+ Tinye onye isi', add_worker: '+ Tinye onye ọrụ', leader: 'Onye isi:' },
  kpis: { workers: 'ỌRỤ́', actifs: 'NA-ARỤ ỌRỤ', steps24h: 'NZỌỤKWỤ (24H)', tokens24h: 'TOKENS (24H)', qualite7j: 'ỌDỊ MMA (7D)' },
  toolbar: {
    process: 'Usoro', current: 'Subgraph dị ugbu a', overview: 'Nlele niile', hide_start: 'zoo START', hide_end: 'zoo END',
    labels: 'akara', follow_sg: 'soro SG', mode_observe: 'Lelee', mode_debug: 'Ndozi ngwa ngwa',
    current_sg_btn: 'SG dị ugbu a', display: 'Ngosi:', mode: 'Ụdị:'
  },
  modal: { process_title: 'Usoro —' },
  status: {
    panel_title: 'Ọnọdụ & nha', running: 'Na-arụ ọrụ', starting: 'Na-amalite', failed: 'Dara ada',
    completed: 'Emechara', canceled: 'Kagburu', idle: 'Dị jụụ', unknown: 'Amabeghị'
  },
  io: { title: 'Ntinye/Npụpụ nke node', in: 'IN', out: 'OUT', error: 'NJEHIE' },
  config: {
    title: 'Nhazi usoro', general: 'N'ozuzu', params: 'Nhazi', docs: 'Akwụkwọ nduzi',
    doc_title: 'Isiokwu', doc_desc: 'Nkọwa', none: 'Enweghị nhazi'
  },
  graph: {
    error_title: 'Eserese', unavailable: 'Eserese adịghị', aria_label: 'Eserese Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'njehie ngosi'
  },
  node_menu: {
    aria_actions: 'Omume node', open_sg: 'Meghee subgraph', run_until: 'Rụọ ruo',
    break_add: 'Tinye ebe nkwụsị', break_remove: 'Wepụ ebe nkwụsị', inspect: 'Nyocha'
  },
  control_inputs: {
    debug_label: 'Ndozi:', node_id: 'ID node', when: 'Mgbe', when_always: 'mgbe niile',
    when_success: 'mgbe ọ gara nke ọma', when_fail: 'mgbe ọ dara ada', when_retry: 'mgbe ọ nwaleghachiri',
    run_until: 'Rụọ ruo', break_add: 'Tinye nkwụsị', break_remove: 'Wepụ nkwụsị'
  },
  chat: {
    leader_panel_title: 'Onye isi — Mkparịta ụka', placeholder: 'Ozi...', tools_trace: 'Lee akara ngwaọrụ',
    error_history: 'Akụkọ ihe mere eme adataghi', empty_reply: '(azịza tọgbọrọ chakoo)', global: 'Mkparịta ụka zuru ụwa ọnụ',
    error_history_global: 'Akụkọ zuru ụwa adataghi', you: 'Gị', assistant: 'LLM'
  },
  leader_global: {
    title: 'Onye isi — Mkparịta ụka zuru ụwa', select_label: 'Onye isi:', select_aria: 'Họrọ onye isi',
    display: 'Aha ngosi', role: 'Ọrụ', persona: 'Àgwà', persona_ph: 'Onye na-achịkọta ndị ọrụ',
    none_detected: '(enweghị onye isi)'
  },
  leader_identity_panel: {
    no_leader: 'Enyebeghị onye isi', error_read: 'Njemara agụtaghị', refresh: 'Tọgharịa',
    display: 'Aha ngosi', role: 'Ọrụ', persona: 'Àgwà', persona_ph: 'Onye na-achịkọta ndị ọrụ',
    global_chat: 'Mkparịta ụka zuru ụwa', leader_workers: 'Ndị ọrụ onye isi', loading: 'Na-ebubata...',
    none_attached: 'Enweghị ọrụ jikọrọ', error_load: 'Nsogbu ịbulite'
  },
  list: { title: 'Ndị ọrụ', view: 'Lelee' },
  config_editor: {
    tabs_simple: 'Dị mfe', tabs_json: 'JSON', beautify: 'Mee ka ọ mara mma', minify: 'Mee ka ọ dị mkpụmkpụ',
    validate: 'Nyocha njikọ', json_valid: 'JSON ziri ezi', json_invalid: 'JSON ezighi ezi',
    complex_only_json: 'Ụfọdụ ubi dị mgbagwoju anya nwere ike ịgbanwe naanị na JSON'
  },
  leader_section: { edit_identity_hint: 'Gbanwee njirimara (pịa)' },
  replay: {
    title: 'Kụgharịa (ụgbọ oge)', load_run: 'Bulite ọrụ gara aga', play: 'Kpọọ', stop: 'Kwụsị',
    error_runs: 'Ọrụ gara aga adataghi', error_steps: 'Nzọụkwụ adataghi',
    view_node: 'Lelee node a', live_announce_step: 'Na-akpọ nzọụkwụ {idx}/{total}: {nodeId}'
  }
};
