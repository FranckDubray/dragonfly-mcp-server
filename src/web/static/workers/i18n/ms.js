export const __meta = { standalone: true, code: 'ms', flag: '🇲🇾', native: 'Bahasa Melayu' };
export default {
  lang: { ms: 'Bahasa Melayu' },
  common: {
    process: 'Proses', details: 'Butiran', tools_mcp: 'Alatan MCP:', last_step: 'Langkah terakhir',
    edit_identity: 'Lihat/sunting identiti', close: 'Tutup', start_debug: 'Mula (nyahpepijat)', start_observe: 'Mula (pemerhatian)',
    step: 'Langkah', continue: 'Teruskan', stop: 'Henti', copy_in: 'Salin IN', copy_out: 'Salin OUT', copy_err: 'Salin ralat',
    error_network: 'Ralat rangkaian', error_action: 'Tindakan gagal', ok: 'OK', current_sg: 'Subgraf semasa',
    chat: 'Sembang', worker_status: 'Status pekerja', save: 'Simpan', send: 'Hantar'
  },
  header: { title: 'Pekerja & Pemimpin', add_leader: '+ Tambah pemimpin', add_worker: '+ Tambah pekerja', leader: 'Pemimpin:' },
  kpis: { workers: 'PEKERJA', actifs: 'AKTIF', steps24h: 'LANGKAH (24J)', tokens24h: 'TOKEN (24J)', qualite7j: 'KUALITI (7H)' },
  toolbar: {
    process: 'Proses', current: 'Subgraf semasa', overview: 'Gambaran keseluruhan', hide_start: 'sembunyikan START', hide_end: 'sembunyikan END',
    labels: 'label', follow_sg: 'ikuti SG', mode_observe: 'Pemerhatian', mode_debug: 'Strim nyahpepijat',
    current_sg_btn: 'SG semasa', display: 'Paparan:', mode: 'Mod:'
  },
  modal: { process_title: 'Proses —' },
  status: {
    panel_title: 'Status dan metrik', running: 'Berjalan', starting: 'Bermula', failed: 'Gagal',
    completed: 'Selesai', canceled: 'Dibatalkan', idle: 'Menganggur', unknown: 'Tidak diketahui'
  },
  io: { title: 'Input/output nod', in: 'IN', out: 'OUT', error: 'RALAT' },
  config: {
    title: 'Konfigurasi proses', general: 'Umum', params: 'Parameter', docs: 'Dokumentasi',
    doc_title: 'Tajuk', doc_desc: 'Penerangan', none: 'Tiada konfigurasi tersedia'
  },
  graph: {
    error_title: 'Graf', unavailable: 'Graf tidak tersedia', aria_label: 'Graf Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'ralat paparan'
  },
  node_menu: {
    aria_actions: 'Tindakan nod', open_sg: 'Buka subgraf', run_until: 'Jalankan sehingga',
    break_add: 'Tambah titik henti', break_remove: 'Buang titik henti', inspect: 'Periksa'
  },
  control_inputs: {
    debug_label: 'Nyahpepijat:', node_id: 'ID nod', when: 'Syarat', when_always: 'sentiasa',
    when_success: 'berjaya', when_fail: 'gagal', when_retry: 'cuba semula',
    run_until: 'Jalankan sehingga', break_add: 'Tambah henti', break_remove: 'Buang henti'
  },
  chat: {
    leader_panel_title: 'Pemimpin — Sembang', placeholder: 'Mesej...', tools_trace: 'Lihat jejak alatan',
    error_history: 'Gagal memuatkan sejarah', empty_reply: '(jawapan kosong)', global: 'Sembang global',
    error_history_global: 'Gagal memuatkan sejarah global', you: 'Anda', assistant: 'LLM'
  },
  leader_global: {
    title: 'Pemimpin — Sembang global', select_label: 'Pemimpin:', select_aria: 'Pilih pemimpin',
    display: 'Nama paparan', role: 'Peranan', persona: 'Persona', persona_ph: 'Orkestrator pekerja',
    none_detected: '(tiada pemimpin)'
  },
  leader_identity_panel: {
    no_leader: 'Tiada pemimpin ditugaskan', error_read: 'Gagal membaca identiti', refresh: 'Muat semula',
    display: 'Nama paparan', role: 'Peranan', persona: 'Persona', persona_ph: 'Orkestrator pekerja',
    global_chat: 'Sembang global', leader_workers: 'Pekerja pemimpin', loading: 'Memuatkan…',
    none_attached: 'Tiada pekerja dilampirkan', error_load: 'Ralat memuatkan'
  },
  list: { title: 'Pekerja', view: 'Lihat' },
  config_editor: {
    tabs_simple: 'Mudah', tabs_json: 'JSON', beautify: 'Percantik', minify: 'Kecilkan',
    validate: 'Sahkan', json_valid: 'JSON sah', json_invalid: 'JSON tidak sah',
    complex_only_json: 'Sesetengah medan kompleks hanya boleh diedit dalam JSON'
  },
  leader_section: { edit_identity_hint: 'Sunting identiti (klik)' },
  replay: {
    title: 'Main semula (mesin masa)', load_run: 'Muat larian', play: 'Main', stop: 'Henti',
    error_runs: 'Gagal memuatkan larian', error_steps: 'Gagal memuatkan langkah',
    view_node: 'Lihat nod ini', live_announce_step: 'Memainkan langkah {idx}/{total}: {nodeId}'
  }
};
