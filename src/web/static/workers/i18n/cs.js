export const __meta = { standalone: true, code: 'cs', flag: '🇨🇿', native: 'Čeština' };
export default {
  lang: { cs: 'Čeština' },
  common: {
    process: 'Proces', details: 'Podrobnosti', tools_mcp: 'MCP nástroje:', last_step: 'Poslední krok',
    edit_identity: 'Zobrazit/upravit identitu', close: 'Zavřít', start_debug: 'Spustit (ladění)', start_observe: 'Spustit (pozorování)',
    step: 'Krok', continue: 'Pokračovat', stop: 'Zastavit', copy_in: 'Kopírovat IN', copy_out: 'Kopírovat OUT', copy_err: 'Kopírovat chybu',
    error_network: 'Chyba sítě', error_action: 'Akce selhala', ok: 'OK', current_sg: 'Aktuální podgraf',
    chat: 'Chat', worker_status: 'Stav pracovníka', save: 'Uložit', send: 'Odeslat'
  },
  header: { title: 'Pracovníci a vedoucí', add_leader: '+ Přidat vedoucího', add_worker: '+ Přidat pracovníka', leader: 'Vedoucí:' },
  kpis: { workers: 'PRACOVNÍCI', actifs: 'AKTIVNÍ', steps24h: 'KROKY (24H)', tokens24h: 'TOKENY (24H)', qualite7j: 'KVALITA (7D)' },
  toolbar: {
    process: 'Proces', current: 'Aktuální podgraf', overview: 'Přehled', hide_start: 'skrýt START', hide_end: 'skrýt END',
    labels: 'štítky', follow_sg: 'sledovat SG', mode_observe: 'Pozorování', mode_debug: 'Ladící stream',
    current_sg_btn: 'Aktuální SG', display: 'Zobrazení:', mode: 'Režim:'
  },
  modal: { process_title: 'Proces —' },
  status: {
    panel_title: 'Stav a metriky', running: 'Běží', starting: 'Spouští se', failed: 'Selhalo',
    completed: 'Dokončeno', canceled: 'Zrušeno', idle: 'Nečinný', unknown: 'Neznámý'
  },
  io: { title: 'Vstupy/výstupy uzlu', in: 'IN', out: 'OUT', error: 'CHYBA' },
  config: {
    title: 'Konfigurace procesu', general: 'Obecné', params: 'Parametry', docs: 'Dokumentace',
    doc_title: 'Nadpis', doc_desc: 'Popis', none: 'Není k dispozici žádná konfigurace'
  },
  graph: {
    error_title: 'Graf', unavailable: 'Graf není k dispozici', aria_label: 'Mermaid graf',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'chyba vykreslení'
  },
  node_menu: {
    aria_actions: 'Akce uzlu', open_sg: 'Otevřít podgraf', run_until: 'Spustit do',
    break_add: 'Přidat bod přerušení', break_remove: 'Odebrat bod přerušení', inspect: 'Zkontrolovat'
  },
  control_inputs: {
    debug_label: 'Ladění:', node_id: 'ID uzlu', when: 'Podmínka', when_always: 'vždy',
    when_success: 'úspěch', when_fail: 'selhání', when_retry: 'opakování',
    run_until: 'Spustit do', break_add: 'Přidat přerušení', break_remove: 'Odebrat přerušení'
  },
  chat: {
    leader_panel_title: 'Vedoucí — Chat', placeholder: 'Zpráva...', tools_trace: 'Zobrazit trasování nástrojů',
    error_history: 'Nepodařilo se načíst historii', empty_reply: '(prázdná odpověď)', global: 'Globální chat',
    error_history_global: 'Nepodařilo se načíst globální historii', you: 'Vy', assistant: 'LLM'
  },
  leader_global: {
    title: 'Vedoucí — Globální chat', select_label: 'Vedoucí:', select_aria: 'Vyberte vedoucího',
    display: 'Zobrazované jméno', role: 'Role', persona: 'Persona', persona_ph: 'Orchestrátor pracovníků',
    none_detected: '(žádný vedoucí)'
  },
  leader_identity_panel: {
    no_leader: 'Nebyl přiřazen žádný vedoucí', error_read: 'Nepodařilo se přečíst identitu', refresh: 'Obnovit',
    display: 'Zobrazované jméno', role: 'Role', persona: 'Persona', persona_ph: 'Orchestrátor pracovníků',
    global_chat: 'Globální chat', leader_workers: 'Pracovníci vedoucího', loading: 'Načítání…',
    none_attached: 'Žádný připojený pracovník', error_load: 'Chyba načítání'
  },
  list: { title: 'Pracovníci', view: 'Zobrazit' },
  config_editor: {
    tabs_simple: 'Jednoduché', tabs_json: 'JSON', beautify: 'Zformátovat', minify: 'Minimalizovat',
    validate: 'Validovat', json_valid: 'Platný JSON', json_invalid: 'Neplatný JSON',
    complex_only_json: 'Některá složitá pole lze upravovat pouze v JSON'
  },
  leader_section: { edit_identity_hint: 'Upravit identitu (klikněte)' },
  replay: {
    title: 'Přehrání (stroj času)', load_run: 'Načíst běh', play: 'Přehrát', stop: 'Zastavit',
    error_runs: 'Nepodařilo se načíst běhy', error_steps: 'Nepodařilo se načíst kroky',
    view_node: 'Zobrazit tento uzel', live_announce_step: 'Přehrávání kroku {idx}/{total}: {nodeId}'
  }
};
