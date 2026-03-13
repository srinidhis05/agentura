CREATE TABLE IF NOT EXISTS mcp_user_tokens (
    id SERIAL PRIMARY KEY,
    user_identifier VARCHAR(200) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMPTZ,
    scope TEXT,
    client_id VARCHAR(200),
    client_secret VARCHAR(200),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_identifier, provider)
);

CREATE INDEX IF NOT EXISTS idx_mcp_user_tokens_user ON mcp_user_tokens(user_identifier);
CREATE INDEX IF NOT EXISTS idx_mcp_user_tokens_provider ON mcp_user_tokens(provider);
