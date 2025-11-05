export const __meta = { standalone: true, code: 'su-Latn', flag: '🇮🇩', native: 'Basa Sunda' };
export default {
  lang: { 'su-Latn': 'Basa Sunda' },
  header: { title: 'Pagawé & Pamingpin', add_leader: '+ Tambah pamingpin', add_worker: '+ Tambah pagawé', leader: 'Pamingpin:' },
  common: {
    process: 'Prosés', details: 'Rincian', tools_mcp: 'Parabot MCP:', last_step: 'Léngkah ahir',
    edit_identity: 'Témbongkeun/édit identitas', close: 'Tutup', start_debug: 'Mimitian (debug)', start_observe: 'Mimitian (observasi)',
    step: 'Léngkah', continue: 'Teruskeun', stop: 'Eureun', copy_in: 'Salin IN', copy_out: 'Salin OUT', copy_err: 'Salin kasalahan',
    error_network: 'Kasalahan jaringan', error_action: 'Tindakan gagal', ok: 'Muhun', current_sg: 'Subgraf ayeuna',
    chat: 'Obrolan', worker_status: 'Status', save: 'Simpen', send: 'Kirim'
  },
  kpis: { workers: 'PAGAWÉ', actifs: 'AKTIP', steps24h: 'LÉNGKAH (24JAM)', tokens24h: 'TOKEN (24JAM)', qualite7j: 'KUALITAS (7POÉ)' },
  toolbar: {
    process: 'Prosés', current: 'Subgraf ayeuna', overview: 'Ringkesan', hide_start: 'sumputkeun START', hide_end: 'sumputkeun END',
    labels: 'labél', follow_sg: 'tuturkeun SG', mode_observe: 'Observasi', mode_debug: 'Stream debug',
    current_sg_btn: 'SG ayeuna', display: 'Témbongkeun:', mode: 'Mode:'
  },
  modal: { process_title: 'Prosés —' },
  status: {
    panel_title: 'Status jeung métrik', running: 'Ngajalankeun', starting: 'Ngamimitian', failed: 'Gagal',
    completed: 'Réngsé', canceled: 'Dibatalkeun', idle: 'Nganggur', unknown: 'Teu kanyahoan'
  },
  io: { title: 'Input/output titik', in: 'IN', out: 'OUT', error: 'KASALAHAN' },
  config: {
    title: 'Konfigurasi prosés', general: 'Umum', params: 'Parameter', docs: 'Dokuméntasi',
    doc_title: 'Judul', doc_desc: 'Pedaran', none: 'Euweuh konfigurasi sayagi'
  },
  graph: {
    error_title: 'Grafik', unavailable: 'Grafik teu sayagi', aria_label: 'Grafik Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'kasalahan render'
  },
  node_menu: {
    aria_actions: 'Tindakan titik', open_sg: 'Buka subgraf', run_until: 'Jalankeun nepi ka',
    break_add: 'Tambahkeun breakpoint', break_remove: 'Cabut breakpoint', inspect: 'Pariksa'
  },
  control_inputs: {
    debug_label: 'Debug:', node_id: 'ID titik', when: 'Kaayaan', when_always: 'salawasna',
    when_success: 'suksés', when_fail: 'gagal', when_retry: 'cobaan deui',
    run_until: 'Jalankeun nepi ka', break_add: 'Tambahkeun breakpoint', break_remove: 'Cabut breakpoint'
  },
  chat: {
    leader_panel_title: 'Pamingpin — Obrolan', placeholder: 'Pesen...', tools_trace: 'Témbongkeun jejak parabot',
    error_history: 'Gagal ngamuat sajarah', empty_reply: '(balesan kosong)', global: 'Obrolan global',
    error_history_global: 'Gagal ngamuat sajarah global', you: 'Anjeun', assistant: 'LLM'
  },
  leader_global: {
    title: 'Pamingpin — Obrolan global', select_label: 'Pamingpin:', select_aria: 'Pilih pamingpin',
    display: 'Ngaran témbong', role: 'Peran', persona: 'Persona', persona_ph: 'Orkestrator pagawé',
    none_detected: '(euweuh pamingpin)'
  },
  leader_identity_panel: {
    no_leader: 'Euweuh pamingpin ditugaskeun', error_read: 'Gagal maca identitas', refresh: 'Segerkeun',
    display: 'Ngaran témbong', role: 'Peran', persona: 'Persona', persona_ph: 'Orkestrator pagawé',
    global_chat: 'Obrolan global', leader_workers: 'Pagawé pamingpin', loading: 'Ngamuat…',
    none_attached: 'Euweuh pagawé dilampirkeun', error_load: 'Kasalahan ngamuat'
  },
  list: { title: 'Pagawé', view: 'Témbongkeun' },
  config_editor: {
    tabs_simple: 'Basajan', tabs_json: 'JSON', beautify: 'Pageuhkeun', minify: 'Ngaleutikan',
    validate: 'Validasi', json_valid: 'JSON sah', json_invalid: 'JSON teu sah',
    complex_only_json: 'Sababaraha widang kompléks ngan bisa diédit dina JSON'
  },
  leader_section: { edit_identity_hint: 'Édit identitas (klik)' },
  replay: {
    title: 'Puteran deui (mesin waktu)', load_run: 'Muat jalankeun', play: 'Puteran', stop: 'Eureun',
    error_runs: 'Gagal ngamuat jalankeun', error_steps: 'Gagal ngamuat léngkah',
    view_node: 'Témbongkeun titik ieu', live_announce_step: 'Muteran léngkah {idx}/{total}: {nodeId}'
  }
};
