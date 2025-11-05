export const __meta = { standalone: true, code: 'my', flag: '🇲🇲', native: 'မြန်မာ' };
export default {
  lang: { my: 'မြန်မာ' },
  header: { title: 'လုပ်သားများနှင့် ခေါင်းဆောင်များ', add_leader: '+ ခေါင်းဆောင်ထပ်ထည့်ရန်', add_worker: '+ လုပ်သားထည့်ရန်', leader: 'ခေါင်းဆောင်:' },
  common: {
    process: 'လုပ်ငန်းစဉ်', details: 'အသေးစိတ်', tools_mcp: 'MCP ကိရိယာများ:', last_step: 'နောက်ဆုံးအဆင့်',
    edit_identity: 'အထောက်အထားကြည့်/ပြင်', close: 'ပိတ်', start_debug: 'စတင် (ပြသနာရှာ)', start_observe: 'စတင် (ကြည့်ရှု)',
    step: 'အဆင့်', continue: 'ဆက်လုပ်', stop: 'ရပ်', copy_in: 'IN ကူးယူ', copy_out: 'OUT ကူးယူ', copy_err: 'အမှားကူးယူ',
    error_network: 'ကွန်ရက်အမှား', error_action: 'လုပ်ဆောင်မှုမအောင်မြင်', ok: 'အိုကေ', current_sg: 'လက်ရှိ subgraph',
    chat: 'စကားပြော', worker_status: 'အခြေအနေ', save: 'သိမ်းဆည်း', send: 'ပို့'
  },
  kpis: { workers: 'လုပ်သားများ', actifs: 'တက်ကြွ', steps24h: 'အဆင့်များ (၂၄နာရီ)', tokens24h: 'တိုကင်များ (၂၄နာရီ)', qualite7j: 'အရည်အသွေး (၇ရက်)' },
  toolbar: {
    process: 'လုပ်ငန်းစဉ်', current: 'လက်ရှိ subgraph', overview: 'အနှစ်ချုပ်', hide_start: 'START ဖျောက်', hide_end: 'END ဖျောက်',
    labels: 'အမည်များ', follow_sg: 'SG လိုက်', mode_observe: 'ကြည့်ရှု', mode_debug: 'ပြသနာရှာစီး',
    current_sg_btn: 'လက်ရှိ SG', display: 'ပြသမှု:', mode: 'မုဒ်:'
  },
  modal: { process_title: 'လုပ်ငန်းစဉ် —' },
  status: {
    panel_title: 'အခြေအနေနှင့် တိုင်းတာမှုများ', running: 'လုပ်ဆောင်နေ', starting: 'စတင်နေ', failed: 'မအောင်မြင်',
    completed: 'ပြီးဆုံး', canceled: 'ဖျက်သိမ်း', idle: 'ငြိမ်နေ', unknown: 'မသိ'
  },
  io: { title: 'ကျောက်ဆူး input/output', in: 'IN', out: 'OUT', error: 'အမှား' },
  config: {
    title: 'လုပ်ငန်းစဉ်စီစဉ်မှု', general: 'ယေဘုယျ', params: 'ပါရာမီတာများ', docs: 'စာရွက်စာတမ်း',
    doc_title: 'ခေါင်းစဉ်', doc_desc: 'ဖော်ပြချက်', none: 'စီစဉ်မှုမရှိ'
  },
  graph: {
    error_title: 'ဂရပ်', unavailable: 'ဂရပ်မရရှိနိုင်', aria_label: 'Mermaid ဂရပ်',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'ပြသမှုအမှား'
  },
  node_menu: {
    aria_actions: 'ကျောက်ဆူးလုပ်ဆောင်ချက်များ', open_sg: 'Subgraph ဖွင့်', run_until: 'အထိလုပ်',
    break_add: 'Breakpoint ထည့်', break_remove: 'Breakpoint ဖယ်', inspect: 'စစ်ဆေး'
  },
  control_inputs: {
    debug_label: 'ပြသနာရှာ:', node_id: 'ကျောက်ဆူး ID', when: 'အခြေအနေ', when_always: 'အမြဲ',
    when_success: 'အောင်မြင်', when_fail: 'မအောင်မြင်', when_retry: 'ထပ်ကြိုး',
    run_until: 'အထိလုပ်', break_add: 'Breakpoint ထည့်', break_remove: 'Breakpoint ဖယ်'
  },
  chat: {
    leader_panel_title: 'ခေါင်းဆောင် — စကားပြော', placeholder: 'မက်ဆေ့ခ်ျ...', tools_trace: 'ကိရိယာလမ်းကြောင်းကြည့်',
    error_history: 'သမိုင်းတင်မှုမအောင်မြင်', empty_reply: '(အလွတ်ပြန်)', global: 'ကမ္ဘာလုံးဆိုင်ရာစကားပြော',
    error_history_global: 'ကမ္ဘာလုံးဆိုင်ရာသမိုင်းတင်မှုမအောင်မြင်', you: 'သင်', assistant: 'LLM'
  },
  leader_global: {
    title: 'ခေါင်းဆောင် — ကမ္ဘာလုံးဆိုင်ရာစကားပြော', select_label: 'ခေါင်းဆောင်:', select_aria: 'ခေါင်းဆောင်ရွေး',
    display: 'ပြသမည့်နာမည်', role: 'အခန်းကဏ္ဍ', persona: 'ကိုယ်ရည်', persona_ph: 'လုပ်သားစီမံသူ',
    none_detected: '(ခေါင်းဆောင်မရှိ)'
  },
  leader_identity_panel: {
    no_leader: 'ခေါင်းဆောင်မတာဝန်ပေး', error_read: 'အထောက်အထားဖတ်မှုမအောင်မြင်', refresh: 'ပြန်လည်တင်',
    display: 'ပြသမည့်နာမည်', role: 'အခန်းကဏ္ဍ', persona: 'ကိုယ်ရည်', persona_ph: 'လုပ်သားစီမံသူ',
    global_chat: 'ကမ္ဘာလုံးဆိုင်ရာစကားပြော', leader_workers: 'ခေါင်းဆောင်၏လုပ်သားများ', loading: 'တင်နေ…',
    none_attached: 'ပူးတွဲလုပ်သားမရှိ', error_load: 'တင်မှုအမှား'
  },
  list: { title: 'လုပ်သားများ', view: 'ကြည့်' },
  config_editor: {
    tabs_simple: 'ရိုးရှင်း', tabs_json: 'JSON', beautify: 'လှပအောင်လုပ်', minify: 'သေးအောင်လုပ်',
    validate: 'အတည်ပြု', json_valid: 'မှန်ကန် JSON', json_invalid: 'မမှန် JSON',
    complex_only_json: 'အချို့ရှုပ်ထွေးသောအကွက်များကို JSON တွင်သာပြင်နိုင်'
  },
  leader_section: { edit_identity_hint: 'အထောက်အထားပြင် (နှိပ်)' },
  replay: {
    title: 'ပြန်လည်ဖွင့် (အချိန်စက်)', load_run: 'လုပ်ငန်းတင်', play: 'ဖွင့်', stop: 'ရပ်',
    error_runs: 'လုပ်ငန်းများတင်မှုမအောင်မြင်', error_steps: 'အဆင့်များတင်မှုမအောင်မြင်',
    view_node: 'ဒီကျောက်ဆူးကြည့်', live_announce_step: 'အဆင့် {idx}/{total} ဖွင့်နေ: {nodeId}'
  }
};
