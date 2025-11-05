export const __meta = { standalone: true, code: 'yue-Hant-HK', flag: '🇭🇰', native: '粵語（香港）' };
export default {
  lang: { 'yue-Hant-HK': '粵語（香港）' },
  header: { title: '員工與領導', add_leader: '+ 新增領導', add_worker: '+ 新增員工', leader: '領導：' },
  common: {
    process: '流程', details: '詳情', tools_mcp: 'MCP 工具:', last_step: '最後一步',
    edit_identity: '睇/改身份', close: '關閉', start_debug: '開始（除錯）', start_observe: '開始（觀察）',
    step: '步驟', continue: '繼續', stop: '停止', copy_in: '複製 IN', copy_out: '複製 OUT', copy_err: '複製錯誤',
    error_network: '網絡錯誤', error_action: '操作失敗', ok: '好', current_sg: '當前子圖',
    chat: '傾計', worker_status: '狀態', save: '儲存', send: '發送'
  },
  kpis: { workers: '員工', actifs: '活躍', steps24h: '步驟 (24小時)', tokens24h: 'Token (24小時)', qualite7j: '質量 (7日)' },
  toolbar: {
    process: '流程', current: '當前子圖', overview: '總覽', hide_start: '隱藏 START', hide_end: '隱藏 END',
    labels: '標籤', follow_sg: '跟住 SG', mode_observe: '觀察', mode_debug: '除錯串流',
    current_sg_btn: '當前 SG', display: '顯示:', mode: '模式:'
  },
  modal: { process_title: '流程 —' },
  status: {
    panel_title: '狀態同指標', running: '運行緊', starting: '啟動緊', failed: '失敗',
    completed: '完成', canceled: '取消', idle: '閒置', unknown: '未知'
  },
  io: { title: '節點輸入/輸出', in: 'IN', out: 'OUT', error: '錯誤' },
  config: {
    title: '流程配置', general: '一般', params: '參數', docs: '文檔',
    doc_title: '標題', doc_desc: '描述', none: '無可用配置'
  },
  graph: {
    error_title: '圖表', unavailable: '圖表唔可用', aria_label: 'Mermaid 圖表',
    mermaid_error_prefix: 'Mermaid — ', render_error: '渲染錯誤'
  },
  node_menu: {
    aria_actions: '節點操作', open_sg: '打開子圖', run_until: '運行到',
    break_add: '加斷點', break_remove: '刪除斷點', inspect: '檢查'
  },
  control_inputs: {
    debug_label: '除錯:', node_id: '節點 ID', when: '條件', when_always: '總係',
    when_success: '成功', when_fail: '失敗', when_retry: '重試',
    run_until: '運行到', break_add: '加斷點', break_remove: '刪除斷點'
  },
  chat: {
    leader_panel_title: '領導 — 傾計', placeholder: '訊息...', tools_trace: '睇工具追蹤',
    error_history: '載入歷史失敗', empty_reply: '(空回覆)', global: '全球傾計',
    error_history_global: '載入全球歷史失敗', you: '你', assistant: 'LLM'
  },
  leader_global: {
    title: '領導 — 全球傾計', select_label: '領導:', select_aria: '選擇領導',
    display: '顯示名稱', role: '角色', persona: '人格', persona_ph: '員工協調者',
    none_detected: '(無領導)'
  },
  leader_identity_panel: {
    no_leader: '無指派領導', error_read: '讀取身份失敗', refresh: '重新整理',
    display: '顯示名稱', role: '角色', persona: '人格', persona_ph: '員工協調者',
    global_chat: '全球傾計', leader_workers: '領導嘅員工', loading: '載入緊…',
    none_attached: '無附加員工', error_load: '載入錯誤'
  },
  list: { title: '員工', view: '查看' },
  config_editor: {
    tabs_simple: '簡單', tabs_json: 'JSON', beautify: '美化', minify: '精簡',
    validate: '驗證', json_valid: '有效 JSON', json_invalid: '無效 JSON',
    complex_only_json: '某啲複雜欄位只可以喺 JSON 入面編輯'
  },
  leader_section: { edit_identity_hint: '編輯身份 (撳)' },
  replay: {
    title: '重播 (時光機)', load_run: '載入運行', play: '播放', stop: '停止',
    error_runs: '載入運行失敗', error_steps: '載入步驟失敗',
    view_node: '睇呢個節點', live_announce_step: '播放緊步驟 {idx}/{total}: {nodeId}'
  }
};
