-- Setup script for Trading CLI API database tables
-- Run this directly in the Docker PostgreSQL container

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
    rate_limit INTEGER NOT NULL DEFAULT 60,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_api_keys_key_hash ON api_keys(key_hash);

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id UUID NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
    command_group VARCHAR(50) NOT NULL,
    command_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    parameters JSONB NOT NULL,
    result_path VARCHAR(500),
    result_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_jobs_api_key_created ON jobs(api_key_id, created_at);
CREATE INDEX IF NOT EXISTS ix_jobs_status_created ON jobs(status, created_at);

-- Insert development API key for testing
-- Key: dev-key-000000000000000000000000
-- Hash generated with bcrypt
INSERT INTO api_keys (id, key_hash, name, scopes, rate_limit, is_active, created_at)
VALUES (
    'dev-key-0000-0000-0000-000000000000'::uuid,
    '$2b$12$YourHashHere',  -- This will be replaced by actual hash
    'Development Key',
    '["*"]'::jsonb,
    1000,
    TRUE,
    NOW()
) ON CONFLICT DO NOTHING;
