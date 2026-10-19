# Upload reservations and account budgets — September 22, 2026

Implemented on the existing authenticated server-mediated upload path and enabled in the local preview. Direct signed uploads are NOT implemented or enabled by this batch.

## Behavior and implementation

- `backend/app/upload_quotas.py:reserve_upload` reserves one slot and measured source bytes before calling storage. Existing ledger usage and pending reservations count together, across images/videos. Different accounts have separate budgets; changing IP addresses does not change account usage.
- Defaults: 100 uploaded assets and 1 GiB of source bytes per account, with no daily reset. Config keys: `UPLOAD_USER_MAX_ASSETS`, `UPLOAD_USER_MAX_BYTES`, `UPLOAD_QUOTAS_ENABLED`. Source-byte accounting is NOT Cloudinary billable bytes, derivatives, bandwidth or total historical storage. Uploads predating the ledger cannot be accounted for automatically. Bounds are provisional development defaults requiring product/staging acceptance before public rollout.
- SQLite uses `BEGIN IMMEDIATE`; PostgreSQL code locks the account row with `FOR UPDATE`. Both reservation and completion use the same locking discipline. No database transaction is held across the cloud upload. PostgreSQL/Cockroach behavior still needs real staging concurrency tests.
- `media_assets.finish_upload` inserts the asset and consumes its matching reservation in one transaction. Missing/mismatched reservations roll back registration. Reservations include owner, resource type and measured source size; arbitrary client lengths/IDs cannot replace them.
- Exceeded budget returns JSON 409 with `code: upload_quota_exceeded` and no-store. Missing schema/database failures return safe 503. Invalid files and unauthenticated requests do not reserve budget. Existing editor error handling displays the API error; frontend was not changed.
- An ambiguous storage or registration failure retains its reservation. With quotas enabled, a cloud exception cannot trigger a second local-storage upload. Pending reservations never expire automatically: the remote object might exist despite a timeout. This is conservative and can lock legitimate users out after repeated failures; manual reconciliation/support is required until the recovery workflow exists. Do not delete reservations merely to make a retry succeed.
- Removing a listing/media reference does not release its upload budget because the object still exists. Reference-aware deletion/reconciliation must come before safe refunds.
- `backend/migrations/002_upload_reservations.sql` is explicit/additive and requires the ledger migration. `backend/migrate_media_assets.py --migration quotas` extends the existing read-only-by-default, backup-required SQLite migration command. No startup/request DDL was introduced.

## Why signed uploads are still pending

Cloudinary documents an hour-long signature validity and excludes `resource_type` from the signed payload. An application reservation timeout alone is therefore not a provider-enforced single-use guarantee. [Official signature documentation](https://cloudinary.com/documentation/authentication_signatures).

The next adapter must pin server-selected IDs, overwrite behavior, environment-specific folders and constrained presets; validate provider-observed immutable identity/version, bytes, type, dimensions and video duration; and make completion/reconciliation idempotent. Preset parameters and precedence must be verified in the actual account before enabling signatures. [Official upload preset documentation](https://cloudinary.com/documentation/upload_presets).

Local `/api/health` reports `cloudinary_enabled: false`. No credentials, provider presets or paid services were provisioned. Mock tests can cover implementation; real signed upload/provider acceptance will require configured isolated Cloudinary access. Never use the previously exposed unrelated chat credential.

## Validation and local enablement

- **80 backend tests pass:** 68 journey/security, eight limiter and four import tests. Python compilation, dependency and whitespace checks pass.
- Seven new tests cover account isolation, byte budgets including pre-quota ledger usage, eight concurrent requests competing for three slots (exactly three succeed), retained ambiguous-failure reservations, image/video shared budgets, completion without reservation, and missing-schema/invalid-file handling. The existing migration test also covers the new migration selection.
- Frontend unchanged; previous 85 tests/lint/TypeScript/production build remain latest, not rerun here.
- Stopped the owned local backend, backed up `backend/intelliwheels.db` to `backend/intelliwheels-before-quotas-20260922-2156.db`, applied the quota migration, then restarted with process-local `MEDIA_ASSET_LEDGER_ENABLED=True` and `UPLOAD_QUOTAS_ENABLED=True`. Source defaults remain false; no hosted setting changed. Six existing cars retained. Backup is private and ignored by Git.
- Frontend localhost:3000 returns 200; backend localhost:5000 serves six cars. Browser/verification skills found no connected browser, so no visual, mobile, RTL or live file-picker acceptance is claimed.

Manual QA: upload below allowance, save/reload; exceed count/bytes and confirm a recoverable error without lost form fields; retry after an ambiguous provider failure and confirm the reservation remains; verify another account still has its own allowance; run multi-worker concurrency on staging; reconcile provider objects before releasing failed reservations. Keep production quotas disabled until configured storage, operational recovery and staging acceptance are verified.

## Files and rollback

New: `backend/app/upload_quotas.py`, `backend/migrations/002_upload_reservations.sql`, this document. Updated: app config, `media_assets.py`, upload routes, migration CLI, journey tests, ledger/upload/readiness/roadmap documentation. Local database changed only by the additive migration, with backup retained.

Restart the local backend with the ledger enabled but quota flag disabled to restore pre-quota behavior; this removes account-budget enforcement and restores the previous development fallback policy. Leave schema, reservation records and backups intact. Do not restore the whole database over newer writes or erase reservations without reconciliation. Code rollback removes only this batch's reservation/locking hooks, config, migration selection and tests together; preserve previous ownership, upload validation and UI work.
