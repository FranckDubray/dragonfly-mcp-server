export const __meta = { standalone: true, code: 'ur', flag: '🇵🇰', native: 'اردو' };
export default {
  lang: { ur: 'اردو' },
  header: { title: 'کارکن اور رہنما', add_leader: '+ رہنما شامل کریں', add_worker: '+ کارکن شامل کریں', leader: 'رہنما:' },
  common: {
    process: 'عمل', details: 'تفصیلات', tools_mcp: 'MCP اوزار:', last_step: 'آخری مرحلہ',
    edit_identity: 'شناخت دیکھیں/ترمیم کریں', close: 'بند کریں', start_observe: 'آغاز (نگرانی)', start_debug: 'آغاز (ڈی بگ)',
    step: 'مرحلہ', continue: 'جاری رکھیں', stop: 'روکیں', copy_in: 'IN کاپی کریں', copy_out: 'OUT کاپی کریں', copy_err: 'خرابی کاپی کریں',
    error_network: 'نیٹ ورک خرابی', error_action: 'عمل ناکام', ok: 'OK', current_sg: 'موجودہ سب گراف',
    chat: 'چیٹ', worker_status: 'حالت', save: 'محفوظ کریں', send: 'بھیجیں'
  },
  kpis: { workers: 'کارکن', actifs: 'فعال', steps24h: 'مراحل (24گھنٹے)', tokens24h: 'ٹوکنز (24گھنٹے)', qualite7j: 'معیار (7دن)' },
  toolbar: {
    process: 'عمل', current: 'موجودہ سب گراف', overview: 'جائزہ', hide_start: 'START چھپائیں', hide_end: 'END چھپائیں',
    labels: 'لیبل', follow_sg: 'SG کی پیروی کریں', mode_observe: 'نگرانی', mode_debug: 'ڈی بگ اسٹریم', current_sg_btn: 'موجودہ SG',
    display: 'ڈسپلے:', mode: 'موڈ:'
  },
  modal: { process_title: 'عمل —' },
  status: { panel_title: 'حالت اور میٹرکس', running: 'چل رہا ہے', starting: 'شروع ہو رہا ہے', failed: 'ناکام', completed: 'مکمل', canceled: 'منسوخ', idle: 'غیرفعال', unknown: 'نامعلوم' },
  io: { title: 'نوڈ ان پٹ/آؤٹ پٹ', in: 'IN', out: 'OUT', error: 'خرابی' },
  config: { title: 'عمل کی تشکیل', general: 'عام', params: 'پیرامیٹرز', docs: 'دستاویزات', doc_title: 'عنوان', doc_desc: 'تفصیل', none: 'کوئی تشکیل دستیاب نہیں' },
  graph: { error_title: 'گراف', unavailable: 'گراف دستیاب نہیں', aria_label: 'Mermaid گراف', mermaid_error_prefix: 'Mermaid — ', render_error: 'رینڈر خرابی' },
  node_menu: { aria_actions: 'نوڈ اعمال', open_sg: 'سب گراف کھولیں', run_until: 'تک چلائیں', break_add: 'بریک پوائنٹ شامل کریں', break_remove: 'بریک پوائنٹ ہٹائیں', inspect: 'جانچ' },
  control_inputs: { debug_label: 'ڈی بگ:', node_id: 'نوڈ ID', when: 'شرط', when_always: 'ہمیشہ', when_success: 'کامیابی', when_fail: 'ناکامی', when_retry: 'دوبارہ کوشش', run_until: 'تک چلائیں', break_add: 'بریک پوائنٹ شامل کریں', break_remove: 'بریک پوائنٹ ہٹائیں' },
  chat: { leader_panel_title: 'رہنما — چیٹ', placeholder: 'پیغام...', tools_trace: 'اوزار ٹریس دیکھیں', error_history: 'تاریخ لوڈ کرنے میں ناکام', empty_reply: '(خالی جواب)', global: 'گلوبل چیٹ', error_history_global: 'گلوبل تاریخ لوڈ کرنے میں ناکام', you: 'آپ', assistant: 'LLM' },
  leader_global: { title: 'رہنما — گلوبل چیٹ', select_label: 'رہنما:', select_aria: 'ایک رہنما منتخب کریں', display: 'نمایشی نام', role: 'کردار', persona: 'پرسونا', persona_ph: 'ورکرز آرکیسٹریٹر', none_detected: '(کوئی رہنما نہیں)' },
  leader_identity_panel: { no_leader: 'کوئی رہنما متعین نہیں', error_read: 'شناخت پڑھنے میں ناکام', refresh: 'ریفریش', display: 'نمایشی نام', role: 'کردار', persona: 'پرسونا', persona_ph: 'ورکرز آرکیسٹریٹر', global_chat: 'گلوبل چیٹ', leader_workers: 'رہنما کے ورکرز', loading: 'لوڈ ہو رہا ہے…', none_attached: 'کوئی منسلک ورکر نہیں', error_load: 'لوڈ خرابی' },
  list: { title: 'کارکن', view: 'دیکھیں' },
  config_editor: { tabs_simple: 'سادہ', tabs_json: 'JSON', beautify: 'فارمیٹ', minify: 'مختصر کریں', validate: 'تصدیق کریں', json_valid: 'درست JSON', json_invalid: 'غلط JSON', complex_only_json: 'کچھ پیچیدہ فیلڈز صرف JSON میں قابل تدوین ہیں' },
  leader_section: { edit_identity_hint: 'شناخت ترمیم کریں (کلک)' },
  replay: { title: 'ری پلے (ٹائم مشین)', load_run: 'رن لوڈ کریں', play: 'چلائیں', stop: 'روکیں', error_runs: 'رن لوڈ کرنے میں ناکام', error_steps: 'مراحل لوڈ کرنے میں ناکام', view_node: 'یہ نوڈ دیکھیں', live_announce_step: 'مرحلہ {idx}/{total} چل رہا ہے: {nodeId}' }
};
