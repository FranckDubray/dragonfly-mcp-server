export const __meta = { standalone: true, code: 'zh-Hans', flag: '🇨🇳', native: '简体中文' };
export default {
  lang: { 'zh-Hans': '简体中文' },
  header: { title: '工作者与领导', add_leader: '+ 添加领导', add_worker: '+ 添加工作者', leader: '领导：' },
  common: {
    process: '流程', details: '详情', tools_mcp: 'MCP 工具：', last_step: '最后一步',
    edit_identity: '查看/编辑身份', close: '关闭', start_observe: '开始（观测）', start_debug: '开始（调试）',
    step: '步骤', continue: '继续', stop: '停止', copy_in: '复制 IN', copy_out: '复制 OUT', copy_err: '复制错误',
    error_network: '网络错误', error_action: '操作失败', ok: '确定', current_sg: '当前子图',
    chat: '聊天', worker_status: '状态', save: '保存', send: '发送',
    status_metrics: '状态与指标', running: '运行中', starting: '启动中', failed: '失败', completed: '已完成', canceled: '已取消', idle: '空闲', unknown: '未知'
  },
  kpis: { workers: '工作者', actifs: '活跃', steps24h: '步骤（24小时）', tokens24h: '令牌（24小时）', qualite7j: '质量（7天）' },
  toolbar: {
    process: '流程', current: '当前子图', overview: '总览', hide_start: '隐藏 START', hide_end: '隐藏 END',
    labels: '标签', follow_sg: '跟随 SG', mode_observe: '观测', mode_debug: '调试流', current_sg_btn: '当前 SG',
    display: '显示：', mode: '模式：'
  },
  modal: { process_title: '流程 —' },
  status: { panel_title: '状态与指标', running: '运行中', starting: '启动中', failed: '失败', completed: '已完成', canceled: '已取消', idle: '空闲', unknown: '未知' },
  io: { title: '节点输入/输出', in: 'IN', out: 'OUT', error: '错误' },
  config: { title: '流程配置', general: '一般', params: '参数', docs: '文档', doc_title: '标题', doc_desc: '描述', none: '无可用配置' },
  graph: { error_title: '图', unavailable: '图不可用', aria_label: 'Mermaid 图', mermaid_error_prefix: 'Mermaid — ', render_error: '渲染错误' },
  node_menu: { aria_actions: '节点操作', open_sg: '打开子图', run_until: '运行至', break_add: '添加断点', break_remove: '移除断点', inspect: '检查' },
  control_inputs: { debug_label: '调试：', node_id: '节点 ID', when: '条件', when_always: '总是', when_success: '成功', when_fail: '失败', when_retry: '重试', run_until: '运行至', break_add: '添加断点', break_remove: '移除断点' },
  chat: { leader_panel_title: '领导 — 聊天', placeholder: '消息…', tools_trace: '查看工具轨迹', error_history: '加载历史失败', empty_reply: '(空回复)', global: '全局聊天', error_history_global: '加载全局历史失败', you: '你', assistant: 'LLM' },
  leader_global: { title: '领导 — 全局聊天', select_label: '领导：', select_aria: '选择一位领导', display: '显示名', role: '角色', persona: '人设', persona_ph: '工作者编排者', none_detected: '(无领导)' },
  leader_identity_panel: { no_leader: '未分配领导', error_read: '读取身份失败', refresh: '刷新', display: '显示名', role: '角色', persona: '人设', persona_ph: '工作者编排者', global_chat: '全局聊天', leader_workers: '领导的工作者', loading: '加载中…', none_attached: '无关联工作者', error_load: '加载错误' },
  list: { title: '工作者', view: '查看' },
  config_editor: { tabs_simple: '简单', tabs_json: 'JSON', beautify: '美化', minify: '压缩', validate: '校验', json_valid: '有效 JSON', json_invalid: '无效 JSON', complex_only_json: '某些复杂字段仅能在 JSON 中编辑' },
  leader_section: { edit_identity_hint: '编辑身份（点击）' },
  replay: { title: '回放（时光机）', load_run: '载入运行', play: '播放', stop: '停止', error_runs: '加载运行失败', error_steps: '加载步骤失败', view_node: '查看此节点', live_announce_step: '正在播放第 {idx}/{total} 步：{nodeId}' }
};
