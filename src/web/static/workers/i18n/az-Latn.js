export const __meta = { standalone: true, code: 'az-Latn', flag: '🇦🇿', native: 'Azərbaycan dili' };
export default {
  lang: { 'az-Latn': 'Azərbaycan dili' },
  common: {
    process: 'Proses', details: 'Təfərrüatlar', tools_mcp: 'MCP alətləri:', last_step: 'Son addım',
    edit_identity: 'Şəxsiyyətə bax/redaktə et', close: 'Bağla', start_debug: 'Başlat (sazlama)', start_observe: 'Başlat (müşahidə)',
    step: 'Addım', continue: 'Davam et', stop: 'Dayandır', copy_in: 'IN kopyala', copy_out: 'OUT kopyala', copy_err: 'Xəta kopyala',
    error_network: 'Şəbəkə xətası', error_action: 'Əməliyyat uğursuz oldu', ok: 'OK', current_sg: 'Cari alt qraf',
    chat: 'Söhbət', worker_status: 'İşçinin statusu', save: 'Yadda saxla', send: 'Göndər'
  },
  header: { title: 'İşçilər və Liderlər', add_leader: '+ Lider əlavə et', add_worker: '+ İşçi əlavə et', leader: 'Lider:' },
  kpis: { workers: 'İŞÇİLƏR', actifs: 'AKTİV', steps24h: 'ADDIMLAR (24S)', tokens24h: 'TOKENLƏR (24S)', qualite7j: 'KEYFİYYƏT (7G)' },
  toolbar: {
    process: 'Proses', current: 'Cari alt qraf', overview: 'Ümumi baxış', hide_start: 'BAŞLANĞICI gizlət', hide_end: 'SONU gizlət',
    labels: 'etiketlər', follow_sg: 'SG izlə', mode_observe: 'Müşahidə', mode_debug: 'Sazlama axını',
    current_sg_btn: 'Cari SG', display: 'Göstəriş:', mode: 'Rejim:'
  },
  modal: { process_title: 'Proses —' },
  status: {
    panel_title: 'Status və göstəricilər', running: 'İşləyir', starting: 'Başlayır', failed: 'Uğursuz',
    completed: 'Tamamlandı', canceled: 'Ləğv edildi', idle: 'Gözləmədə', unknown: 'Naməlum'
  },
  io: { title: 'Node girişləri/çıxışları', in: 'IN', out: 'OUT', error: 'XƏTA' },
  config: {
    title: 'Proses konfiqurasiyası', general: 'Ümumi', params: 'Parametrlər', docs: 'Sənədlər',
    doc_title: 'Başlıq', doc_desc: 'Təsvir', none: 'Konfiqurasiya mövcud deyil'
  },
  graph: {
    error_title: 'Qraf', unavailable: 'Qraf əlçatan deyil', aria_label: 'Mermaid qrafı',
    mermaid_error_prefix: 'Mermaid — ', render_error: 'render xətası'
  },
  node_menu: {
    aria_actions: 'Node əməliyyatları', open_sg: 'Alt qrafı aç', run_until: 'Qədər işlət',
    break_add: 'Fasilə nöqtəsi əlavə et', break_remove: 'Fasilə nöqtəsini sil', inspect: 'Yoxla'
  },
  control_inputs: {
    debug_label: 'Sazlama:', node_id: 'Node ID', when: 'Şərt', when_always: 'həmişə',
    when_success: 'uğur', when_fail: 'uğursuz', when_retry: 'təkrar',
    run_until: 'Qədər işlət', break_add: 'Fasilə əlavə et', break_remove: 'Fasiləni sil'
  },
  chat: {
    leader_panel_title: 'Lider — Söhbət', placeholder: 'Mesaj...', tools_trace: 'Alət izlərini gör',
    error_history: 'Tarixçə yüklənmədi', empty_reply: '(boş cavab)', global: 'Qlobal söhbət',
    error_history_global: 'Qlobal tarixçə yüklənmədi', you: 'Siz', assistant: 'LLM'
  },
  leader_global: {
    title: 'Lider — Qlobal söhbət', select_label: 'Lider:', select_aria: 'Lider seçin',
    display: 'Görüntü adı', role: 'Rol', persona: 'Persona', persona_ph: 'İşçi orkestratoru',
    none_detected: '(lider yoxdur)'
  },
  leader_identity_panel: {
    no_leader: 'Təyin edilmiş lider yoxdur', error_read: 'Şəxsiyyət oxunmadı', refresh: 'Yenilə',
    display: 'Görüntü adı', role: 'Rol', persona: 'Persona', persona_ph: 'İşçi orkestratoru',
    global_chat: 'Qlobal söhbət', leader_workers: 'Liderin işçiləri', loading: 'Yüklənir…',
    none_attached: 'Əlavə işçi yoxdur', error_load: 'Yükləmə xətası'
  },
  list: { title: 'İşçilər', view: 'Bax' },
  config_editor: {
    tabs_simple: 'Sadə', tabs_json: 'JSON', beautify: 'Gözəlləşdir', minify: 'Kiçilt',
    validate: 'Yoxla', json_valid: 'Etibarlı JSON', json_invalid: 'Etibarsız JSON',
    complex_only_json: 'Bəzi mürəkkəb sahələr yalnız JSON-da redaktə oluna bilər'
  },
  leader_section: { edit_identity_hint: 'Şəxsiyyəti redaktə et (klikləyin)' },
  replay: {
    title: 'Təkrar (vaxt maşını)', load_run: 'İşə salma yüklə', play: 'Oynat', stop: 'Dayandır',
    error_runs: 'İşə salmalar yüklənmədi', error_steps: 'Addımlar yüklənmədi',
    view_node: 'Bu node-a bax', live_announce_step: '{idx}/{total} addım oynadılır: {nodeId}'
  }
};
