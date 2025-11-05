export const __meta = { standalone: true, code: 'ar', flag: '🇸🇦', native: 'العربية' };
export default {
  lang: { ar: 'العربية' },
  header: { title: 'العمال والقادة', add_leader: '+ إضافة قائد', add_worker: '+ إضافة عامل', leader: 'قائد:' },
  common: {
    process: 'العملية', details: 'التفاصيل', tools_mcp: 'أدوات MCP:', last_step: 'آخر خطوة',
    edit_identity: 'عرض/تحرير الهوية', close: 'إغلاق', start_observe: 'بدء (مراقبة)', start_debug: 'بدء (تصحيح)',
    step: 'خطوة', continue: 'متابعة', stop: 'إيقاف', copy_in: 'نسخ IN', copy_out: 'نسخ OUT', copy_err: 'نسخ الخطأ',
    error_network: 'خطأ في الشبكة', error_action: 'فشلت العملية', ok: 'حسنًا', current_sg: 'المخطط الفرعي الحالي',
    chat: 'دردشة', worker_status: 'الحالة', save: 'حفظ', send: 'إرسال'
  },
  kpis: { workers: 'العمال', actifs: 'النشطون', steps24h: 'الخطوات (24س)', tokens24h: 'الرموز (24س)', qualite7j: 'الجودة (7أ)' },
  toolbar: {
    process: 'العملية', current: 'المخطط الفرعي الحالي', overview: 'نظرة عامة', hide_start: 'إخفاء START', hide_end: 'إخفاء END',
    labels: 'التسميات', follow_sg: 'اتّبع SG', mode_observe: 'مراقبة', mode_debug: 'تيار التصحيح', current_sg_btn: 'SG الحالي',
    display: 'العرض:', mode: 'الوضع:'
  },
  modal: { process_title: 'العملية —' },
  status: {
    panel_title: 'الحالة والقياسات', running: 'نشِط', starting: 'قيد البدء', failed: 'فشل', completed: 'اكتمل',
    canceled: 'أُلغي', idle: 'خامل', unknown: 'غير معروف'
  },
  io: { title: 'مدخلات/مخرجات العقدة', in: 'IN', out: 'OUT', error: 'خطأ' },
  config: {
    title: 'تهيئة العملية', general: 'عام', params: 'معلمات', docs: 'توثيق', doc_title: 'العنوان',
    doc_desc: 'الوصف', none: 'لا توجد تهيئة متاحة'
  },
  graph: {
    error_title: 'الرسم البياني', unavailable: 'الرسم البياني غير متاح', aria_label: 'رسم Mermaid', mermaid_error_prefix: 'Mermaid — ',
    render_error: 'خطأ في العرض'
  },
  node_menu: {
    aria_actions: 'إجراءات العقدة', open_sg: 'فتح المخطط الفرعي', run_until: 'تشغيل حتى', break_add: 'إضافة نقطة توقّف',
    break_remove: 'إزالة نقطة التوقّف', inspect: 'فحص'
  },
  control_inputs: {
    debug_label: 'تصحيح:', node_id: 'معرّف العقدة', when: 'شرط', when_always: 'دائمًا', when_success: 'نجاح',
    when_fail: 'فشل', when_retry: 'إعادة المحاولة', run_until: 'تشغيل حتى', break_add: 'إضافة نقطة توقّف', break_remove: 'إزالة نقطة التوقّف'
  },
  chat: {
    leader_panel_title: 'القائد — دردشة', placeholder: 'رسالة…', tools_trace: 'عرض آثار الأدوات',
    error_history: 'فشل تحميل السجل', empty_reply: '(رد فارغ)', global: 'دردشة عامة',
    error_history_global: 'فشل تحميل السجل العام', you: 'أنت', assistant: 'LLM'
  },
  leader_global: {
    title: 'القائد — الدردشة العامة', select_label: 'القائد:', select_aria: 'اختر قائدًا', display: 'اسم العرض',
    role: 'الدور', persona: 'الشخصية', persona_ph: 'منسّق العمال', none_detected: '(لا قائد)'
  },
  leader_identity_panel: {
    no_leader: 'لا يوجد قائد معيّن', error_read: 'فشل قراءة الهوية', refresh: 'تحديث', display: 'اسم العرض',
    role: 'الدور', persona: 'الشخصية', persona_ph: 'منسّق العمال', global_chat: 'الدردشة العامة',
    leader_workers: 'عمال القائد', loading: 'جارٍ التحميل…', none_attached: 'لا عامل مرتبط', error_load: 'خطأ في التحميل'
  },
  list: { title: 'العمال', view: 'عرض' },
  config_editor: {
    tabs_simple: 'بسيط', tabs_json: 'JSON', beautify: 'تنسيق', minify: 'تصغير', validate: 'تحقق',
    json_valid: 'JSON صالح', json_invalid: 'JSON غير صالح', complex_only_json: 'بعض الحقول المعقّدة قابلة للتحرير فقط في JSON'
  },
  leader_section: { edit_identity_hint: 'تحرير الهوية (انقر)' },
  replay: {
    title: 'إعادة العرض (آلة الزمن)', load_run: 'تحميل التشغيل', play: 'تشغيل', stop: 'إيقاف',
    error_runs: 'فشل تحميل التشغيل', error_steps: 'فشل تحميل الخطوات', view_node: 'عرض هذه العقدة',
    live_announce_step: 'تشغيل الخطوة {idx}/{total}: {nodeId}'
  }
};
