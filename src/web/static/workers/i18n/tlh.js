export const __meta = { standalone: true, code: 'tlh', flag: '🖖', native: "tlhIngan Hol" };
export default {
  lang: { tlh: "tlhIngan Hol" },
  header: { title: "vumwI'pu' je DevwI'pu'", add_leader: "+ DevwI' chenmoH", add_worker: "+ vumwI' chenmoH", leader: "DevwI':" },
  common: {
    process: "tlham", details: "ngoq", tools_mcp: "MCP janmey:", last_step: "moQ Qav", 
    edit_identity: "pong choH", close: "SoQ", start_debug: "tagh (qaD)", start_observe: "tagh (legh)", 
    step: "moQ", continue: "taH", stop: "mev", copy_in: "Copy IN", copy_out: "Copy OUT", copy_err: "Copy Qagh",
    error_network: "Qum Qagh", error_action: "vang Qagh", ok: "maj", current_sg: "SG DaH",
    chat: "Qum", worker_status: "Dotlh", save: "pol", send: "ngeH"
  },
  kpis: { workers: "VUMWI'mey", actifs: "Qap", steps24h: "moQ (24H)", tokens24h: "TOKENS (24H)", qualite7j: "Qav (7j)" },
  toolbar: {
    process: "tlham", current: "SG DaH", overview: "naw'", hide_start: "START So'", hide_end: "END So'",
    labels: "per", follow_sg: "SG tlha'", mode_observe: "legh", mode_debug: "qaD stream",
    current_sg_btn: "SG DaH", display: "'ang:", mode: "mIw:"
  },
  modal: { process_title: "tlham —" },
  status: {
    panel_title: "Dotlh je vI'", running: "vum", starting: "taghlu'", failed: "luj",
    completed: "rIn", canceled: "qIl", idle: "leng", unknown: "Sovbe'"
  },
  io: { title: "node lel/lob", in: "IN", out: "OUT", error: "QAGH" },
  config: {
    title: "tlham DeS", general: "Hoch", params: "wIv", docs: "ghItlh",
    doc_title: "pong", doc_desc: "QIj", none: "DeS tu'be'"
  },
  graph: {
    error_title: "lIw", unavailable: "lIw tu'be'", aria_label: "Mermaid lIw",
    mermaid_error_prefix: "Mermaid — ", render_error: "cha' Qagh"
  },
  node_menu: {
    aria_actions: "node vang", open_sg: "SG poSmoH", run_until: "... pIm qet",
    break_add: "mev Daq chel", break_remove: "mev Daq teq", inspect: "nej"
  },
  control_inputs: {
    debug_label: "qaD:", node_id: "node ID", when: "ghu'", when_always: "reH",
    when_success: "Qap", when_fail: "luj", when_retry: "nID",
    run_until: "... pIm qet", break_add: "mev chel", break_remove: "mev teq"
  },
  chat: {
    leader_panel_title: "DevwI' — Qum", placeholder: "ja'...", tools_trace: "jan nID legh",
    error_history: "qun lod luj", empty_reply: "(chIm jang)", global: "Hoch Qum",
    error_history_global: "Hoch qun lod luj", you: "SoH", assistant: "LLM"
  },
  leader_global: {
    title: "DevwI' — Hoch Qum", select_label: "DevwI':", select_aria: "DevwI' wIv",
    display: "pong cha'", role: "Qu'", persona: "nugh", persona_ph: "vumwI' DevwI'",
    none_detected: "(DevwI' tu'be')"
  },
  leader_identity_panel: {
    no_leader: "DevwI' tuQlu'be'", error_read: "pong laD luj", refresh: "chu'",
    display: "pong cha'", role: "Qu'", persona: "nugh", persona_ph: "vumwI' DevwI'",
    global_chat: "Hoch Qum", leader_workers: "DevwI' vumwI'pu'", loading: "lod...",
    none_attached: "vumwI' qIl tu'be'", error_load: "lod Qagh"
  },
  list: { title: "vumwI'pu'", view: "legh" },
  config_editor: {
    tabs_simple: "nap", tabs_json: "JSON", beautify: "'IH", minify: "mach",
    validate: "wIv", json_valid: "JSON pIm", json_invalid: "JSON Qagh",
    complex_only_json: "Duj Daq JSON neH choH"
  },
  leader_section: { edit_identity_hint: "pong choH (ghItlh)" },
  replay: {
    title: "nID (poH jan)", load_run: "vang lod", play: "chu'", stop: "mev",
    error_runs: "vang lod luj", error_steps: "moQ lod luj",
    view_node: "node DaH legh", live_announce_step: "moQ {idx}/{total} chu': {nodeId}"
  }
};
