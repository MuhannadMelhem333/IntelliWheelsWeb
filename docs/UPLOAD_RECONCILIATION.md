# Read-only upload reconciliation inventory

September 23 accounting update: completed signed intents must now retain their full reservation until reconciliation; inventory flags missing/mismatched completed holds as inconsistent. Previous descriptions treating every completed reservation as erroneous are superseded. Owner-only paginated recovery discovery added, but no refund or cleanup operation: see `UPLOAD_RECOVERY_PROGRESS.md`. Combined backend tests now 102 PASS.

Implemented September 22, 2026. This is an operational diagnostic, not a cleanup or quota-refund command. Direct uploads remain disabled.

## Run locally

```powershell
.\.venv\Scripts\python.exe backend/inspect_uploads.py --database backend/intelliwheels.db
```

The tool resolves an existing SQLite file, opens it with `mode=ro` and `query_only`, and reads a single transaction snapshot. It never imports Flask, loads .env, creates tables, contacts Cloudinary, updates usage or deletes anything. Output is aggregate counts/source bytes; it omits account IDs, public IDs, URLs and credentials. Unknown/incompatible schema fails with a generic error and nonzero exit.

## Interpretation

- `ledger`: registered asset count and measured source-byte usage. Does not include historical unregistered listing media or provider transformations.
- `reservations`: pending count/bytes, including proxy uploads with ambiguous outcomes. These still consume allowance.
- `signed_schema_present`: false is supported; the tool does not apply the migration.
- `signed.pending` and `expired_pending`: intents awaiting completion and the subset with signatures at least one hour old. Expiry does **not** prove provider absence or authorize release of reserved usage.
- `signed.completed` and `active_completed`: completed ledger entries and the subset whose original signatures have not expired. Completion does not invalidate a signed capability; this is a replay-risk visibility measure, not an estimate of stored objects.
- `signed.inconsistent`: missing/wrong reservation for pending intents; missing/wrong owner, type, namespace, public ID or byte accounting for completed ledger entries; missing immutable provider identity/version; invalid issue time. Rows can overlap other categories. Investigate using controlled private access; do not repair automatically.
- `unmatched_reservations`: no signed intent exists with the reservation ID. Proxy reservations legitimately fall here; do not label them orphaned or refund them automatically.
- `provider_checked`, `automatic_refunds_allowed`, `automatic_deletions_allowed` are always false. This report cannot establish provider storage state, ownership of historical media, absence of other resource types, or safe deletion.

## Verified locally

Six inventory tests cover schema absence, read-only file-hash preservation, expiration, active completed signatures, ledger mismatch, missing reservation/future timestamp, unmatched proxy usage and nonexistent paths. All 91 backend tests pass. Live read-only inventory: zero ledger assets, zero reservations, no signed schema. This does not mean there are no listing images: the six existing listings predate the enforced ledger.

Files: `backend/inspect_uploads.py`, `backend/test_inspect_uploads.py`, `.gitignore`, this document and roadmap/readiness logs. Rollback: remove only the inspector/test and its ignore exception; no database rollback exists or is needed because nothing was changed.

## Remaining implementation and acceptance

1. Read-only provider inventory with explicit account/environment boundaries, bounded/paginated requests, error-as-unknown handling and immutable identity matching. Live provider is not configured in this preview.
2. Cross-resource replay accounting: inspect all possible namespaces/resource identities, not merely the expected image/video object. Include possible raw-ID/extension behavior in provider acceptance; an expected-type lookup alone cannot prove absence. Keep signed uploads off until enforced provider restrictions or conservative accounting are demonstrated.
3. Persist reviewed reconciliation evidence and recheck after signature expiry plus in-flight processing delay. Do not treat an immediate 404 as proof that an in-flight upload cannot finish.
4. Build recovery UI for pending uploads and safe quota settlement. Any later cleanup requires verified listing/reference accounting, race-safe ownership checks and a documented rollback/recovery policy. No deletion is authorized by this inventory.

These are unfinished Phase 4 tasks, not manual QA alone.

## September 23: bounded provider observation implemented

`backend/inspect_upload_provider.py` now provides the read-only provider observation step. It reads only signed intents matching the configured cloud and an explicit environment, validates their exact generated namespace before any request, and queries image/video/raw `upload` resources by public-ID prefix. Prefix results expose raw-extension variants rather than silently discarding them. Completion identity/version mismatches and unexpected resource types/IDs are counted. No raw metadata, account identifiers, URLs or credentials are printed.

Run only with approved credentials already supplied securely to the process; the command does not load .env or print credential values:

```powershell
.\.venv\Scripts\python.exe backend/inspect_upload_provider.py --database backend/intelliwheels.db --environment staging --query-provider --limit 10 --max-pages 2
```

Requires the signed-intent schema. This command was **not run against a live provider**: the local schema remains unapplied and Cloudinary is unconfigured. Do not apply the schema or enable signed uploads merely to run an empty report.

Request bounds: default ten oldest intents, two pages per resource type, 100 results per page, ten-second request timeout; at most 60 SDK calls by default. Maximum arguments allow 25 intents/five pages (375 calls). These requests consume Admin API allowance; choose small limits for staging. There is no retry loop. More intents/pages mark the report partial; the initial version is a bounded oldest-intent sample, not an account-wide crawler with a resumable cursor.

Timeouts, authentication/rate-limit errors, malformed metadata, repeating cursors/identities and exhausted page bounds mark observations incomplete. `expected_object_not_seen` means only that it was not observed, never that storage is empty. Observed bytes are a lower bound for this prefix/type sample, not billable storage. Empty matches do not authorize refunds. Even complete pagination is not an atomic provider snapshot, cannot rule out late uploads, and covers only recorded intents and the `upload` delivery type.

Exit codes: 0 means the bounded selected scan completed (findings may still exist); 2 means incomplete/truncated; 1 means setup/schema failure. Never use exit 0 as permission to delete, refund or enable signed mode.

Eight additional tests cover all resource types, prefix variants, immutable identity, bounded/repeated pagination, provider errors, malformed responses, scoped read-only database loading, and missing objects. Final combined backend suite: 99 PASS. An initial fixture failed a uniqueness constraint and Windows connection cleanup; corrected using a single-row update and explicit connection closing, then the whole suite passed. Python compilation, CI YAML/wiring validation and whitespace checks pass. CI explicitly includes the new suite. Frontend code is unchanged; its preceding 94 tests/lint/types/build remain the latest frontend results.

Additional files: `backend/inspect_upload_provider.py`, `backend/test_inspect_upload_provider.py`, `.gitignore`, `.github/workflows/ci.yml`, and reconciliation/CI/roadmap/readiness documentation. Rollback removes only this inspector, test, test ignore exception and CI module entry. No database/provider rollback is required because no provider call or data mutation was performed by this work.

Both preview processes restarted September 23; listings HTTP 200, backend healthy and six cars retained. Browser unavailable after connection troubleshooting; visual QA remains pending. Backend is still a development server with the existing development secret warning and unavailable Gemini configuration, not a deployment-ready service.

Next: replay-safe reservation/settlement design and durable recovery, followed by provider acceptance and safe reference-aware cleanup. The new observer detects evidence of replay; it does not prevent replay or fix quota accounting. Signed mode stays OFF, readiness stays 59/100.
