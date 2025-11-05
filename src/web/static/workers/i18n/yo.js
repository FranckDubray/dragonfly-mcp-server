export const __meta = { standalone: true, code: 'yo', flag: '🇳🇬', native: 'Yorùbá' };
export default {
  lang: { yo: 'Yorùbá' },
  common: {
    process: 'Ilana', details: 'Àwọn àlàyé', tools_mcp: 'Awọn irinṣẹ MCP:', last_step: 'Igbesẹ to kẹhin',
    edit_identity: 'Wo/ṣatunkọ idanimo', close: 'Pa', start_debug: 'Bẹrẹ (ìtúnṣe aṣiṣe)', start_observe: 'Bẹrẹ (bọjúto)',
    step: 'Igbesẹ', continue: 'Tẹ̀síwájú', stop: 'Dákẹ́', copy_in: 'Daakọ IN', copy_out: 'Daakọ OUT', copy_err: 'Daakọ aṣiṣe',
    error_network: 'Aṣiṣe nẹtiwọki', error_action: 'Iṣe kuna', ok: 'O dara', current_sg: 'Subgraf lọwọlọwọ',
    chat: 'Ọrọ̀', worker_status: 'Ipo oṣiṣẹ', save: 'Fipamọ́', send: 'Firanṣẹ'
  },
  header: { title: 'Oṣiṣẹ & Àwọn Olórí', add_leader: '+ Fi olórí kun', add_worker: '+ Fi oṣiṣẹ kun', leader: 'Olórí:' },
  kpis: { workers: 'OṢIṢẸ', actifs: 'TÍ N ṢIṢ', steps24h: 'IGBESẸ (24W)', tokens24h: 'TOKENS (24W)', qualite7j: 'DIDARA (7Ọ)' },
  toolbar: {
    process: 'Ilana', current: 'Subgraf lọwọlọwọ', overview: 'Àkópọ́', hide_start: 'fi START pamọ́', hide_end: 'fi END pamọ́',
    labels: 'àwọn àmì', follow_sg: 'tẹ̀lé SG', mode_observe: 'Bọjúto', mode_debug: 'Ṣiṣan aṣiṣe',
    current_sg_btn: 'SG lọwọlọwọ', display: 'Ifihan:', mode: 'Ọna:'
  },
  modal: { process_title: 'Ilana —' },
  status: {
    panel_title: 'Ipo & àwọn òṣùwọ̀n', running: 'N ṣiṣẹ', starting: 'N bẹrẹ', failed: 'O kuna',
    completed: 'O pari', canceled: 'A fagilee', idle: 'O wa laisẹ', unknown: 'Aimọ'
  },
  io: { title: 'Àwọn ohun elo/Awọn abajade node', in: 'IN', out: 'OUT', error: 'AṢIṢE' },
  config: {
    title: 'Eto iṣeto ilana', general: 'Gbogbogbo', params: 'Awọn paramita', docs: 'Ìwé ìtòsọ́nà',
    doc_title: 'Akọle', doc_desc: 'Apejuwe', none: 'Ko si eto iṣeto'
  },
  graph: {
    error_title: 'Aworan', unavailable: 'Aworan ko si', aria_label: 'Aworan Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'aṣiṣe ifihan'
  },
  node_menu: {
    aria_actions: 'Awọn iṣe node', open_sg: 'Ṣii subgraph', run_until: 'Ṣiṣẹ titi di',
    break_add: 'Fi ibi idaduro kun', break_remove: 'Yọ ibi idaduro kuro', inspect: 'Ṣayẹwo'
  },
  control_inputs: {
    debug_label: 'Ìtúnṣe:', node_id: 'ID node', when: 'Nigba', when_always: 'nigbagbogbo',
    when_success: 'ti o ba ṣaṣeyọri', when_fail: 'ti o ba kuna', when_retry: 'ti o ba tun gbiyanju',
    run_until: 'Ṣiṣẹ titi di', break_add: 'Fi idaduro kun', break_remove: 'Yọ idaduro kuro'
  },
  chat: {
    leader_panel_title: 'Olórí — Ọrọ̀', placeholder: 'Ifiranṣẹ...', tools_trace: 'Wo àwọn àmì irinṣẹ',
    error_history: 'Itan ko ṣiṣẹ', empty_reply: '(esi ofo)', global: 'Ọrọ̀ agbaye',
    error_history_global: 'Itan agbaye ko ṣiṣẹ', you: 'Iwọ', assistant: 'LLM'
  },
  leader_global: {
    title: 'Olórí — Ọrọ̀ agbaye', select_label: 'Olórí:', select_aria: 'Yan olórí kan',
    display: 'Orukọ ifihan', role: 'Ipa', persona: 'Ẹni-ara', persona_ph: 'Oludari awọn oṣiṣẹ',
    none_detected: '(ko si olórí)'
  },
  leader_identity_panel: {
    no_leader: 'Ko si olórí ti a yan', error_read: 'Idanimo ko ka', refresh: 'Tunṣe',
    display: 'Orukọ ifihan', role: 'Ipa', persona: 'Ẹni-ara', persona_ph: 'Oludari awọn oṣiṣẹ',
    global_chat: 'Ọrọ̀ agbaye', leader_workers: 'Awọn oṣiṣẹ olórí', loading: 'N ṣe ikojọpọ...',
    none_attached: 'Ko si oṣiṣẹ to so mọ́', error_load: 'Àṣìṣe ikojọpọ'
  },
  list: { title: 'Oṣiṣẹ', view: 'Wo' },
  config_editor: {
    tabs_simple: 'Rọrun', tabs_json: 'JSON', beautify: 'Fún àṣà', minify: 'Fún kíkún',
    validate: 'Fọwọsi', json_valid: 'JSON tó wúlò', json_invalid: 'JSON tí kò tọ́',
    complex_only_json: 'Diẹ ninu awọn aaye idiju le ṣe atunṣe ni JSON nikan'
  },
  leader_section: { edit_identity_hint: 'Ṣatunkọ idanimo (tẹ)' },
  replay: {
    title: 'Atẹjáde àtúnṣe (ẹ̀rọ àkókò)', load_run: 'Gba iṣẹ ti kọja', play: 'Mu', stop: 'Dákẹ́',
    error_runs: 'Iṣẹ ti kọja ko ṣiṣẹ', error_steps: 'Igbesẹ ko ṣiṣẹ',
    view_node: 'Wo node yii', live_announce_step: 'N mu igbesẹ {idx}/{total}: {nodeId}'
  }
};
