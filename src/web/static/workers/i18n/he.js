export const __meta = { standalone: true, code: 'he', flag: '🇮🇱', native: 'עברית' };
export default {
  lang: { he: 'עברית' },
  common: {
    process: 'תהליך', details: 'פרטים', tools_mcp: 'כלי MCP:', last_step: 'שלב אחרון',
    edit_identity: 'הצג/ערוך זהות', close: 'סגור', start_debug: 'התחל (ניפוי)', start_observe: 'התחל (תצפית)',
    step: 'שלב', continue: 'המשך', stop: 'עצור', copy_in: 'העתק IN', copy_out: 'העתק OUT', copy_err: 'העתק שגיאה',
    error_network: 'שגיאת רשת', error_action: 'הפעולה נכשלה', ok: 'אישור', current_sg: 'תת-גרף נוכחי',
    chat: 'צ׳אט', worker_status: 'סטטוס עובד', save: 'שמור', send: 'שלח'
  },
  header: { title: 'עובדים ומנהיגים', add_leader: '+ הוסף מנהיג', add_worker: '+ הוסף עובד', leader: 'מנהיג:' },
  kpis: { workers: 'עובדים', actifs: 'פעילים', steps24h: 'צעדים (24 שעות)', tokens24h: 'טוקנים (24 שעות)', qualite7j: 'איכות (7 ימים)' },
  toolbar: {
    process: 'תהליך', current: 'תת-גרף נוכחי', overview: 'סקירה', hide_start: 'הסתר START', hide_end: 'הסתר END',
    labels: 'תוויות', follow_sg: 'עקוב אחר SG', mode_observe: 'תצפית', mode_debug: 'זרם ניפוי',
    current_sg_btn: 'SG נוכחי', display: 'תצוגה:', mode: 'מצב:'
  },
  modal: { process_title: 'תהליך —' },
  status: {
    panel_title: 'סטטוס ומדדים', running: 'פועל', starting: 'מתחיל', failed: 'נכשל',
    completed: 'הושלם', canceled: 'בוטל', idle: 'לא פעיל', unknown: 'לא ידוע'
  },
  io: { title: 'כניסות/יציאות צומת', in: 'IN', out: 'OUT', error: 'שגיאה' },
  config: {
    title: 'תצורת תהליך', general: 'כללי', params: 'פרמטרים', docs: 'תיעוד',
    doc_title: 'כותרת', doc_desc: 'תיאור', none: 'אין תצורה זמינה'
  },
  graph: {
    error_title: 'גרף', unavailable: 'הגרף אינו זמין', aria_label: 'גרף Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'שגיאת עיבוד'
  },
  node_menu: {
    aria_actions: 'פעולות צומת', open_sg: 'פתח תת-גרף', run_until: 'הרץ עד',
    break_add: 'הוסף נקודת עצירה', break_remove: 'הסר נקודת עצירה', inspect: 'בדוק'
  },
  control_inputs: {
    debug_label: 'ניפוי:', node_id: 'מזהה צומת', when: 'תנאי', when_always: 'תמיד',
    when_success: 'הצלחה', when_fail: 'כשלון', when_retry: 'ניסיון חוזר',
    run_until: 'הרץ עד', break_add: 'הוסף עצירה', break_remove: 'הסר עצירה'
  },
  chat: {
    leader_panel_title: 'מנהיג — צ׳אט', placeholder: 'הודעה...', tools_trace: 'הצג עקבות כלים',
    error_history: 'טעינת היסטוריה נכשלה', empty_reply: '(תשובה ריקה)', global: 'צ׳אט גלובלי',
    error_history_global: 'טעינת היסטוריה גלובלית נכשלה', you: 'אתה', assistant: 'LLM'
  },
  leader_global: {
    title: 'מנהיג — צ׳אט גלובלי', select_label: 'מנהיג:', select_aria: 'בחר מנהיג',
    display: 'שם תצוגה', role: 'תפקיד', persona: 'פרסונה', persona_ph: 'מתאם עובדים',
    none_detected: '(אין מנהיג)'
  },
  leader_identity_panel: {
    no_leader: 'לא הוקצה מנהיג', error_read: 'קריאת זהות נכשלה', refresh: 'רענן',
    display: 'שם תצוגה', role: 'תפקיד', persona: 'פרסונה', persona_ph: 'מתאם עובדים',
    global_chat: 'צ׳אט גלובלי', leader_workers: 'עובדי המנהיג', loading: 'טוען…',
    none_attached: 'אין עובד מצורף', error_load: 'שגיאת טעינה'
  },
  list: { title: 'עובדים', view: 'הצג' },
  config_editor: {
    tabs_simple: 'פשוט', tabs_json: 'JSON', beautify: 'עיצוב', minify: 'צמצום',
    validate: 'אימות', json_valid: 'JSON תקין', json_invalid: 'JSON לא תקין',
    complex_only_json: 'שדות מורכבים מסוימים ניתנים לעריכה רק ב-JSON'
  },
  leader_section: { edit_identity_hint: 'ערוך זהות (לחץ)' },
  replay: {
    title: 'השמעה חוזרת (מכונת זמן)', load_run: 'טען הרצה', play: 'נגן', stop: 'עצור',
    error_runs: 'טעינת הרצות נכשלה', error_steps: 'טעינת צעדים נכשלה',
    view_node: 'הצג צומת זה', live_announce_step: 'מנגן צעד {idx}/{total}: {nodeId}'
  }
};
