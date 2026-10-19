CREATE TABLE IF NOT EXISTS signed_upload_intents (
    id TEXT PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    request_key TEXT NOT NULL,
    resource_type TEXT NOT NULL CHECK (resource_type IN ('image', 'video')),
    public_id TEXT NOT NULL UNIQUE,
    cloud_name TEXT NOT NULL,
    preset TEXT NOT NULL,
    environment TEXT NOT NULL,
    max_bytes BIGINT NOT NULL,
    issued_at BIGINT NOT NULL,
    asset_id TEXT REFERENCES media_assets(id),
    provider_asset_id TEXT,
    provider_version BIGINT,
    UNIQUE(owner_id, request_key)
);
