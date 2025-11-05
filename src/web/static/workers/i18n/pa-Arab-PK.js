export const __meta = { standalone: true, code: 'pa-Arab-PK', flag: '🇵🇰', native: 'پنجابی (پاکستان)' };
export default {
  lang: { 'pa-Arab-PK': 'پنجابی (پاکستان)' },
  header: { title: 'مزدور اور رہنما', add_leader: '+ رہنما شامل کریں', add_worker: '+ مزدور شامل کریں', leader: 'رہنما:' },
  common: {
    process: 'عمل', details: 'تفصیلات', tools_mcp: 'MCP اوزار:', last_step: 'آخری مرحلہ',
    edit_identity: 'شناخت دیکھیں/ترتیب دیں', close: 'بند کریں', start_debug: 'شروع کریں (ڈیبگ)', start_observe: 'شروع کریں (مشاہدہ)',
    step: 'مرحلہ', continue: 'جاری رکھیں', stop: 'روکیں', copy_in: 'IN کاپی کریں', copy_out: 'OUT کاپی کریں', copy_err: 'غلطی کاپی کریں',
    error_network: 'نیٹ ورک کی غلطی', error_action: 'عمل ناکام', ok: 'ٹھیک ہے', current_sg: 'موجودہ سب گراف',
    chat: 'چیٹ', worker_status: 'حیثیت', save: 'محفوظ کریں', send: 'بھیجیں'
  },
  kpis: { workers: 'مزدور', actifs: 'فعال', steps24h: 'مراحل (24گھنٹے)', tokens24h: 'ٹوکنز (24گھنٹے)', qualite7j: 'معیار (7دن)' },
  toolbar: {
    process: 'عمل', current: 'موجودہ سب گراف', overview: 'جائزہ', hide_start: 'START چھپائیں', hide_end: 'END چھپائیں',
    labels: 'لیبل', follow_sg: 'SG کی پیروی کریں', mode_observe: 'مشاہدہ', mode_debug: 'ڈیبگ سٹریم',
    current_sg_btn: 'موجودہ SG', display: 'ڈسپلے:', mode: 'موڈ:'
  },
  modal: { process_title: 'عمل —' },
  status: {
    panel_title: 'حیثیت اور میٹرکس', running: 'چل رہا ہے', starting: 'شروع ہو رہا ہے', failed: 'ناکام',
    completed: 'مکمل', canceled: 'منسوخ', idle: 'بیکار', unknown: 'نامعلوم'
  },
  io: { title: 'نوڈ ان پٹ/آؤٹ پٹ', in: 'IN', out: 'OUT', error: 'غلطی' },
  config: {
    title: 'عمل کی ترتیب', general: 'عام', params: 'پیرامیٹرز', docs: 'دستاویزات',
    doc_title: 'عنوان', doc_desc: 'تفصیل', none: 'کوئی ترتیب دستیاب نہیں'
  },
  graph: {
    error_title: 'گراف', unavailable: 'گراف دستیاب نہیں', aria_label: 'Mermaid گراف',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'رینڈر کی غلطی'
  },
  node_menu: {
    aria_actions: 'نوڈ کی کارروائیاں', open_sg: 'سب گراف کھولیں', run_until: 'تک چلائیں',
    break_add: 'بریک پوائنٹ شامل کریں', break_remove: 'بریک پوائنٹ ہٹائیں', inspect: 'معائنہ کریں'
  },
  control_inputs: {
    debug_label: 'ڈیبگ:', node_id: 'نوڈ ID', when: 'شرط', when_always: 'ہمیشہ',
    when_success: 'کامیابی', when_fail: 'ناکامی', when_retry: 'دوبارہ کوشش',
    run_until: 'تک چلائیں', break_add: 'بریک پوائنٹ شامل کریں', break_remove: 'بریک پوائنٹ ہٹائیں'
  },
  chat: {
    leader_panel_title: 'رہنما — چیٹ', placeholder: 'پیغام...', tools_trace: 'ٹولز ٹریس دیکھیں',
    error_history: 'تاریخ لوڈ ناکام', empty_reply: '(خالی جواب)', global: 'عالمی چیٹ',
    error_history_global: 'عالمی تاریخ لوڈ ناکام', you: 'آپ', assistant: 'LLM'
  },
  leader_global: {
    title: 'رہنما — عالمی چیٹ', select_label: 'رہنما:', select_aria: 'رہنما منتخب کریں',
    display: 'ڈسپلے نام', role: 'کردار', persona: 'شخصیت', persona_ph: 'مزدوروں کا منتظم',
    none_detected: '(کوئی رہنما نہیں)'
  },
  leader_identity_panel: {
    no_leader: 'کوئی رہنما تفویض نہیں', error_read: 'شناخت پڑھنے میں ناکام', refresh: 'تازہ کریں',
    display: 'ڈسپلے نام', role: 'کردار', persona: 'شخصیت', persona_ph: 'مزدوروں کا منتظم',
    global_chat: 'عالمی چیٹ', leader_workers: 'رہنما کے مزدور', loading: 'لوڈ ہو رہا ہے…',
    none_attached: 'کوئی منسلک مزدور نہیں', error_load: 'لوڈ کی غلطی'
  },
  list: { title: 'مزدور', view: 'دیکھیں' },
  config_editor: {
    tabs_simple: 'آسان', tabs_json: 'JSON', beautify: 'خوبصورت بنائیں', minify: 'چھوٹا کریں',
    validate: 'تصدیق کریں', json_valid: 'درست JSON', json_invalid: 'غلط JSON',
    complex_only_json: 'کچھ پیچیدہ فیلڈز صرف JSON میں ترمیم کیے جا سکتے ہیں'
  },
  leader_section: { edit_identity_hint: 'شناخت ترتیب دیں (کلک کریں)' },
  replay: {
    title: 'دوبارہ چلائیں (ٹائم مشین)', load_run: 'رن لوڈ کریں', play: 'چلائیں', stop: 'روکیں',
    error_runs: 'رنز لوڈ ناکام', error_steps: 'مراحل لوڈ ناکام',
    view_node: 'یہ نوڈ دیکھیں', live_announce_step: 'مرحلہ {idx}/{total} چل رہا ہے: {nodeId}'
  }
};
