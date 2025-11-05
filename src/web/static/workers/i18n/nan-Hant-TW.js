export const __meta = { standalone: true, code: 'nan-Hant-TW', flag: '🇹🇼', native: '閩南語（臺灣）' };
export default {
  lang: { 'nan-Hant-TW': '閩南語（臺灣）' },
  header: { title: '作工人與頭人', add_leader: '+ 添頭人', add_worker: '+ 添作工人', leader: '頭人：' },
  common: {
    process: '流程', details: '詳細', tools_mcp: 'MCP 工具：', last_step: '上尾步',
    edit_identity: '看/改身份', close: '關', start_debug: '開始（除錯）', start_observe: '開始（觀察）',
    step: '步驟', continue: '繼續', stop: '停止', copy_in: '複製 IN', copy_out: '複製 OUT', copy_err: '複製錯誤',
    error_network: '網路錯誤', error_action: '動作失敗', ok: '好', current_sg: '當前 subgraph',
    chat: '講話', worker_status: '狀態', save: '儲存', send: '送出'
  },
  kpis: { workers: '作工人', actifs: '活跳跳', steps24h: '步數 (24點鐘)', tokens24h: 'Token (24點鐘)', qualite7j: '品質 (7工)' },
  toolbar: {
    process: '流程', current: '當前 subgraph', overview: '總覽', hide_start: '藏 START', hide_end: '藏 END',
    labels: '標籤', follow_sg: '跟 SG', mode_observe: '觀察', mode_debug: '除錯串流',
    current_sg_btn: '當前 SG', display: '顯示：', mode: '模式：'
  },
  modal: { process_title: '流程 —' },
  status: {
    panel_title: '狀態佮指標', running: '咧走', starting: '咧起', failed: '歹去',
    completed: '做好', canceled: '取消', idle: '閒閒', unknown: '毋知'
  },
  io: { title: '節點 輸入/輸出', in: 'IN', out: 'OUT', error: '錯誤' },
  config: {
    title: '流程設定', general: '一般', params: '參數', docs: '文件',
    doc_title: '標題', doc_desc: '說明', none: '無設定'
  },
  graph: {
    error_title: '圖表', unavailable: '圖表無法度', aria_label: 'Mermaid 圖表',
    mermaid_error_prefix: 'Mermaid — ', render_error: '渲染錯誤'
  },
  node_menu: {
    aria_actions: '節點動作', open_sg: '開 subgraph', run_until: '走到',
    break_add: '加中斷點', break_remove: '除中斷點', inspect: '檢查'
  },
  control_inputs: {
    debug_label: '除錯：', node_id: '節點 ID', when: '條件', when_always: '逐擺',
    when_success: '成功', when_fail: '失敗', when_retry: '閣試',
    run_until: '走到', break_add: '加中斷點', break_remove: '除中斷點'
  },
  chat: {
    leader_panel_title: '頭人 — 講話', placeholder: '訊息...', tools_trace: '看工具痕跡',
    error_history: '載入歷史失敗', empty_reply: '(空回)', global: '全球講話',
    error_history_global: '載入全球歷史失敗', you: '你', assistant: 'LLM'
  },
  leader_global: {
    title: '頭人 — 全球講話', select_label: '頭人：', select_aria: '選頭人',
    display: '顯示名', role: '角色', persona: '性格', persona_ph: '作工人協調者',
    none_detected: '(無頭人)'
  },
  leader_identity_panel: {
    no_leader: '無指派頭人', error_read: '讀身份失敗', refresh: '刷新',
    display: '顯示名', role: '角色', persona: '性格', persona_ph: '作工人協調者',
    global_chat: '全球講話', leader_workers: '頭人ê作工人', loading: '咧載…',
    none_attached: '無附帶作工人', error_load: '載入錯誤'
  },
  list: { title: '作工人', view: '看' },
  config_editor: {
    tabs_simple: '簡單', tabs_json: 'JSON', beautify: '美化', minify: '壓縮',
    validate: '驗證', json_valid: '有效 JSON', json_invalid: '無效 JSON',
    complex_only_json: '一寡複雜欄位干焦佇 JSON 內編輯'
  },
  leader_section: { edit_identity_hint: '編輯身份 (點)' },
  replay: {
    title: '重播 (時間機器)', load_run: '載入執行', play: '播放', stop: '停',
    error_runs: '載入執行失敗', error_steps: '載入步驟失敗',
    view_node: '看此節點', live_announce_step: '咧播步驟 {idx}/{total}：{nodeId}'
  }
};
