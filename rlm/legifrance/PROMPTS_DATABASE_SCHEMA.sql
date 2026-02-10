-- Schema SQLite pour la base de donnees des prompts
-- Fichier : sqlite3/prompts.db

CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,           -- 'legal', 'medical', 'financial', 'technical'
    agent_type TEXT NOT NULL,       -- 'planner', 'researcher', 'evaluator', 'corrector'
    version TEXT DEFAULT 'v1',      -- 'v1', 'v2', 'experimental', 'stable'
    prompt TEXT NOT NULL,           -- Contenu complet du prompt
    description TEXT,               -- Documentation du prompt
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    author TEXT DEFAULT 'system',  -- Qui a cree ce prompt
    is_active BOOLEAN DEFAULT 1,    -- Pour desactiver sans supprimer
    usage_count INTEGER DEFAULT 0,  -- Nombre d'utilisations (optionnel)
    last_used_at TIMESTAMP,         -- Derniere utilisation (optionnel)
    tags TEXT,                      -- JSON array de tags (ex: '["juridique","retraite"]')
    UNIQUE(domain, agent_type, version)
);

CREATE INDEX idx_prompts_lookup ON prompts(domain, agent_type, version, is_active);
CREATE INDEX idx_prompts_active ON prompts(is_active);

-- Table de logs d'utilisation (optionnel, pour analytics)
CREATE TABLE IF NOT EXISTS prompt_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    thread_id TEXT,                 -- Thread chat_agent associe
    execution_time_ms INTEGER,      -- Duree execution
    tokens_used INTEGER,            -- Tokens consommes
    success BOOLEAN,                -- Success ou echec
    error_message TEXT,             -- Si echec
    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
);

CREATE INDEX idx_usage_logs_prompt ON prompt_usage_logs(prompt_id);
CREATE INDEX idx_usage_logs_date ON prompt_usage_logs(used_at);

-- Vue pour les prompts actifs (facilite les queries)
CREATE VIEW IF NOT EXISTS active_prompts AS
SELECT 
    id,
    domain,
    agent_type,
    version,
    prompt,
    description,
    created_at,
    updated_at,
    author,
    usage_count,
    last_used_at
FROM prompts
WHERE is_active = 1;

-- Trigger pour mettre a jour updated_at automatiquement
CREATE TRIGGER IF NOT EXISTS update_prompts_timestamp 
AFTER UPDATE ON prompts
FOR EACH ROW
BEGIN
    UPDATE prompts SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
