# Media asset ledger foundation — September 22, 2026

Current status: integrated with listing writes and the editor, tested, and enabled in the local preview process. The source default remains `MEDIA_ASSET_LEDGER_ENABLED=False`; hosted rollout is NOT enabled. Signed uploads, storage quotas and cleanup are still incomplete. The foundation sections below record the earlier implementation; this continuation supersedes their unintegrated/not-applied status.

## Account quota continuation

The existing upload flow now reserves per-account asset/source-byte allowance before storage and consumes it in the asset transaction. Quotas and ledger are enabled together in the local preview following a second additive migration/backup; source/hosted flags remain false. Eighty backend tests pass. Ambiguous cloud failures retain reservations and cannot fall back locally while quotas are enabled. Full behavior, recovery limitations and rollback: UPLOAD_QUOTAS.md. Signed direct uploads and reconciliation remain unfinished.

## Integrated flow and local rollout

- `listingMediaPayload` carries known IDs only for active gallery entries. `ListingEditorView` retains IDs from image/video upload responses, restores them from saved `mediaGallery`, and omits removed entries. API response types and `CarMedia` include optional `assetId`. The Next.js skill was used to preserve the existing route/Client Component boundary; appearance is unchanged.
- `bind_listing_assets` runs after shape/count validation and before car insertion/update. It checks each claimed asset against authenticated owner, exact delivery URL and resource type. Newly added unknown or foreign media is rejected even when only a cover/gallery URL is submitted. Exact owner URLs submitted by older clients are resolved to verified IDs automatically.
- Existing URLs are grandfathered only on the same listing, allowing legacy edits without inventing asset ownership. They cannot be copied into a new listing under enabled enforcement. Invalid claimed IDs never fall back to legacy compatibility. Existing imported read-only `image_urls` remains outside this writable contract.
- Verified IDs are stored inside the existing `media_gallery` JSON alongside the listing's other values in the same INSERT/UPDATE transaction; no new association table or separate association commit is needed. One owner's asset may be referenced by multiple listings. This is not exclusive association or a quota reservation. Concurrent edits still have the existing last-write-wins behavior and require staging tests.
- Local gated uploads now return/store an absolute delivery URL using the local request origin so the API receipt and frontend preview URL agree. Cloud URLs are unchanged. No external URL is fetched by the association validator.
- Removing a reference does not remove its ledger record or physical/cloud object. Reference-aware cleanup remains a separate deliverable; no asset deletion permission is inferred from a URL.

Validation: **73 backend tests** (61 journey/security, eight limiter, four import), **85 frontend tests**, full/changed-file ESLint, TypeScript, compilation, dependency and whitespace checks pass. Production build passed with network access for existing fonts (24 pages; existing Browserslist warning). API tests exercise upload/create/reload/edit/removal, foreign-owner/URL-only bypass, ID/type/URL mismatch, no-write rejection, and legacy continuation. Payload tests verify ID propagation and removal. These are Flask/SQLite and pure frontend tests, NOT a browser E2E pass or actual Cloudinary/PostgreSQL acceptance.

Local rollout performed after checks: stopped the owned backend process, applied the additive migration to `backend/intelliwheels.db` with backup `backend/intelliwheels-before-ledger-20260922-1610.db`, then restarted the development backend with `app.config['MEDIA_ASSET_LEDGER_ENABLED']=True`. Existing six cars retained. Backup is ignored by Git and must be retained privately. No production data or hosted setting was touched. The flag is process-local, not a committed default or environment-file change; an ordinary restart without that override disables enforcement.

Browser discovery returned no connected browser. Verification skills therefore could not establish rendering, picker interactions, console status or mobile/RTL correctness. Manual QA: sign in, upload an image and video, create/reload/edit the listing, remove each media type and refresh; confirm IDs remain with retained entries and old media does not return. With a second user, try associating the first user's asset ID or exact URL and expect rejection. Edit an existing URL-only listing and retain its media successfully. Verify errors retain the draft. Check English/Arabic and desktop/mobile. Real cloud persistence and staged concurrent/failure behavior remain pending.

Continuation files: `backend/app/listing_media.py`, `backend/app/media_assets.py`, `backend/app/routes/cars.py`, `backend/test_public_journey.py`, `src/lib/types.ts`, `src/lib/api.ts`, `src/lib/listingMediaPayload.ts`, `src/components/listings/ListingEditorView.tsx`, `tests/listing-media-payload.test.mjs`, and ledger/upload/readiness/roadmap docs; local SQLite plus private backup changed only by the additive migration.

Rollback: restart the local backend without the process-level flag override to disable association enforcement. Keep the additive table and backup; do not restore the whole backup over subsequent user writes. For code rollback, remove only this continuation's `bind_listing_assets` integration, asset-ID validation/propagation, and tests together; preserve the prior ledger and upload safeguards. No physical media was deleted. Next: signed upload reservations/completion with per-user quotas and staged provider validation.

## Architecture and API

