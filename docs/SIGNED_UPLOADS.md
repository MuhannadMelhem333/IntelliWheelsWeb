# Signed upload adapter — September 22, 2026

Status: backend/client integration implemented and tested with mocked provider responses. **Direct uploads are disabled; Phase 4 is not complete.** No Cloudinary configuration or live signed-intent migration was applied.

September 23 correction: completion now retains the full reservation instead of settling it. Ledger usage plus reservation deliberately double-counts the expected asset until verified reconciliation. Expiry does not release it. This prevents repeated completion/new-intent cycles from prematurely recycling quota, but does not bound all cross-resource replay or prove provider cost safety. The provider rollout gates below still apply. Owner-only `GET /api/uploads/recovery` now supports paginated recovery discovery; editor recovery UI is not yet wired. See `UPLOAD_RECOVERY_PROGRESS.md` for current behavior and tests; older settlement descriptions below are superseded by this correction.

## Scope and flow

Listing editor -> `api.ts:prepareListingUpload` -> authenticated `POST /api/uploads/prepare` -> explicit proxy or direct choice -> provider upload -> authenticated completion -> owned ledger ID -> existing listing association.

- With `SIGNED_UPLOADS_ENABLED=False`, preparation returns `mode: proxy` and the existing image/video endpoints retain their validation, ledger, quota and development-only storage behavior. This adds one authenticated preparation request per upload. Deploy backend endpoints before this client integration; old backends without preparation will reject uploads rather than silently downgrade.
- Direct mode also requires `SIGNED_UPLOAD_PRESETS_VERIFIED`, `MEDIA_ASSET_LEDGER_ENABLED`, and `UPLOAD_QUOTAS_ENABLED`, verified provider configuration, separate image/video preset names and a development/staging/production namespace.
- Preparation validates kind/request key, reserves the entire configured format cap, writes an intent in the same transaction and signs server-selected ID, preset, timestamp, formats and `overwrite=false`. Client size, URL and public ID are not trusted. Repeating an owner/request key returns the original intent/signature; completed requests return the completion ID. Concurrent initial duplicates may receive a safe 503 from the unique constraint; retry uses the existing intent without consuming another reservation.
- Completion uses server-to-server provider lookup, not browser JSON. Owner, cloud, public ID, resource kind, delivery type, immutable identity, version, format, bytes and dimensions must match. Videos require finite positive duration at most 120 seconds and positive dimensions (audio-only is rejected). Animated GIF/WebP require frame metadata; missing metadata fails closed.
- Completion locks the owner and rechecks the intent, inserts ledger metadata, settles reserved cap to observed bytes, and marks completion atomically. Repeated completion returns the same asset. No lock is held during provider lookup. PostgreSQL/CockroachDB behavior still needs actual database acceptance.
- `directUpload.ts` allows only the exact HTTPS Cloudinary upload origin and expected resource path. Provider requests omit application authorization and cookies, disallow redirects and time out after 120 seconds. Browser provider response bodies are ignored. Even HTTP/network failures lead to server reconciliation, never automatic proxy fallback.
- Request keys are kept only in a WeakMap keyed by File and session/kind scope. After a provider attempt, retry of that same File/session requests completion only. Reloading/reselecting loses this client retry identity; there is no pending-upload recovery UI yet. A definitely failed provider upload can therefore remain reserved until reconciliation rather than being automatically refunded.
- Signatures expire after one hour; preparation does not extend them. Completion can reconcile an existing asset after signature expiry. Pending usage never expires automatically.

## Mandatory provider rollout gates — NOT satisfied

Cloudinary excludes `resource_type` from upload signatures, and different resource types can share a public ID. The current one-resource reservation and completion lookup **do not account for cross-type replay**. The presets-verified flag alone is not proof that this is safe. Before enabling, demonstrate provider-side rejection of cross-type replay or implement conservative multi-resource reservations and exhaustive reconciliation. Do not enable solely because unit tests pass.

