export const __meta = { standalone: true, code: 'ja', flag: '🇯🇵', native: '日本語' };
export default {
  lang: { ja: '日本語' },
  header: { title: 'ワーカーとリーダー', add_leader: '+ リーダーを追加', add_worker: '+ ワーカーを追加', leader: 'リーダー:' },
  common: {
    process: 'プロセス', details: '詳細', tools_mcp: 'MCP ツール:', last_step: '最後のステップ',
    edit_identity: 'アイデンティティを表示/編集', close: '閉じる', start_observe: '開始（監視）', start_debug: '開始（デバッグ）',
    step: 'ステップ', continue: '続行', stop: '停止', copy_in: 'IN をコピー', copy_out: 'OUT をコピー', copy_err: 'エラーをコピー',
    error_network: 'ネットワークエラー', error_action: '操作に失敗', ok: 'OK', current_sg: '現在のサブグラフ',
    chat: 'チャット', worker_status: 'ステータス', save: '保存', send: '送信'
  },
  kpis: { workers: 'ワーカー', actifs: 'アクティブ', steps24h: 'ステップ（24H）', tokens24h: 'トークン（24H）', qualite7j: '品質（7日）' },
  toolbar: {
    process: 'プロセス', current: '現在のサブグラフ', overview: '概要', hide_start: 'START を隠す', hide_end: 'END を隠す',
    labels: 'ラベル', follow_sg: 'SG を追従', mode_observe: '監視', mode_debug: 'デバッグ・ストリーム', current_sg_btn: '現在の SG',
    display: '表示:', mode: 'モード:'
  },
  modal: { process_title: 'プロセス —' },
  status: { panel_title: 'ステータスとメトリクス', running: '稼働中', starting: '起動中', failed: '失敗', completed: '完了', canceled: 'キャンセル', idle: '待機', unknown: '不明' },
  io: { title: 'ノード入出力', in: 'IN', out: 'OUT', error: 'エラー' },
  config: { title: 'プロセス設定', general: '一般', params: 'パラメータ', docs: 'ドキュメント', doc_title: 'タイトル', doc_desc: '説明', none: '利用可能な設定はありません' },
  graph: { error_title: 'グラフ', unavailable: 'グラフは利用できません', aria_label: 'Mermaid グラフ', mermaid_error_prefix: 'Mermaid — ', render_error: 'レンダーエラー' },
  node_menu: { aria_actions: 'ノードアクション', open_sg: 'サブグラフを開く', run_until: 'まで実行', break_add: 'ブレークポイントを追加', break_remove: 'ブレークポイントを削除', inspect: '検査' },
  control_inputs: { debug_label: 'デバッグ:', node_id: 'ノード ID', when: '条件', when_always: '常に', when_success: '成功', when_fail: '失敗', when_retry: '再試行', run_until: 'まで実行', break_add: 'ブレークポイントを追加', break_remove: 'ブレークポイントを削除' },
  chat: { leader_panel_title: 'リーダー — チャット', placeholder: 'メッセージ...', tools_trace: 'ツールのトレースを表示', error_history: '履歴の読み込みに失敗しました', empty_reply: '(空の返信)', global: 'グローバルチャット', error_history_global: 'グローバル履歴の読み込みに失敗しました', you: 'あなた', assistant: 'LLM' },
  leader_global: { title: 'リーダー — グローバルチャット', select_label: 'リーダー:', select_aria: 'リーダーを選択', display: '表示名', role: '役割', persona: 'ペルソナ', persona_ph: 'ワーカーのオーケストレーター', none_detected: '(リーダーなし)' },
  leader_identity_panel: { no_leader: 'リーダーは割り当てられていません', error_read: 'アイデンティティの読み込みに失敗しました', refresh: '更新', display: '表示名', role: '役割', persona: 'ペルソナ', persona_ph: 'ワーカーのオーケストレーター', global_chat: 'グローバルチャット', leader_workers: 'リーダーのワーカー', loading: '読み込み中…', none_attached: '関連付けられたワーカーなし', error_load: '読み込みエラー' },
  list: { title: 'ワーカー', view: '表示' },
  config_editor: { tabs_simple: 'シンプル', tabs_json: 'JSON', beautify: '整形', minify: '最小化', validate: '検証', json_valid: '有効な JSON', json_invalid: '無効な JSON', complex_only_json: '一部の複雑なフィールドは JSON でのみ編集可能です' },
  leader_section: { edit_identity_hint: 'アイデンティティを編集（クリック）' },
  replay: { title: 'リプレイ（タイムマシン）', load_run: '実行を読み込む', play: '再生', stop: '停止', error_runs: '実行の読み込みに失敗しました', error_steps: 'ステップの読み込みに失敗しました', view_node: 'このノードを表示', live_announce_step: 'ステップ {idx}/{total} を再生中: {nodeId}' }
};
