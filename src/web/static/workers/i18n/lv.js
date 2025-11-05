export const __meta = { standalone: true, code: 'lv', flag: '🇱🇻', native: 'Latviešu' };
export default {
  lang: { lv: 'Latviešu' },
  common: {
    process: 'Process', details: 'Detaļas', tools_mcp: 'MCP rīki:', last_step: 'Pēdējais solis',
    edit_identity: 'Skatīt/rediģēt identitāti', close: 'Aizvērt', start_debug: 'Sākt (atkļūdošana)', start_observe: 'Sākt (novērošana)',
    step: 'Solis', continue: 'Turpināt', stop: 'Apturēt', copy_in: 'Kopēt IN', copy_out: 'Kopēt OUT', copy_err: 'Kopēt kļūdu',
    error_network: 'Tīkla kļūda', error_action: 'Darbība neizdevās', ok: 'Labi', current_sg: 'Pašreizējais apakšgrafiks',
    chat: 'Tērzēšana', worker_status: 'Darbinieka statuss', save: 'Saglabāt', send: 'Sūtīt'
  },
  header: { title: 'Darbinieki un vadītāji', add_leader: '+ Pievienot vadītāju', add_worker: '+ Pievienot darbinieku', leader: 'Vadītājs:' },
  kpis: { workers: 'DARBINIEKI', actifs: 'AKTĪVI', steps24h: 'SOĻI (24H)', tokens24h: 'ŽETONI (24H)', qualite7j: 'KVALITĀTE (7D)' },
  toolbar: {
    process: 'Process', current: 'Pašreizējais apakšgrafiks', overview: 'Pārskats', hide_start: 'paslēpt START', hide_end: 'paslēpt END',
    labels: 'etiķetes', follow_sg: 'sekot SG', mode_observe: 'Novērošana', mode_debug: 'Atkļūdošanas plūsma',
    current_sg_btn: 'Pašreizējais SG', display: 'Attēlojums:', mode: 'Režīms:'
  },
  modal: { process_title: 'Process —' },
  status: {
    panel_title: 'Statuss un metrikas', running: 'Darbībā', starting: 'Uzsākšana', failed: 'Neizdevās',
    completed: 'Pabeigts', canceled: 'Atcelts', idle: 'Dīkstāve', unknown: 'Nezināms'
  },
  io: { title: 'Mezgla ievades/izvades', in: 'IN', out: 'OUT', error: 'KĻŪDA' },
  config: {
    title: 'Procesa konfigurācija', general: 'Vispārīgi', params: 'Parametri', docs: 'Dokumentācija',
    doc_title: 'Nosaukums', doc_desc: 'Apraksts', none: 'Nav pieejama konfigurācija'
  },
  graph: {
    error_title: 'Grafiks', unavailable: 'Grafiks nav pieejams', aria_label: 'Mermaid grafiks',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'renderēšanas kļūda'
  },
  node_menu: {
    aria_actions: 'Mezgla darbības', open_sg: 'Atvērt apakšgrafiku', run_until: 'Izpildīt līdz',
    break_add: 'Pievienot pārtraukuma punktu', break_remove: 'Noņemt pārtraukuma punktu', inspect: 'Pārbaudīt'
  },
  control_inputs: {
    debug_label: 'Atkļūdošana:', node_id: 'Mezgla ID', when: 'Nosacījums', when_always: 'vienmēr',
    when_success: 'veiksme', when_fail: 'neveiksme', when_retry: 'atkārtot',
    run_until: 'Izpildīt līdz', break_add: 'Pievienot pārtraukumu', break_remove: 'Noņemt pārtraukumu'
  },
  chat: {
    leader_panel_title: 'Vadītājs — Tērzēšana', placeholder: 'Ziņojums...', tools_trace: 'Skatīt rīku pēdas',
    error_history: 'Neizdevās ielādēt vēsturi', empty_reply: '(tukša atbilde)', global: 'Globālā tērzēšana',
    error_history_global: 'Neizdevās ielādēt globālo vēsturi', you: 'Jūs', assistant: 'LLM'
  },
  leader_global: {
    title: 'Vadītājs — Globālā tērzēšana', select_label: 'Vadītājs:', select_aria: 'Izvēlieties vadītāju',
    display: 'Attēlojamais vārds', role: 'Loma', persona: 'Persona', persona_ph: 'Darbinieku orkestrators',
    none_detected: '(nav vadītāja)'
  },
  leader_identity_panel: {
    no_leader: 'Nav piešķirts vadītājs', error_read: 'Neizdevās nolasīt identitāti', refresh: 'Atjaunināt',
    display: 'Attēlojamais vārds', role: 'Loma', persona: 'Persona', persona_ph: 'Darbinieku orkestrators',
    global_chat: 'Globālā tērzēšana', leader_workers: 'Vadītāja darbinieki', loading: 'Ielādē…',
    none_attached: 'Nav pievienots darbinieks', error_load: 'Ielādes kļūda'
  },
  list: { title: 'Darbinieki', view: 'Skatīt' },
  config_editor: {
    tabs_simple: 'Vienkāršs', tabs_json: 'JSON', beautify: 'Skaistināt', minify: 'Samazināt',
    validate: 'Validēt', json_valid: 'Derīgs JSON', json_invalid: 'Nederīgs JSON',
    complex_only_json: 'Dažus sarežģītus laukus var rediģēt tikai JSON'
  },
  leader_section: { edit_identity_hint: 'Rediģēt identitāti (noklikšķiniet)' },
  replay: {
    title: 'Atkārtošana (laika mašīna)', load_run: 'Ielādēt izpildi', play: 'Atskaņot', stop: 'Apturēt',
    error_runs: 'Neizdevās ielādēt izpildes', error_steps: 'Neizdevās ielādēt soļus',
    view_node: 'Skatīt šo mezglu', live_announce_step: 'Atskaņo soli {idx}/{total}: {nodeId}'
  }
};
