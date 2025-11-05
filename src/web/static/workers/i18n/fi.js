export const __meta = { standalone: true, code: 'fi', flag: '🇫🇮', native: 'Suomi' };
export default {
  lang: { fi: 'Suomi' },
  common: {
    process: 'Prosessi', details: 'Yksityiskohdat', tools_mcp: 'MCP-työkalut:', last_step: 'Viimeinen vaihe',
    edit_identity: 'Näytä/muokkaa identiteettiä', close: 'Sulje', start_debug: 'Käynnistä (virheenkorjaus)', start_observe: 'Käynnistä (havainnointi)',
    step: 'Vaihe', continue: 'Jatka', stop: 'Pysäytä', copy_in: 'Kopioi IN', copy_out: 'Kopioi OUT', copy_err: 'Kopioi virhe',
    error_network: 'Verkkovirhe', error_action: 'Toiminto epäonnistui', ok: 'OK', current_sg: 'Nykyinen alikaavio',
    chat: 'Keskustelu', worker_status: 'Workerin tila', save: 'Tallenna', send: 'Lähetä'
  },
  header: { title: 'Työntekijät ja johtajat', add_leader: '+ Lisää johtaja', add_worker: '+ Lisää työntekijä', leader: 'Johtaja:' },
  kpis: { workers: 'TYÖNTEKIJÄT', actifs: 'AKTIIVISET', steps24h: 'VAIHEET (24H)', tokens24h: 'TOKENIT (24H)', qualite7j: 'LAATU (7PV)' },
  toolbar: {
    process: 'Prosessi', current: 'Nykyinen alikaavio', overview: 'Yleiskatsaus', hide_start: 'piilota START', hide_end: 'piilota END',
    labels: 'tunnisteet', follow_sg: 'seuraa SG', mode_observe: 'Havainnointi', mode_debug: 'Virheenkorjausvirta',
    current_sg_btn: 'Nykyinen SG', display: 'Näyttö:', mode: 'Tila:'
  },
  modal: { process_title: 'Prosessi —' },
  status: {
    panel_title: 'Tila ja mittarit', running: 'Käynnissä', starting: 'Käynnistyy', failed: 'Epäonnistui',
    completed: 'Valmis', canceled: 'Peruutettu', idle: 'Vapaa', unknown: 'Tuntematon'
  },
  io: { title: 'Solmun sisään-/ulostulot', in: 'IN', out: 'OUT', error: 'VIRHE' },
  config: {
    title: 'Prosessin konfiguraatio', general: 'Yleinen', params: 'Parametrit', docs: 'Dokumentaatio',
    doc_title: 'Otsikko', doc_desc: 'Kuvaus', none: 'Ei saatavilla olevaa konfiguraatiota'
  },
  graph: {
    error_title: 'Kaavio', unavailable: 'Kaavio ei saatavilla', aria_label: 'Mermaid-kaavio',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'renderointivirhe'
  },
  node_menu: {
    aria_actions: 'Solmun toiminnot', open_sg: 'Avaa alikaavio', run_until: 'Suorita saakka',
    break_add: 'Lisää keskeytyskohta', break_remove: 'Poista keskeytyskohta', inspect: 'Tarkastele'
  },
  control_inputs: {
    debug_label: 'Virheenkorjaus:', node_id: 'Solmun ID', when: 'Ehto', when_always: 'aina',
    when_success: 'onnistuminen', when_fail: 'epäonnistuminen', when_retry: 'uudelleenyritys',
    run_until: 'Suorita saakka', break_add: 'Lisää keskeytys', break_remove: 'Poista keskeytys'
  },
  chat: {
    leader_panel_title: 'Johtaja — Keskustelu', placeholder: 'Viesti...', tools_trace: 'Näytä työkalujäljet',
    error_history: 'Historian lataaminen epäonnistui', empty_reply: '(tyhjä vastaus)', global: 'Globaali keskustelu',
    error_history_global: 'Globaalin historian lataaminen epäonnistui', you: 'Sinä', assistant: 'LLM'
  },
  leader_global: {
    title: 'Johtaja — Globaali keskustelu', select_label: 'Johtaja:', select_aria: 'Valitse johtaja',
    display: 'Näyttönimi', role: 'Rooli', persona: 'Persoona', persona_ph: 'Työntekijöiden orkestroija',
    none_detected: '(ei johtajaa)'
  },
  leader_identity_panel: {
    no_leader: 'Ei määritettyä johtajaa', error_read: 'Identiteetin lukeminen epäonnistui', refresh: 'Päivitä',
    display: 'Näyttönimi', role: 'Rooli', persona: 'Persoona', persona_ph: 'Työntekijöiden orkestroija',
    global_chat: 'Globaali keskustelu', leader_workers: 'Johtajan työntekijät', loading: 'Ladataan…',
    none_attached: 'Ei liitettyä työntekijää', error_load: 'Latausvirhe'
  },
  list: { title: 'Työntekijät', view: 'Näytä' },
  config_editor: {
    tabs_simple: 'Yksinkertainen', tabs_json: 'JSON', beautify: 'Kaunista', minify: 'Minimoi',
    validate: 'Validoi', json_valid: 'Kelvollinen JSON', json_invalid: 'Virheellinen JSON',
    complex_only_json: 'Jotkut monimutkaiset kentät voidaan muokata vain JSON:ssa'
  },
  leader_section: { edit_identity_hint: 'Muokkaa identiteettiä (klikkaa)' },
  replay: {
    title: 'Toisto (aikakone)', load_run: 'Lataa suoritus', play: 'Toista', stop: 'Pysäytä',
    error_runs: 'Suoritusten lataaminen epäonnistui', error_steps: 'Vaiheiden lataaminen epäonnistui',
    view_node: 'Näytä tämä solmu', live_announce_step: 'Toistetaan vaihetta {idx}/{total}: {nodeId}'
  }
};
