export const __meta = { standalone: true, code: 'ko', flag: '🇰🇷', native: '한국어' };
export default {
  lang: { ko: '한국어' },
  header: { title: '근로자 & 리더', add_leader: '+ 리더 추가', add_worker: '+ 근로자 추가', leader: '리더:' },
  common: {
    process: '프로세스', details: '세부정보', tools_mcp: 'MCP 도구:', last_step: '마지막 단계',
    edit_identity: '신원 보기/편집', close: '닫기', start_observe: '시작(관찰)', start_debug: '시작(디버그)',
    step: '단계', continue: '계속', stop: '중지', copy_in: 'IN 복사', copy_out: 'OUT 복사', copy_err: '오류 복사',
    error_network: '네트워크 오류', error_action: '작업 실패', ok: '확인', current_sg: '현재 서브그래프',
    chat: '채팅', worker_status: '상태', save: '저장', send: '보내기',
    status_metrics: '상태 및 지표', running: '실행 중', starting: '시작 중', failed: '실패', completed: '완료됨', canceled: '취소됨', idle: '대기 중', unknown: '알 수 없음'
  },
  kpis: { workers: '근로자', actifs: '활성', steps24h: '단계 (24시간)', tokens24h: '토큰 (24시간)', qualite7j: '품질 (7일)' },
  toolbar: {
    process: '프로세스', current: '현재 서브그래프', overview: '개요', hide_start: 'START 숨기기', hide_end: 'END 숨기기',
    labels: '레이블', follow_sg: 'SG 따라가기', mode_observe: '관찰', mode_debug: '디버그 스트림', current_sg_btn: '현재 SG',
    display: '표시:', mode: '모드:'
  },
  modal: { process_title: '프로세스 —' },
  status: { panel_title: '상태 및 지표', running: '실행 중', starting: '시작 중', failed: '실패', completed: '완료됨', canceled: '취소됨', idle: '대기 중', unknown: '알 수 없음' },
  io: { title: '노드 입출력', in: 'IN', out: 'OUT', error: '오류' },
  config: { title: '프로세스 구성', general: '일반', params: '매개변수', docs: '문서', doc_title: '제목', doc_desc: '설명', none: '사용 가능한 구성 없음' },
  graph: { error_title: '그래프', unavailable: '그래프를 사용할 수 없음', aria_label: 'Mermaid 그래프', mermaid_error_prefix: 'Mermaid — ', render_error: '렌더링 오류' },
  node_menu: { aria_actions: '노드 작업', open_sg: '서브그래프 열기', run_until: '까지 실행', break_add: '중단점 추가', break_remove: '중단점 제거', inspect: '검사' },
  control_inputs: { debug_label: '디버그:', node_id: '노드 ID', when: '조건', when_always: '항상', when_success: '성공', when_fail: '실패', when_retry: '재시도', run_until: '까지 실행', break_add: '중단점 추가', break_remove: '중단점 제거' },
  chat: { leader_panel_title: '리더 — 채팅', placeholder: '메시지...', tools_trace: '도구 트레이스 보기', error_history: '기록을 불러오지 못했습니다', empty_reply: '(빈 응답)', global: '글로벌 채팅', error_history_global: '글로벌 기록을 불러오지 못했습니다', you: '당신', assistant: 'LLM' },
  leader_global: { title: '리더 — 글로벌 채팅', select_label: '리더:', select_aria: '리더 선택', display: '표시 이름', role: '역할', persona: '페르소나', persona_ph: '워커 오케스트레이터', none_detected: '(리더 없음)' },
  leader_identity_panel: { no_leader: '리더가 지정되지 않았습니다', error_read: '신원 읽기에 실패했습니다', refresh: '새로고침', display: '표시 이름', role: '역할', persona: '페르소나', persona_ph: '워커 오케스트레이터', global_chat: '글로벌 채팅', leader_workers: '리더의 근로자', loading: '불러오는 중…', none_attached: '연결된 근로자 없음', error_load: '불러오기 오류' },
  list: { title: '근로자', view: '보기' },
  config_editor: { tabs_simple: '간단', tabs_json: 'JSON', beautify: '서식', minify: '최소화', validate: '검증', json_valid: '유효한 JSON', json_invalid: '유효하지 않은 JSON', complex_only_json: '일부 복잡한 필드는 JSON에서만 편집 가능합니다' },
  leader_section: { edit_identity_hint: '신원 편집(클릭)' },
  replay: { title: '재생(타임 머신)', load_run: '실행 불러오기', play: '재생', stop: '중지', error_runs: '실행을 불러오지 못했습니다', error_steps: '단계를 불러오지 못했습니다', view_node: '이 노드 보기', live_announce_step: '단계 {idx}/{total} 재생 중: {nodeId}' }
};
