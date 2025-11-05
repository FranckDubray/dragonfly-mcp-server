export const __meta = { standalone: true, code: 'sk', flag: '🇸🇰', native: 'Slovenčina' };
export default {
  lang: { sk: 'Slovenčina' },
  common: {
    process: 'Proces', details: 'Podrobnosti', tools_mcp: 'MCP nástroje:', last_step: 'Posledný krok',
    edit_identity: 'Zobraziť/upraviť identitu', close: 'Zavrieť', start_debug: 'Spustiť (ladenie)', start_observe: 'Spustiť (pozorovanie)',
    step: 'Krok', continue: 'Pokračovať', stop: 'Zastaviť', copy_in: 'Kopírovať IN', copy_out: 'Kopírovať OUT', copy_err: 'Kopírovať chybu',
    error_network: 'Chyba siete', error_action: 'Akcia zlyhala', ok: 'OK', current_sg: 'Aktuálny podgraf',
    chat: 'Chat', worker_status: 'Stav pracovníka', save: 'Uložiť', send: 'Odoslať'
  },
  header: { title: 'Pracovníci a lídri', add_leader: '+ Pridať lídra', add_worker: '+ Pridať pracovníka', leader: 'Líder:' },
  kpis: { workers: 'PRACOVNÍCI', actifs: 'AKTÍVNI', steps24h: 'KROKY (24H)', tokens24h: 'TOKENY (24H)', qualite7j: 'KVALITA (7D)' },
  toolbar: {
    process: 'Proces', current: 'Aktuálny podgraf', overview: 'Prehľad', hide_start: 'skryť START', hide_end: 'skryť END',
    labels: 'štítky', follow_sg: 'sledovať SG', mode_observe: 'Pozorovanie', mode_debug: 'Ladič stream',
    current_sg_btn: 'Aktuálny SG', display: 'Zobrazenie:', mode: 'Režim:'
  },
  modal: { process_title: 'Proces —' },
  status: {
    panel_title: 'Stav a metriky', running: 'Beží', starting: 'Spúšťa sa', failed: 'Zlyhalo',
    completed: 'Dokončené', canceled: 'Zrušené', idle: 'Nečinné', unknown: 'Neznáme'
  },
  io: { title: 'Vstupy/výstupy uzla', in: 'IN', out: 'OUT', error: 'CHYBA' },
  config: {
    title: 'Konfigurácia procesu', general: 'Všeobecné', params: 'Parametre', docs: 'Dokumentácia',
    doc_title: 'Názov', doc_desc: 'Popis', none: 'Žiadna konfigurácia nie je k dispozícii'
  },
  graph: {
    error_title: 'Graf', unavailable: 'Graf nie je k dispozícii', aria_label: 'Mermaid graf',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'chyba vykreslenia'
  },
  node_menu: {
    aria_actions: 'Akcie uzla', open_sg: 'Otvoriť podgraf', run_until: 'Spustiť do',
    break_add: 'Pridať bod prerušenia', break_remove: 'Odstrániť bod prerušenia', inspect: 'Skontrolovať'
  },
  control_inputs: {
    debug_label: 'Ladenie:', node_id: 'ID uzla', when: 'Podmienka', when_always: 'vždy',
    when_success: 'úspech', when_fail: 'zlyhanie', when_retry: 'opakovanie',
    run_until: 'Spustiť do', break_add: 'Pridať prerušenie', break_remove: 'Odstrániť prerušenie'
  },
  chat: {
    leader_panel_title: 'Líder — Chat', placeholder: 'Správa...', tools_trace: 'Zobraziť stopy nástrojov',
    error_history: 'Nepodarilo sa načítať históriu', empty_reply: '(prázdna odpoveď)', global: 'Globálny chat',
    error_history_global: 'Nepodarilo sa načítať globálnu históriu', you: 'Vy', assistant: 'LLM'
  },
  leader_global: {
    title: 'Líder — Globálny chat', select_label: 'Líder:', select_aria: 'Vyberte lídra',
    display: 'Zobrazované meno', role: 'Rola', persona: 'Persona', persona_ph: 'Orchestrátor pracovníkov',
    none_detected: '(žiadny líder)'
  },
  leader_identity_panel: {
    no_leader: 'Nebol priradený žiadny líder', error_read: 'Nepodarilo sa prečítať identitu', refresh: 'Obnoviť',
    display: 'Zobrazované meno', role: 'Rola', persona: 'Persona', persona_ph: 'Orchestrátor pracovníkov',
    global_chat: 'Globálny chat', leader_workers: 'Pracovníci lídra', loading: 'Načítava sa…',
    none_attached: 'Žiadny pripojený pracovník', error_load: 'Chyba načítania'
  },
  list: { title: 'Pracovníci', view: 'Zobraziť' },
  config_editor: {
    tabs_simple: 'Jednoduché', tabs_json: 'JSON', beautify: 'Skrášliť', minify: 'Minimalizovať',
    validate: 'Validovať', json_valid: 'Platný JSON', json_invalid: 'Neplatný JSON',
    complex_only_json: 'Niektoré zložité polia možno upravovať iba v JSON'
  },
  leader_section: { edit_identity_hint: 'Upraviť identitu (kliknite)' },
  replay: {
    title: 'Prehrávanie (stroj času)', load_run: 'Načítať beh', play: 'Prehrať', stop: 'Zastaviť',
    error_runs: 'Nepodarilo sa načítať behy', error_steps: 'Nepodarilo sa načítať kroky',
    view_node: 'Zobraziť tento uzol', live_announce_step: 'Prehrávanie kroku {idx}/{total}: {nodeId}'
  }
};
