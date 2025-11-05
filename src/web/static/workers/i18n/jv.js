export const __meta = { standalone: true, code: 'jv', flag: '🇮🇩', native: 'Basa Jawa' };
export default {
  lang: { jv: 'Basa Jawa' },
  common: {
    process: 'Proses', details: 'Rincian', tools_mcp: 'Piranti MCP:', last_step: 'Langkah pungkasan',
    edit_identity: 'Deleng/besut identitas', close: 'Tutup', start_debug: 'Miwiti (debug)', start_observe: 'Miwiti (ngawasi)',
    step: 'Langkah', continue: 'Terusake', stop: 'Mandheg', copy_in: 'Salin IN', copy_out: 'Salin OUT', copy_err: 'Salin kesalahan',
    error_network: 'Kesalahan jaringan', error_action: 'Tindakan gagal', ok: 'OK', current_sg: 'Subgraf saiki',
    chat: 'Obrolan', worker_status: 'Status buruh', save: 'Simpen', send: 'Kirim'
  },
  header: { title: 'Buruh & Pimpinan', add_leader: '+ Tambah pimpinan', add_worker: '+ Tambah buruh', leader: 'Pimpinan:' },
  kpis: { workers: 'BURUH', actifs: 'AKTIF', steps24h: 'LANGKAH (24J)', tokens24h: 'TOKEN (24J)', qualite7j: 'KUALITAS (7D)' },
  toolbar: {
    process: 'Proses', current: 'Subgraf saiki', overview: 'Ringkesan', hide_start: 'singidake START', hide_end: 'singidake END',
    labels: 'label', follow_sg: 'tindakake SG', mode_observe: 'Ngawasi', mode_debug: 'Debug stream',
    current_sg_btn: 'SG saiki', display: 'Tampilan:', mode: 'Mode:'
  },
  modal: { process_title: 'Proses —' },
  status: {
    panel_title: 'Status lan metrik', running: 'Mlaku', starting: 'Miwiti', failed: 'Gagal',
    completed: 'Rampung', canceled: 'Dibatalake', idle: 'Nganggur', unknown: 'Ora dingerteni'
  },
  io: { title: 'Input/output node', in: 'IN', out: 'OUT', error: 'KESALAHAN' },
  config: {
    title: 'Konfigurasi proses', general: 'Umum', params: 'Parameter', docs: 'Dokumentasi',
    doc_title: 'Judhul', doc_desc: 'Katerangan', none: 'Ora ana konfigurasi'
  },
  graph: {
    error_title: 'Graf', unavailable: 'Graf ora kasedhiya', aria_label: 'Graf Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'kesalahan render'
  },
  node_menu: {
    aria_actions: 'Tumindak node', open_sg: 'Bukak subgraf', run_until: 'Mlaku nganti',
    break_add: 'Tambahake breakpoint', break_remove: 'Busak breakpoint', inspect: 'Priksa'
  },
  control_inputs: {
    debug_label: 'Debug:', node_id: 'ID node', when: 'Nalika', when_always: 'tansah',
    when_success: 'sukses', when_fail: 'gagal', when_retry: 'nyoba maneh',
    run_until: 'Mlaku nganti', break_add: 'Tambahake breakpoint', break_remove: 'Busak breakpoint'
  },
  chat: {
    leader_panel_title: 'Pimpinan — Obrolan', placeholder: 'Pesen...', tools_trace: 'Deleng jejak piranti',
    error_history: 'Gagal ngemot riwayat', empty_reply: '(wangsulan kosong)', global: 'Obrolan global',
    error_history_global: 'Gagal ngemot riwayat global', you: 'Sampeyan', assistant: 'LLM'
  },
  leader_global: {
    title: 'Pimpinan — Obrolan global', select_label: 'Pimpinan:', select_aria: 'Pilih pimpinan',
    display: 'Jeneng tampilan', role: 'Peran', persona: 'Persona', persona_ph: 'Orkestrator buruh',
    none_detected: '(ora ana pimpinan)'
  },
  leader_identity_panel: {
    no_leader: 'Ora ana pimpinan sing ditugasake', error_read: 'Gagal maca identitas', refresh: 'Anyari',
    display: 'Jeneng tampilan', role: 'Peran', persona: 'Persona', persona_ph: 'Orkestrator buruh',
    global_chat: 'Obrolan global', leader_workers: 'Buruh pimpinan', loading: 'Ngemot…',
    none_attached: 'Ora ana buruh sing dilampirake', error_load: 'Kesalahan ngemot'
  },
  list: { title: 'Buruh', view: 'Deleng' },
  config_editor: {
    tabs_simple: 'Prasaja', tabs_json: 'JSON', beautify: 'Apikake', minify: 'Cilikake',
    validate: 'Validasi', json_valid: 'JSON bener', json_invalid: 'JSON salah',
    complex_only_json: 'Sawetara kolom rumit mung bisa dibesut ing JSON'
  },
  leader_section: { edit_identity_hint: 'Besut identitas (klik)' },
  replay: {
    title: 'Muter maneh (mesin wektu)', load_run: 'Muat jalanake', play: 'Muter', stop: 'Mandheg',
    error_runs: 'Gagal ngemot jalanake', error_steps: 'Gagal ngemot langkah',
    view_node: 'Deleng node iki', live_announce_step: 'Muter langkah {idx}/{total}: {nodeId}'
  }
};
