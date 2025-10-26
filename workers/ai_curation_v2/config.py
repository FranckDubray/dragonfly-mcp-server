# Worker config for ai_curation_v2 — unique source of truth for init variables
# Move/keep all runtime context variables here (values) and their human docs below.

CONFIG = {'http_timeout_sec': 160,
 'llm_model': 'gpt-4o-mini',
 'sonar_model': 'sonar',
 'llm_temperature': 0.3,
 'quality_threshold': 7,
 'max_retries': 3,
 'primary_sites': ['https://openai.com/index',
                   'https://www.anthropic.com/news',
                   'https://blog.google/technology/ai',
                   'https://deepmind.google/discover/blog',
                   'https://ai.meta.com/blog',
                   'https://aws.amazon.com/blogs',
                   'https://azure.microsoft.com/blog',
                   'https://developer.nvidia.com/blog',
                   'https://stability.ai/news',
                   'https://arxiv.org'],
 'db_file': 'worker_ai_curation_v2.db'}

# Descriptions lisibles par l’outil (py_orchestrator.operation=config → champs "docs")
CONFIG_DOC = {
    "http_timeout_sec": "Timeout HTTP (sec) pour les appels MCP (call_llm, etc.). Défaut 30s.",
    "llm_model": "Modèle LLM principal utilisé pour le scoring et le formatage du rapport.",
    "sonar_model": "Modèle Sonar utilisé pour la validation/collecte.",
    "llm_temperature": "Température de génération LLM.",
    "quality_threshold": "Seuil de score minimal pour considérer la curation satisfaisante.",
    "max_retries": "Nombre maximal de tentatives de re‑scoring si la validation échoue.",
    "primary_sites": "Liste des sites officiels prioritaires pour l’enrichissement/validation.",
    "db_file": "Nom du fichier SQLite pour persister l’état et les rapports.",
}
