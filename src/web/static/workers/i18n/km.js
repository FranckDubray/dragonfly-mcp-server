export const __meta = { standalone: true, code: 'km', flag: '🇰🇭', native: 'ខ្មែរ' };
export default {
  lang: { km: 'ខ្មែរ' },
  header: { title: 'កម្មករ និង មេដឹកនាំ', add_leader: '+ បន្ថែម​មេដឹកនាំ', add_worker: '+ បន្ថែម​កម្មករ', leader: 'មេដឹកនាំ:' },
  common: {
    process: 'ដំណើរការ', details: 'ព័ត៌មានលម្អិត', tools_mcp: 'ឧបករណ៍ MCP:', last_step: 'ជំហានចុងក្រោយ',
    edit_identity: 'កែសម្រួលអត្តសញ្ញាណ', close: 'បិទ', start_debug: 'ចាប់ផ្តើម (បញ្ហាស្រាវជ្រាវ)', start_observe: 'ចាប់ផ្តើម (សង្កេត)',
    step: 'ជំហាន', continue: 'បន្ត', stop: 'បញ្ឈប់', copy_in: 'ចម្លង IN', copy_out: 'ចម្លង OUT', copy_err: 'ចម្លងកំហុស',
    error_network: 'បញ្ហាបណ្តាញ', error_action: 'សកម្មភាពបរាជ័យ', ok: 'យល់ព្រម', current_sg: 'គំនូសក្រោមបច្ចុប្បន្ន',
    chat: 'ការសន្ទនា', worker_status: 'ស្ថានភាព', save: 'រក្សាទុក', send: 'ផ្ញើ'
  },
  kpis: { workers: 'កម្មករ', actifs: 'សកម្ម', steps24h: 'ជំហាន (24ម៉ោង)', tokens24h: 'ថូខឹន (24ម៉ោង)', qualite7j: 'គុណភាព (7ថ្ងៃ)' },
  toolbar: {
    process: 'ដំណើរការ', current: 'គំនូសក្រោមបច្ចុប្បន្ន', overview: 'ទិដ្ឋភាពទូទៅ', hide_start: 'លាក់ START', hide_end: 'លាក់ END',
    labels: 'ស្លាក', follow_sg: 'តាម SG', mode_observe: 'សង្កេត', mode_debug: 'ស្ទ្រីមបញ្ហាស្រាវជ្រាវ',
    current_sg_btn: 'SG បច្ចុប្បន្ន', display: 'បង្ហាញ:', mode: 'របៀប:'
  },
  modal: { process_title: 'ដំណើរការ —' },
  status: {
    panel_title: 'ស្ថានភាព និងមាត្រដ្ឋាន', running: 'កំពុងដំណើរការ', starting: 'កំពុងចាប់ផ្តើម', failed: 'បរាជ័យ',
    completed: 'បានបញ្ចប់', canceled: 'បានបោះបង់', idle: 'ទំនេរ', unknown: 'មិនស្គាល់'
  },
  io: { title: 'ធាតុបញ្ចូល/បង្ហាញ', in: 'IN', out: 'OUT', error: 'កំហុស' },
  config: {
    title: 'ការកំណត់រចនាសម្ព័ន្ធ', general: 'ទូទៅ', params: 'ប៉ារ៉ាម៉ែត្រ', docs: 'ឯកសារ',
    doc_title: 'ចំណងជើង', doc_desc: 'ការពិពណ៌នា', none: 'មិនមានការកំណត់រចនាសម្ព័ន្ធ'
  },
  graph: {
    error_title: 'គំនូសតាង', unavailable: 'គំនូសតាងមិនមាន', aria_label: 'គំនូសតាង Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'កំហុសក្នុងការបង្ហាញ'
  },
  node_menu: {
    aria_actions: 'សកម្មភាពថ្នាំង', open_sg: 'បើកគំនូសក្រោម', run_until: 'ដំណើរការរហូតដល់',
    break_add: 'បន្ថែមចំណុចឈប់', break_remove: 'លុបចំណុចឈប់', inspect: 'ពិនិត្យ'
  },
  control_inputs: {
    debug_label: 'បញ្ហាស្រាវជ្រាវ:', node_id: 'លេខសម្គាល់ថ្នាំង', when: 'លក្ខខណ្ឌ', when_always: 'ជានិច្ច',
    when_success: 'ជោគជ័យ', when_fail: 'បរាជ័យ', when_retry: 'ព្យាយាមម្តងទៀត',
    run_until: 'ដំណើរការរហូតដល់', break_add: 'បន្ថែមចំណុចឈប់', break_remove: 'លុបចំណុចឈប់'
  },
  chat: {
    leader_panel_title: 'មេដឹកនាំ — ការសន្ទនា', placeholder: 'សារ...', tools_trace: 'មើលដាននិមិត្តសញ្ញាឧបករណ៍',
    error_history: 'មិនអាចផ្ទុកប្រវត្តិ', empty_reply: '(ចម្លើយទទេ)', global: 'ជជែកសកល',
    error_history_global: 'មិនអាចផ្ទុកប្រវត្តិសកល', you: 'អ្នក', assistant: 'LLM'
  },
  leader_global: {
    title: 'មេដឹកនាំ — ជជែកសកល', select_label: 'មេដឹកនាំ:', select_aria: 'ជ្រើសរើសមេដឹកនាំ',
    display: 'ឈ្មោះបង្ហាញ', role: 'តួនាទី', persona: 'បុគ្គលិកលក្ខណៈ', persona_ph: 'អ្នកសម្របសម្រួលកម្មករ',
    none_detected: '(មិនមានមេដឹកនាំ)'
  },
  leader_identity_panel: {
    no_leader: 'មិនមានមេដឹកនាំបានកំណត់', error_read: 'មិនអាចអានអត្តសញ្ញាណ', refresh: 'ផ្ទុកឡើងវិញ',
    display: 'ឈ្មោះបង្ហាញ', role: 'តួនាទី', persona: 'បុគ្គលិកលក្ខណៈ', persona_ph: 'អ្នកសម្របសម្រួលកម្មករ',
    global_chat: 'ជជែកសកល', leader_workers: 'កម្មករមេដឹកនាំ', loading: 'កំពុងផ្ទុក…',
    none_attached: 'មិនមានកម្មករភ្ជាប់', error_load: 'កំហុសក្នុងការផ្ទុក'
  },
  list: { title: 'កម្មករ', view: 'មើល' },
  config_editor: {
    tabs_simple: 'សាមញ្ញ', tabs_json: 'JSON', beautify: 'ធ្វើឱ្យស្អាត', minify: 'បង្រួម',
    validate: 'ផ្ទៀងផ្ទាត់', json_valid: 'JSON ត្រឹមត្រូវ', json_invalid: 'JSON មិនត្រឹមត្រូវ',
    complex_only_json: 'វាលស្មុគស្មាញមួយចំនួនអាចកែបានតែក្នុង JSON'
  },
  leader_section: { edit_identity_hint: 'កែសម្រួលអត្តសញ្ញាណ (ចុច)' },
  replay: {
    title: 'ចាក់ឡើងវិញ (ម៉ាស៊ីនពេលវេលា)', load_run: 'ផ្ទុកការដំណើរការ', play: 'ចាក់', stop: 'បញ្ឈប់',
    error_runs: 'មិនអាចផ្ទុកការដំណើរការ', error_steps: 'មិនអាចផ្ទុកជំហាន',
    view_node: 'មើលថ្នាំងនេះ', live_announce_step: 'កំពុងចាក់ជំហាន {idx}/{total}: {nodeId}'
  }
};
