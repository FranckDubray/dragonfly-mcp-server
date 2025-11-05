export const __meta = { standalone: true, code: 'en', flag: '🇪🇺', native: 'English' };
export default {
  lang: { en: 'English' },
  header: { title: 'Workers & Leaders', add_leader: '+ Add leader', add_worker: '+ Add worker', leader: 'Leader:' },
  common: {
    process: 'Process', details: 'Details', tools_mcp: 'Tools MCP:', last_step: 'Last step',
    edit_identity: 'View/edit identity', close: 'Close', start_debug: 'Start (debug)', start_observe: 'Start (observe)',
    step: 'Step', continue: 'Continue', stop: 'Stop', copy_in: 'Copy IN', copy_out: 'Copy OUT', copy_err: 'Copy error',
    error_network: 'Network error', error_action: 'Action failed', ok: 'OK', current_sg: 'Current subgraph',
    chat: 'Chat', worker_status: 'Status', save: 'Save', send: 'Send'
  },
  kpis: { workers: 'WORKERS', actifs: 'ACTIVE', steps24h: 'STEPS (24H)', tokens24h: 'TOKENS (24H)', qualite7j: 'QUALITY (7D)' },
  toolbar: {
    process: 'Process', current: 'Current subgraph', overview: 'Overview', hide_start: 'hide START', hide_end: 'hide END',
    labels: 'labels', follow_sg: 'follow SG', mode_observe: 'Observe', mode_debug: 'Debug stream', current_sg_btn: 'Current SG',
    display: 'Display:', mode: 'Mode:'
  },
  modal: { process_title: 'Process —' },
  status: {
    panel_title: 'Status & metrics', running: 'Running', starting: 'Starting', failed: 'Failed', completed: 'Completed',
    canceled: 'Canceled', idle: 'Idle', unknown: 'Unknown'
  },
  io: { title: 'Node inputs/outputs', in: 'IN', out: 'OUT', error: 'ERROR' },
  config: {
    title: 'Process configuration', general: 'General', params: 'Parameters', docs: 'Documentation', doc_title: 'Title',
    doc_desc: 'Description', none: 'No configuration available'
  },
  graph: {
    error_title: 'Graph', unavailable: 'Graph unavailable', aria_label: 'Mermaid graph', mermaid_error_prefix: 'Mermaid — ',
    render_error: 'render error'
  },
  node_menu: {
    aria_actions: 'Node actions', open_sg: 'Open subgraph', run_until: 'Run until', break_add: 'Add breakpoint',
    break_remove: 'Remove breakpoint', inspect: 'Inspect'
  },
  control_inputs: {
    debug_label: 'Debug:', node_id: 'Node ID', when: 'Condition', when_always: 'always', when_success: 'success',
    when_fail: 'fail', when_retry: 'retry', run_until: 'Run until', break_add: 'Add breakpoint', break_remove: 'Remove breakpoint'
  },
  chat: {
    leader_panel_title: 'Leader — Chat', placeholder: 'Message...', tools_trace: 'View tools traces',
    error_history: 'Failed to load history', empty_reply: '(empty reply)', global: 'Global chat',
    error_history_global: 'Failed to load global history', you: 'You', assistant: 'LLM'
  },
  leader_global: {
    title: 'Leader — Global chat', select_label: 'Leader:', select_aria: 'Select a leader', display: 'Display name',
    role: 'Role', persona: 'Persona', persona_ph: 'Workers orchestrator', none_detected: '(no leader)'
  },
  leader_identity_panel: {
    no_leader: 'No leader assigned', error_read: 'Failed to read identity', refresh: 'Refresh', display: 'Display name',
    role: 'Role', persona: 'Persona', persona_ph: 'Workers orchestrator', global_chat: 'Global chat',
    leader_workers: 'Leader workers', loading: 'Loading…', none_attached: 'No attached worker', error_load: 'Load error'
  },
  list: { title: 'Workers', view: 'View' },
  config_editor: {
    tabs_simple: 'Simple', tabs_json: 'JSON', beautify: 'Beautify', minify: 'Minify', validate: 'Validate',
    json_valid: 'Valid JSON', json_invalid: 'Invalid JSON', complex_only_json: 'Some complex fields are only editable in JSON'
  },
  leader_section: { edit_identity_hint: 'Edit identity (click)' },
  replay: {
    title: 'Replay (time machine)', load_run: 'Load run', play: 'Play', stop: 'Stop',
    error_runs: 'Failed to load runs', error_steps: 'Failed to load steps', view_node: 'View this node',
    live_announce_step: 'Playing step {idx}/{total}: {nodeId}'
  }
};
