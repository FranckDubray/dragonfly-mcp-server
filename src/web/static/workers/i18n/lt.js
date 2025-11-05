export const __meta = { standalone: true, code: 'lt', flag: '🇱🇹', native: 'Lietuvių' };
export default {
  lang: { lt: 'Lietuvių' },
  common: {
    process: 'Procesas', details: 'Išsami informacija', tools_mcp: 'MCP įrankiai:', last_step: 'Paskutinis žingsnis',
    edit_identity: 'Žiūrėti/redaguoti tapatybę', close: 'Uždaryti', start_debug: 'Pradėti (derinimas)', start_observe: 'Pradėti (stebėjimas)',
    step: 'Žingsnis', continue: 'Tęsti', stop: 'Sustabdyti', copy_in: 'Kopijuoti IN', copy_out: 'Kopijuoti OUT', copy_err: 'Kopijuoti klaidą',
    error_network: 'Tinklo klaida', error_action: 'Veiksmas nepavyko', ok: 'Gerai', current_sg: 'Dabartinis pografis',
    chat: 'Pokalbis', worker_status: 'Darbuotojo būsena', save: 'Išsaugoti', send: 'Siųsti'
  },
  header: { title: 'Darbuotojai ir lyderiai', add_leader: '+ Pridėti lyderį', add_worker: '+ Pridėti darbuotoją', leader: 'Lyderis:' },
  kpis: { workers: 'DARBUOTOJAI', actifs: 'AKTYVŪS', steps24h: 'ŽINGSNIAI (24 VAL.)', tokens24h: 'ŽETONAI (24 VAL.)', qualite7j: 'KOKYBĖ (7 D.)' },
  toolbar: {
    process: 'Procesas', current: 'Dabartinis pografis', overview: 'Apžvalga', hide_start: 'slėpti START', hide_end: 'slėpti END',
    labels: 'žymos', follow_sg: 'sekti SG', mode_observe: 'Stebėjimas', mode_debug: 'Derinimo srautas',
    current_sg_btn: 'Dabartinis SG', display: 'Rodymas:', mode: 'Režimas:'
  },
  modal: { process_title: 'Procesas —' },
  status: {
    panel_title: 'Būsena ir rodikliai', running: 'Vykdoma', starting: 'Paleidžiama', failed: 'Nepavyko',
    completed: 'Užbaigta', canceled: 'Atšaukta', idle: 'Laisva', unknown: 'Nežinoma'
  },
  io: { title: 'Mazgo įvestys/išvestys', in: 'IN', out: 'OUT', error: 'KLAIDA' },
  config: {
    title: 'Proceso konfigūracija', general: 'Bendra', params: 'Parametrai', docs: 'Dokumentacija',
    doc_title: 'Pavadinimas', doc_desc: 'Aprašymas', none: 'Nėra prieinamos konfigūracijos'
  },
  graph: {
    error_title: 'Grafikas', unavailable: 'Grafikas neprieinamas', aria_label: 'Mermaid grafikas',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'atvaizdavimo klaida'
  },
  node_menu: {
    aria_actions: 'Mazgo veiksmai', open_sg: 'Atidaryti pografį', run_until: 'Vykdyti iki',
    break_add: 'Pridėti stabdos tašką', break_remove: 'Pašalinti stabdos tašką', inspect: 'Tikrinti'
  },
  control_inputs: {
    debug_label: 'Derinimas:', node_id: 'Mazgo ID', when: 'Sąlyga', when_always: 'visada',
    when_success: 'sėkmė', when_fail: 'nesėkmė', when_retry: 'pakartojimas',
    run_until: 'Vykdyti iki', break_add: 'Pridėti stabdymą', break_remove: 'Pašalinti stabdymą'
  },
  chat: {
    leader_panel_title: 'Lyderis — Pokalbis', placeholder: 'Žinutė...', tools_trace: 'Peržiūrėti įrankių pėdsakus',
    error_history: 'Nepavyko įkelti istorijos', empty_reply: '(tuščias atsakymas)', global: 'Globalus pokalbis',
    error_history_global: 'Nepavyko įkelti globalios istorijos', you: 'Jūs', assistant: 'LLM'
  },
  leader_global: {
    title: 'Lyderis — Globalus pokalbis', select_label: 'Lyderis:', select_aria: 'Pasirinkite lyderį',
    display: 'Rodomas vardas', role: 'Vaidmuo', persona: 'Persona', persona_ph: 'Darbuotojų orkestruotojas',
    none_detected: '(nėra lyderio)'
  },
  leader_identity_panel: {
    no_leader: 'Nepriskirtas lyderis', error_read: 'Nepavyko perskaityti tapatybės', refresh: 'Atnaujinti',
    display: 'Rodomas vardas', role: 'Vaidmuo', persona: 'Persona', persona_ph: 'Darbuotojų orkestruotojas',
    global_chat: 'Globalus pokalbis', leader_workers: 'Lyderio darbuotojai', loading: 'Įkeliama…',
    none_attached: 'Nėra priskirto darbuotojo', error_load: 'Įkėlimo klaida'
  },
  list: { title: 'Darbuotojai', view: 'Žiūrėti' },
  config_editor: {
    tabs_simple: 'Paprastas', tabs_json: 'JSON', beautify: 'Gražinti', minify: 'Sumažinti',
    validate: 'Tikrinti', json_valid: 'Tinkamas JSON', json_invalid: 'Netinkamas JSON',
    complex_only_json: 'Kai kuriuos sudėtingus laukus galima redaguoti tik JSON'
  },
  leader_section: { edit_identity_hint: 'Redaguoti tapatybę (spustelėkite)' },
  replay: {
    title: 'Atkartojimas (laiko mašina)', load_run: 'Įkelti vykdymą', play: 'Groti', stop: 'Sustabdyti',
    error_runs: 'Nepavyko įkelti vykdymų', error_steps: 'Nepavyko įkelti žingsnių',
    view_node: 'Žiūrėti šį mazgą', live_announce_step: 'Grojama žingsnis {idx}/{total}: {nodeId}'
  }
};
