-- Additive only. Apply explicitly; never run from a request or app startup.
-- SQLite and PostgreSQL syntax; PostgreSQL/Cockroach acceptance is pending.
CREATE TABLE IF NOT EXISTS media_assets (
    id TEXT PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    provider TEXT NOT NULL CHECK (provider IN ('local', 'cloudinary')),
    storage_namespace TEXT NOT NULL,
    resource_type TEXT NOT NULL CHECK (resource_type IN ('image', 'video')),
    provider_id TEXT NOT NULL,
    delivery_url TEXT NOT NULL,
    source_bytes BIGINT NOT NULL CHECK (source_bytes > 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (provider, storage_namespace, resource_type, provider_id)
);
CREATE INDEX IF NOT EXISTS media_assets_owner_idx ON media_assets(owner_id);
