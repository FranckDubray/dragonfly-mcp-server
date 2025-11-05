export const __meta = { standalone: true, code: 'es', flag: '🇪🇸', native: 'Español' };
export default {
  lang: { es: 'Español' },
  header: { title: 'Trabajadores y líderes', add_leader: '+ Agregar líder', add_worker: '+ Agregar trabajador', leader: 'Líder:' },
  common: {
    process: 'Proceso', details: 'Detalles', tools_mcp: 'Herramientas MCP:', last_step: 'Último paso',
    edit_identity: 'Ver/editar identidad', close: 'Cerrar', start_observe: 'Iniciar (observar)', start_debug: 'Iniciar (depurar)',
    step: 'Paso', continue: 'Continuar', stop: 'Detener', copy_in: 'Copiar IN', copy_out: 'Copiar OUT', copy_err: 'Copiar error',
    error_network: 'Error de red', error_action: 'Acción fallida', ok: 'OK', current_sg: 'Subgrafo actual',
    chat: 'Chat', worker_status: 'Estado', save: 'Guardar', send: 'Enviar',
    status_metrics: 'Estado y métricas', running: 'En ejecución', starting: 'Iniciando', failed: 'Fallido', completed: 'Completado', canceled: 'Cancelado', idle: 'Inactivo', unknown: 'Desconocido'
  },
  kpis: { workers: 'TRABAJADORES', actifs: 'ACTIVOS', steps24h: 'PASOS (24H)', tokens24h: 'TOKENS (24H)', qualite7j: 'CALIDAD (7D)' },
  toolbar: {
    process: 'Proceso', current: 'Subgrafo actual', overview: 'Resumen', hide_start: 'ocultar START', hide_end: 'ocultar END',
    labels: 'etiquetas', follow_sg: 'seguir SG', mode_observe: 'Observar', mode_debug: 'Flujo de depuración', current_sg_btn: 'SG actual',
    display: 'Mostrar:', mode: 'Modo:'
  },
  modal: { process_title: 'Proceso —' },
  status: { panel_title: 'Estado y métricas', running: 'En ejecución', starting: 'Iniciando', failed: 'Fallido', completed: 'Completado', canceled: 'Cancelado', idle: 'Inactivo', unknown: 'Desconocido' },
  io: { title: 'Entradas/Salidas del nodo', in: 'IN', out: 'OUT', error: 'ERROR' },
  config: { title: 'Configuración del proceso', general: 'General', params: 'Parámetros', docs: 'Documentación', doc_title: 'Título', doc_desc: 'Descripción', none: 'No hay configuración disponible' },
  graph: { error_title: 'Gráfico', unavailable: 'Gráfico no disponible', aria_label: 'Gráfico Mermaid', mermaid_error_prefix: 'Mermaid — ', render_error: 'error de renderizado' },
  node_menu: { aria_actions: 'Acciones del nodo', open_sg: 'Abrir subgrafo', run_until: 'Ejecutar hasta', break_add: 'Añadir punto de interrupción', break_remove: 'Quitar punto de interrupción', inspect: 'Inspeccionar' },
  control_inputs: { debug_label: 'Depurar:', node_id: 'ID del nodo', when: 'Condición', when_always: 'siempre', when_success: 'éxito', when_fail: 'error', when_retry: 'reintentar', run_until: 'Ejecutar hasta', break_add: 'Añadir punto de interrupción', break_remove: 'Quitar punto de interrupción' },
  chat: { leader_panel_title: 'Líder — Chat', placeholder: 'Mensaje...', tools_trace: 'Ver trazas de herramientas', error_history: 'Error al cargar el historial', empty_reply: '(respuesta vacía)', global: 'Chat global', error_history_global: 'Error al cargar el historial global', you: 'Tú', assistant: 'LLM' },
  leader_global: { title: 'Líder — Chat global', select_label: 'Líder:', select_aria: 'Seleccionar un líder', display: 'Nombre para mostrar', role: 'Rol', persona: 'Persona', persona_ph: 'Orquestador de workers', none_detected: '(sin líder)' },
  leader_identity_panel: { no_leader: 'Ningún líder asignado', error_read: 'Error al leer la identidad', refresh: 'Actualizar', display: 'Nombre para mostrar', role: 'Rol', persona: 'Persona', persona_ph: 'Orquestador de workers', global_chat: 'Chat global', leader_workers: 'Workers del líder', loading: 'Cargando…', none_attached: 'Ningún worker adjunto', error_load: 'Error de carga' },
  list: { title: 'Trabajadores', view: 'Ver' },
  config_editor: { tabs_simple: 'Simple', tabs_json: 'JSON', beautify: 'Dar formato', minify: 'Minimizar', validate: 'Validar', json_valid: 'JSON válido', json_invalid: 'JSON inválido', complex_only_json: 'Algunos campos complejos solo se pueden editar en JSON' },
  leader_section: { edit_identity_hint: 'Editar identidad (clic)' },
  replay: { title: 'Reproducción (máquina del tiempo)', load_run: 'Cargar ejecución', play: 'Reproducir', stop: 'Detener', error_runs: 'Error al cargar ejecuciones', error_steps: 'Error al cargar pasos', view_node: 'Ver este nodo', live_announce_step: 'Reproduciendo paso {idx}/{total}: {nodeId}' }
};