Also verify signed presets reject oversize and disallowed content before storage; enforce dimensions/duration; prohibit unsafe incoming transformations; verify original/observed byte semantics, animated metadata availability, environment separation and overwrite/replay restrictions. Confirm upload CORS, server lookup limits/timeouts and actual account behavior. Rejected completion may still leave a billable object; this adapter does not delete it. Source-byte allowance is not a Cloudinary billing cap.

Primary references: [authentication signatures](https://cloudinary.com/documentation/authentication_signatures), [upload presets](https://cloudinary.com/documentation/upload_presets), [Admin API](https://cloudinary.com/documentation/admin_api), [upload API](https://cloudinary.com/documentation/image_upload_api_reference).

## Schema and rollback

New additive `003_signed_upload_intents.sql` depends on ledger and quota tables. `migrate_media_assets.py --migration signed` supports read-only inspection and explicit backed-up SQLite application, tested only on disposable databases. It is not a production migration framework. No schema DDL runs in upload requests.

Rollback: keep/set `SIGNED_UPLOADS_ENABLED=False`, retaining ledger/quota protections and all existing data. Keep prepare available returning proxy for the integrated frontend. If removing this implementation, remove frontend negotiation before removing its backend endpoints. Never drop intent/reservation/asset rows as rollback: they may represent stored provider objects and usage still requiring reconciliation. Preserve all previous worktree changes.

## Validation and preview evidence

- Frontend: 94 tests PASS, including real API-client mocked-network negotiation/provider/completion and seven direct helper tests; TypeScript and project ESLint PASS.
- Backend: 85 tests PASS (73 journey, eight limiter, four import); signed cases cover gating/auth, server-owned parameters, idempotency, private completion, metadata rejection, expiry, association and migration backup. Provider calls are mocked. Python compilation and Git whitespace checks PASS.
- Initial backend invocation from repository root failed module resolution; rerun from `backend/` passed. This was a runner working-directory error, not an application regression.
- Restricted build failed only fetching Geist/Geist Mono. Network-enabled build PASS, 24 pages. Existing stale Browserslist warning remains; fonts unchanged.
- Frontend `/` and `/listings` HTTP 200; backend restored and health is healthy, six cars returned. Local ledger and quota flags retained; signed flags off. No test data written to the live database.
- Browser discovery returned no available browser. The verification skills therefore could not establish rendering, console, interactive upload or mobile behavior; these remain pending, not passed.

## Manual/provider QA pending

1. With direct mode off, sign in, upload image/video, preview, save, reload and remove gallery items: existing proxy flow and asset IDs remain intact.
2. Repeat in English/Arabic, RTL, light/dark and mobile; layout/copy are unchanged by this patch.
3. In isolated approved staging only, after provider gates above, direct upload sends no app credential to Cloudinary; completion produces the URL/ID saved on the listing.
4. Lose provider/completion responses; retry same selected File: no second provider POST and one ledger row. Verify recovery after reload/reselection separately; UI recovery is unfinished.
5. Reject foreign completion/association, invalid metadata, oversize files, excessive duration and exhausted allowance without local fallback or leaked provider details.
6. Test concurrent prepare/completion and provider timeout/limits on the actual target database/provider. Reconcile abandoned and cross-resource objects before refunding usage.

## Files in this batch

`backend/app/__init__.py`, `backend/app/signed_uploads.py`, `backend/app/upload_quotas.py`, `backend/migrations/003_signed_upload_intents.sql`, `backend/migrate_media_assets.py`, `backend/test_public_journey.py`, `src/lib/api.ts`, `src/lib/directUpload.ts`, `tests/direct-upload.test.mjs`, `tests/api-session.test.mjs`, `tests/auth-provider.test.mjs`, `tests/cookie-api.test.mjs`, this document, `PUBLIC_RELEASE_READINESS.md`, and `ROADMAP_CONTINUATION.md`.

Next: read-only abandoned-upload/provider reconciliation inventory and replay accounting, followed by reviewed recovery/cleanup. Do not perform physical asset deletion without verified ownership/reference accounting. Remaining Phase 4: provider acceptance, recovery UI, cleanup, moderation and live video validation. Readiness remains 59/100; no hosted acceptance credit awarded for gated code.
