export const __meta = { standalone: true, code: 'pl', flag: '🇵🇱', native: 'Polski' };
export default {
  lang: { pl: 'Polski' },
  common: {
    process: 'Proces', details: 'Szczegóły', tools_mcp: 'Narzędzia MCP:', last_step: 'Ostatni krok',
    edit_identity: 'Wyświetl/edytuj tożsamość', close: 'Zamknij', start_debug: 'Start (debugowanie)', start_observe: 'Start (obserwacja)',
    step: 'Krok', continue: 'Kontynuuj', stop: 'Zatrzymaj', copy_in: 'Kopiuj IN', copy_out: 'Kopiuj OUT', copy_err: 'Kopiuj błąd',
    error_network: 'Błąd sieci', error_action: 'Akcja nie powiodła się', ok: 'OK', current_sg: 'Bieżący podgraf',
    chat: 'Czat', worker_status: 'Status pracownika', save: 'Zapisz', send: 'Wyślij'
  },
  header: { title: 'Pracownicy i liderzy', add_leader: '+ Dodaj lidera', add_worker: '+ Dodaj pracownika', leader: 'Lider:' },
  kpis: { workers: 'PRACOWNICY', actifs: 'AKTYWNI', steps24h: 'KROKI (24H)', tokens24h: 'TOKENY (24H)', qualite7j: 'JAKOŚĆ (7D)' },
  toolbar: {
    process: 'Proces', current: 'Bieżący podgraf', overview: 'Przegląd', hide_start: 'ukryj START', hide_end: 'ukryj END',
    labels: 'etykiety', follow_sg: 'śledź SG', mode_observe: 'Obserwacja', mode_debug: 'Strumień debug',
    current_sg_btn: 'Bieżący SG', display: 'Wyświetlanie:', mode: 'Tryb:'
  },
  modal: { process_title: 'Proces —' },
  status: {
    panel_title: 'Status i metryki', running: 'Działa', starting: 'Uruchamianie', failed: 'Niepowodzenie',
    completed: 'Zakończono', canceled: 'Anulowano', idle: 'Bezczynny', unknown: 'Nieznany'
  },
  io: { title: 'Wejścia/wyjścia węzła', in: 'IN', out: 'OUT', error: 'BŁĄD' },
  config: {
    title: 'Konfiguracja procesu', general: 'Ogólne', params: 'Parametry', docs: 'Dokumentacja',
    doc_title: 'Tytuł', doc_desc: 'Opis', none: 'Brak dostępnej konfiguracji'
  },
  graph: {
    error_title: 'Graf', unavailable: 'Graf niedostępny', aria_label: 'Graf Mermaid',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'błąd renderowania'
  },
  node_menu: {
    aria_actions: 'Akcje węzła', open_sg: 'Otwórz podgraf', run_until: 'Uruchom do',
    break_add: 'Dodaj punkt przerwania', break_remove: 'Usuń punkt przerwania', inspect: 'Sprawdź'
  },
  control_inputs: {
    debug_label: 'Debug:', node_id: 'ID węzła', when: 'Warunek', when_always: 'zawsze',
    when_success: 'sukces', when_fail: 'niepowodzenie', when_retry: 'ponowienie',
    run_until: 'Uruchom do', break_add: 'Dodaj przerwanie', break_remove: 'Usuń przerwanie'
  },
  chat: {
    leader_panel_title: 'Lider — Czat', placeholder: 'Wiadomość...', tools_trace: 'Zobacz ślady narzędzi',
    error_history: 'Nie udało się wczytać historii', empty_reply: '(pusta odpowiedź)', global: 'Czat globalny',
    error_history_global: 'Nie udało się wczytać historii globalnej', you: 'Ty', assistant: 'LLM'
  },
  leader_global: {
    title: 'Lider — Czat globalny', select_label: 'Lider:', select_aria: 'Wybierz lidera',
    display: 'Nazwa wyświetlana', role: 'Rola', persona: 'Persona', persona_ph: 'Orkiestrator pracowników',
    none_detected: '(brak lidera)'
  },
  leader_identity_panel: {
    no_leader: 'Nie przypisano lidera', error_read: 'Nie udało się odczytać tożsamości', refresh: 'Odśwież',
    display: 'Nazwa wyświetlana', role: 'Rola', persona: 'Persona', persona_ph: 'Orkiestrator pracowników',
    global_chat: 'Czat globalny', leader_workers: 'Pracownicy lidera', loading: 'Ładowanie…',
    none_attached: 'Brak przypisanego pracownika', error_load: 'Błąd ładowania'
  },
  list: { title: 'Pracownicy', view: 'Wyświetl' },
  config_editor: {
    tabs_simple: 'Prosty', tabs_json: 'JSON', beautify: 'Sformatuj', minify: 'Zminifikuj',
    validate: 'Waliduj', json_valid: 'Poprawny JSON', json_invalid: 'Niepoprawny JSON',
    complex_only_json: 'Niektóre złożone pola można edytować tylko w JSON'
  },
  leader_section: { edit_identity_hint: 'Edytuj tożsamość (kliknij)' },
  replay: {
    title: 'Odtwarzanie (maszyna czasu)', load_run: 'Załaduj uruchomienie', play: 'Odtwórz', stop: 'Zatrzymaj',
    error_runs: 'Nie udało się załadować uruchomień', error_steps: 'Nie udało się załadować kroków',
    view_node: 'Zobacz ten węzeł', live_announce_step: 'Odtwarzanie kroku {idx}/{total}: {nodeId}'
  }
};
