-- Explicit additive migration; requires 001_media_assets.sql.
-- Pending reservations are NOT automatically expired: a remote upload may exist.
CREATE TABLE IF NOT EXISTS upload_reservations (
    id TEXT PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    resource_type TEXT NOT NULL CHECK (resource_type IN ('image', 'video')),
    source_bytes BIGINT NOT NULL CHECK (source_bytes > 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS upload_reservations_owner_idx ON upload_reservations(owner_id);
