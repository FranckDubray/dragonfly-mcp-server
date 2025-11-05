export const __meta = { standalone: true, code: 'uz-Latn', flag: '🇺🇿', native: 'Oʻzbekcha' };
export default {
  lang: { 'uz-Latn': 'Oʻzbekcha' },
  header: { title: 'Xodimlar va yetakchilar', add_leader: '+ Yetakchi qoʻshish', add_worker: '+ Xodim qoʻshish', leader: 'Yetakchi:' },
  common: {
    process: 'Jarayon', details: 'Tafsilotlar', tools_mcp: 'MCP vositalari:', last_step: 'Oxirgi qadam',
    edit_identity: 'Identifikatsiyani koʻrish/tahrirlash', close: 'Yopish', start_debug: 'Boshlash (debug)', start_observe: 'Boshlash (kuzatish)',
    step: 'Qadam', continue: 'Davom etish', stop: 'Toʻxtatish', copy_in: 'IN nusxalash', copy_out: 'OUT nusxalash', copy_err: 'Xatoni nusxalash',
    error_network: 'Tarmoq xatosi', error_action: 'Amal bajarilmadi', ok: 'OK', current_sg: 'Joriy subgraf',
    chat: 'Suhbat', worker_status: 'Holat', save: 'Saqlash', send: 'Yuborish'
  },
  kpis: { workers: 'XODIMLAR', actifs: 'FAOL', steps24h: 'QADAMLAR (24S)', tokens24h: 'TOKENLAR (24S)', qualite7j: 'SIFAT (7K)' },
  toolbar: {
    process: 'Jarayon', current: 'Joriy subgraf', overview: 'Umumiy koʻrinish', hide_start: 'START yashirish', hide_end: 'END yashirish',
    labels: 'yorliqlar', follow_sg: 'SG kuzatish', mode_observe: 'Kuzatish', mode_debug: 'Debug oqimi',
    current_sg_btn: 'Joriy SG', display: 'Koʻrinish:', mode: 'Rejim:'
  },
  modal: { process_title: 'Jarayon —' },
  status: {
    panel_title: 'Holat va koʻrsatkichlar', running: 'Ishlayapti', starting: 'Boshlanmoqda', failed: 'Muvaffaqiyatsiz',
    completed: 'Tugallandi', canceled: 'Bekor qilindi', idle: 'Kutish rejimida', unknown: 'Noma'lum'
  },
  io: { title: 'Node kirish/chiqish', in: 'IN', out: 'OUT', error: 'XATO' },
  config: {
    title: 'Jarayon konfiguratsiyasi', general: 'Umumiy', params: 'Parametrlar', docs: 'Hujjatlar',
    doc_title: 'Sarlavha', doc_desc: 'Tavsif', none: 'Konfiguratsiya mavjud emas'
  },
  graph: {
    error_title: 'Grafik', unavailable: 'Grafik mavjud emas', aria_label: 'Mermaid grafik',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'render xatosi'
  },
  node_menu: {
    aria_actions: 'Node harakatlari', open_sg: 'Subgrafni ochish', run_until: 'Gacha ishlash',
    break_add: 'Toʻxtash nuqtasini qoʻshish', break_remove: 'Toʻxtash nuqtasini olib tashlash', inspect: 'Tekshirish'
  },
  control_inputs: {
    debug_label: 'Debug:', node_id: 'Node ID', when: 'Shart', when_always: 'doim',
    when_success: 'muvaffaqiyat', when_fail: 'muvaffaqiyatsizlik', when_retry: 'qayta urinish',
    run_until: 'Gacha ishlash', break_add: 'Toʻxtash nuqtasini qoʻshish', break_remove: 'Toʻxtash nuqtasini olib tashlash'
  },
  chat: {
    leader_panel_title: 'Yetakchi — Suhbat', placeholder: 'Xabar...', tools_trace: 'Vosita izlarini koʻrish',
    error_history: 'Tarixni yuklash muvaffaqiyatsiz', empty_reply: '(boʻsh javob)', global: 'Global suhbat',
    error_history_global: 'Global tarixni yuklash muvaffaqiyatsiz', you: 'Siz', assistant: 'LLM'
  },
  leader_global: {
    title: 'Yetakchi — Global suhbat', select_label: 'Yetakchi:', select_aria: 'Yetakchini tanlash',
    display: 'Koʻrinish nomi', role: 'Rol', persona: 'Shaxs', persona_ph: 'Xodimlar orkestratori',
    none_detected: '(yetakchi yoʻq)'
  },
  leader_identity_panel: {
    no_leader: 'Yetakchi tayinlanmagan', error_read: 'Identifikatsiyani oʻqib boʻlmadi', refresh: 'Yangilash',
    display: 'Koʻrinish nomi', role: 'Rol', persona: 'Shaxs', persona_ph: 'Xodimlar orkestratori',
    global_chat: 'Global suhbat', leader_workers: 'Yetakchi xodimlari', loading: 'Yuklanmoqda…',
    none_attached: 'Biriktirilgan xodim yoʻq', error_load: 'Yuklash xatosi'
  },
  list: { title: 'Xodimlar', view: 'Koʻrish' },
  config_editor: {
    tabs_simple: 'Oddiy', tabs_json: 'JSON', beautify: 'Chiroyli qilish', minify: 'Kichraytirish',
    validate: 'Tekshirish', json_valid: 'Toʻgʻri JSON', json_invalid: 'Xato JSON',
    complex_only_json: 'Baʼzi murakkab maydonlar faqat JSON da tahrirlanishi mumkin'
  },
  leader_section: { edit_identity_hint: 'Identifikatsiyani tahrirlash (bosing)' },
  replay: {
    title: 'Qayta ijro (vaqt mashinasi)', load_run: 'Ishlashni yuklash', play: 'Ijro', stop: 'Toʻxtatish',
    error_runs: 'Ishlashlarni yuklash muvaffaqiyatsiz', error_steps: 'Qadamlarni yuklash muvaffaqiyatsiz',
    view_node: 'Ushbu nodeni koʻrish', live_announce_step: 'Qadam {idx}/{total} ijro etilmoqda: {nodeId}'
  }
};
