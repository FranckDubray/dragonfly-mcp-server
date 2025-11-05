export const __meta = { standalone: true, code: 'pt', flag: '🇵🇹', native: 'Português' };
export default {
  lang: { pt: 'Português' },
  header: { title: 'Trabalhadores e líderes', add_leader: '+ Adicionar líder', add_worker: '+ Adicionar trabalhador', leader: 'Líder:' },
  common: {
    process: 'Processo', details: 'Detalhes', tools_mcp: 'Ferramentas MCP:', last_step: 'Último passo',
    edit_identity: 'Ver/editar identidade', close: 'Fechar', start_observe: 'Iniciar (observar)', start_debug: 'Iniciar (depurar)',
    step: 'Passo', continue: 'Continuar', stop: 'Parar', copy_in: 'Copiar IN', copy_out: 'Copiar OUT', copy_err: 'Copiar erro',
    error_network: 'Erro de rede', error_action: 'Ação falhou', ok: 'OK', current_sg: 'Subgrafo atual',
    chat: 'Chat', worker_status: 'Estado', save: 'Guardar', send: 'Enviar',
    status_metrics: 'Estado e métricas', running: 'Em execução', starting: 'A iniciar', failed: 'Falhou', completed: 'Concluído', canceled: 'Cancelado', idle: 'Inativo', unknown: 'Desconhecido'
  },
  kpis: { workers: 'TRABALHADORES', actifs: 'ATIVOS', steps24h: 'PASSOS (24H)', tokens24h: 'TOKENS (24H)', qualite7j: 'QUALIDADE (7D)' },
  toolbar: {
    process: 'Processo', current: 'Subgrafo atual', overview: 'Visão geral', hide_start: 'ocultar START', hide_end: 'ocultar END',
    labels: 'rótulos', follow_sg: 'seguir SG', mode_observe: 'Observar', mode_debug: 'Fluxo de depuração', current_sg_btn: 'SG atual',
    display: 'Mostrar:', mode: 'Modo:'
  },
  modal: { process_title: 'Processo —' },
  status: { panel_title: 'Estado e métricas', running: 'Em execução', starting: 'A iniciar', failed: 'Falhou', completed: 'Concluído', canceled: 'Cancelado', idle: 'Inativo', unknown: 'Desconhecido' },
  io: { title: 'Entradas/Saídas do nó', in: 'IN', out: 'OUT', error: 'ERRO' },
  config: { title: 'Configuração do processo', general: 'Geral', params: 'Parâmetros', docs: 'Documentação', doc_title: 'Título', doc_desc: 'Descrição', none: 'Nenhuma configuração disponível' },
  graph: { error_title: 'Gráfico', unavailable: 'Gráfico indisponível', aria_label: 'Gráfico Mermaid', mermaid_error_prefix: 'Mermaid — ', render_error: 'erro de renderização' },
  node_menu: { aria_actions: 'Ações do nó', open_sg: 'Abrir subgrafo', run_until: 'Executar até', break_add: 'Adicionar ponto de interrupção', break_remove: 'Remover ponto de interrupção', inspect: 'Inspecionar' },
  control_inputs: { debug_label: 'Depuração:', node_id: 'ID do nó', when: 'Condição', when_always: 'sempre', when_success: 'sucesso', when_fail: 'falha', when_retry: 'tentar novamente', run_until: 'Executar até', break_add: 'Adicionar ponto de interrupção', break_remove: 'Remover ponto de interrupção' },
  chat: { leader_panel_title: 'Líder — Chat', placeholder: 'Mensagem...', tools_trace: 'Ver rastros das ferramentas', error_history: 'Falha ao carregar o histórico', empty_reply: '(resposta vazia)', global: 'Chat global', error_history_global: 'Falha ao carregar o histórico global', you: 'Você', assistant: 'LLM' },
  leader_global: { title: 'Líder — Chat global', select_label: 'Líder:', select_aria: 'Selecionar um líder', display: 'Nome de exibição', role: 'Função', persona: 'Persona', persona_ph: 'Orquestrador de workers', none_detected: '(nenhum líder)' },
  leader_identity_panel: { no_leader: 'Nenhum líder atribuído', error_read: 'Falha ao ler a identidade', refresh: 'Atualizar', display: 'Nome de exibição', role: 'Função', persona: 'Persona', persona_ph: 'Orquestrador de workers', global_chat: 'Chat global', leader_workers: 'Workers do líder', loading: 'A carregar…', none_attached: 'Nenhum worker anexado', error_load: 'Erro de carregamento' },
  list: { title: 'Trabalhadores', view: 'Ver' },
  config_editor: { tabs_simple: 'Simples', tabs_json: 'JSON', beautify: 'Formatar', minify: 'Minificar', validate: 'Validar', json_valid: 'JSON válido', json_invalid: 'JSON inválido', complex_only_json: 'Alguns campos complexos só podem ser editados em JSON' },
  leader_section: { edit_identity_hint: 'Editar identidade (clique)' },
  replay: { title: 'Reprodução (máquina do tempo)', load_run: 'Carregar execução', play: 'Reproduzir', stop: 'Parar', error_runs: 'Falha ao carregar execuções', error_steps: 'Falha ao carregar passos', view_node: 'Ver este nó', live_announce_step: 'Reproduzindo passo {idx}/{total}: {nodeId}' }
};
