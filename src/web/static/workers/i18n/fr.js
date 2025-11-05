





















export const __meta = { standalone: true, code: 'fr', flag: '🇫🇷', native: 'Français' };
export default {
  lang: { fr:'Français' },
  common: {
    process: 'Processus', details: 'Détails', tools_mcp: 'Tools MCP:', last_step: 'Dernière étape', edit_identity: "Voir/éditer l’identité", close: 'Fermer', start_debug: 'Start (debug)', start_observe: 'Start (observe)', step: 'Step', continue: 'Continue', stop: 'Stop', copy_in: 'Copier IN', copy_out: 'Copier OUT', copy_err: 'Copier erreur', error_network: 'Erreur réseau', error_action: 'Action échouée', ok: 'OK', current_sg: 'Sous-graphe courant', chat:'Chat', worker_status:'Status', save:'Enregistrer', send:'Envoyer'
  },
  header: { title: 'Workers & Leaders', add_leader: '+ Créer un leader', add_worker: '+ Ajouter un worker', leader: 'Leader:' },
  kpis: { workers: 'WORKERS', actifs: 'ACTIFS', steps24h: 'ÉTAPES (24H)', tokens24h: 'TOKENS (24H)', qualite7j: 'QUALITÉ (7J)' },
  toolbar: { process: 'Processus', current: 'Sous-graphe courant', overview: 'Overview', hide_start: 'hide START', hide_end: 'hide END', labels: 'labels', follow_sg: 'follow SG', mode_observe: 'Observe', mode_debug: 'Debug stream', current_sg_btn: 'SG courant', display:'Affichage:', mode:'Mode:' },
  modal: { process_title: 'Processus —' },
  status: { panel_title:'Statut & métriques', running: 'Actif', starting: 'Actif', failed: 'En échec', completed: 'Terminé', canceled: 'Annulé', idle: 'En veille', unknown: 'En veille' },
  io: { title: 'Entrées/Sorties du nœud', in: 'IN', out: 'OUT', error: 'ERREUR' },
  config: { title:'Configuration du process', general:'Général', params:'Paramètres', docs:'Documentation', doc_title:'Titre', doc_desc:'Description', none:'Aucune configuration disponible' },
  graph: { error_title:'Graphe', unavailable:'Graphe indisponible', aria_label:'Graphe Mermaid', mermaid_error_prefix:'Mermaid — ', render_error:'erreur de rendu' },
  node_menu: { aria_actions:'Actions nœud', open_sg:'Ouvrir le sous-graphe', run_until:'Run until', break_add:'Ajouter un breakpoint', break_remove:'Retirer le breakpoint', inspect:'Inspecter' },
  control_inputs: { debug_label:'Debug:', node_id:'ID du nœud', when:'Condition', when_always:'always', when_success:'success', when_fail:'fail', when_retry:'retry', run_until:'Run until', break_add:'Ajouter un breakpoint', break_remove:'Retirer un breakpoint' },
  chat: { leader_panel_title:'Leader — Chat', placeholder:'Message...', tools_trace:'Voir traces tools', error_history:'Erreur chargement historique', empty_reply:'(réponse vide)', global:'Chat global', error_history_global:'Erreur chargement historique global', you:'Vous', assistant:'LLM' },
  leader_global: { title:'Leader — Chat global', select_label:'Leader:', select_aria:'Sélectionner un leader', display:'Nom d’affichage', role:'Rôle', persona:'Persona', persona_ph:'Orchestrateur des workers', none_detected:'(aucun leader)' },
  leader_identity_panel: { no_leader:'Aucun leader affecté', error_read:'Erreur lecture identité', refresh:'Rafraîchir', display:'Nom d’affichage', role:'Rôle', persona:'Persona', persona_ph:'Orchestrateur des workers', global_chat:'Global chat', leader_workers:'Workers du leader', loading:'Chargement…', none_attached:'Aucun worker rattaché', error_load:'Erreur de chargement' },
  list: { title:'Workers', view:'Voir' },
  config_editor: { tabs_simple:'Simple', tabs_json:'JSON', beautify:'Beautify', minify:'Minify', validate:'Valider', json_valid:'JSON valide', json_invalid:'JSON invalide', complex_only_json:'Certains champs complexes ne sont modifiables qu’en JSON' },
  leader_section: { edit_identity_hint:"Éditer l’identité (cliquer)" },
  replay: { title: 'Replay (time machine)', load_run:'Charger run', play:'Lecture', stop:'Stop', error_runs:'Erreur chargement runs', error_steps:'Erreur chargement steps', view_node:'Voir ce nœud', live_announce_step:'Lecture step {idx}/{total}: {nodeId}' }
};