- Explicit additive schema: `backend/migrations/001_media_assets.sql`. A random asset ID records authenticated owner, provider, storage namespace, resource type, provider ID, delivery URL, source byte count and creation time. A unique provider/namespace/type/provider-ID key prevents a duplicate identity being registered to another owner. Owner index supports later accounting. No historical URL ownership is inferred.
- `backend/app/media_assets.py:check_ledger_ready` checks the table before upload storage when enabled. No table creation or alteration occurs in requests/startup. Missing schema returns safe 503 before storage.
- `finish_upload` commits server-observed results before returning the additional `assetId` field. Owner comes from the authenticated session, not multipart fields. Source bytes come from stream validation, not a client-supplied length. Existing success fields remain unchanged; with rollout disabled responses remain unchanged and the table is not queried.
- `GET /api/uploads/assets/<asset_id>` requires authentication and scopes its query to the current user. Invalid, missing, foreign-owned and disabled-rollout records return the same 404 body. Successful metadata responses use `Cache-Control: no-store`; authentication failures return 401. No owner IDs, private storage metadata or secrets are exposed. Read-only endpoint budget is 60/minute/IP using the existing limiter.
- Database registration failure returns safe 503 without URL/success, local fallback, retry or deletion. The already stored object can be orphaned: a future reconciliation workflow is required. Duplicate provider identity does not overwrite the ledger owner; it does NOT undo a provider-side overwrite. Current uploads still rely on provider-generated unique IDs.
- The local namespace is `local`; Cloudinary namespace is the configured cloud name. Source byte counts do not represent transformed/rendition storage costs. Database rows are not a storage reservation or a billing quota.

## Migration and rollout

`backend/migrate_media_assets.py` is a standalone SQLite-only command: no Flask import, `.env` loading, schema initialization or automatic production connection. Default is read-only inspection of an explicitly named existing database. Applying requires an explicit new backup destination. Existing backup files/source paths are refused. Backup uses SQLite's backup API; all connections are explicitly closed, including on Windows. Apply uses an explicit transaction and preserves existing tables/data. Stop the application for an actual migration and keep the backup; schema checks alone are not full schema version management.

Example for a disposable development database (NOT executed on the preview database):

```powershell
.\.venv\Scripts\python.exe backend/migrate_media_assets.py --database C:\temp\fixture.db
.\.venv\Scripts\python.exe backend/migrate_media_assets.py --database C:\temp\fixture.db --apply --backup C:\temp\fixture-before-ledger.db
```

The source must contain the existing users table. The SQL is written in shared SQLite/PostgreSQL syntax, but only SQLite execution has been tested. PostgreSQL/Cockroach staging must validate types, constraints, privileges, transactions and restore before a reviewed hosted migration. Do not run the SQLite command against hosted databases. Applying `IF NOT EXISTS` to an incompatible pre-existing table is not a schema upgrade; inspect the schema first.

Enable the Python application config flag only after applying the migration and staging acceptance; it is deliberately not automatically enabled by an environment variable or this patch. No instance configuration was changed. This ledger alone must not be marketed as complete ownership enforcement: listing mutation still accepts the existing URL contract, and the frontend does not yet persist/use asset IDs.

## Verification

- 58 journey/security tests + eight limiter tests + four import tests: **70 backend tests pass**. Python compilation and dependency checks pass.
- Seven new tests cover disabled compatibility/no automatic schema, missing-migration rejection before storage, forged multipart identity rejection, provider-identity collision, video provenance, private lookup, database registration failure without fallback, read-only migration inspection, backup contents, safe reapplication and refusal to overwrite backups/create missing source files.
- Tests use disposable SQLite and mocked Cloudinary. A Windows handle-cleanup test initially failed; explicit connection closing fixed it and the full suite passed afterward.
- Frontend untouched: previous 83 tests/lint/TypeScript/network-enabled production build remain the latest frontend baseline, not rerun for this backend-only batch.
- Both previews respond; six cars retained. No browser, hosted database or actual Cloudinary acceptance is claimed. Existing safe failure-event log lines during injected-failure tests are expected.

## Remaining implementation and manual acceptance

1. Add an atomic, owner-scoped listing/asset association contract, preserving legacy URL compatibility without treating URLs as owned assets. Carry new IDs through the editor.
2. Add reservations and transactional per-user quotas before signed requests; use server-defined folders/parameters, not arbitrary client public IDs.
3. Verify direct-upload completion against provider metadata, including immutable identity/version, type, dimensions, duration and bytes. Make completion/retry idempotent.
4. Implement reference-aware deletion/orphan reconciliation; never destroy provider objects using an arbitrary submitted URL/public ID. Define retention and failure retry behavior before enabling cleanup.
5. Run staged two-user upload/lookup/association tests, provider outages, database commit failures, concurrent requests, restart persistence and restore verification. Confirm existing listing upload UI remains compatible with the added response field.

## Files and rollback

New: `backend/app/media_assets.py`, `backend/migrations/001_media_assets.sql`, `backend/migrate_media_assets.py`, this document. Updated: app config, upload routes, upload validator (returns measured bytes), journey tests, upload/roadmap/readiness docs.

Keep the rollout flag false to retain existing behavior. To revert code, undo only this batch's ledger imports/calls/config, return-size addition and new tests/files; preserve prior upload validation, rate limits, auth and frontend work. An applied additive table may safely remain unused; do not drop it or restore a whole old database over newer writes. Production rollback/schema deletion/restore requires a separately approved data-safe procedure. No live migration was performed in this run.
