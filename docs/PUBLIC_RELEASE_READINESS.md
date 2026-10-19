# Public release readiness — September 19, 2026

Status: **NOT READY FOR PUBLIC DEPLOYMENT**. Local preview is available; passing tests do not remove the blockers below.

September 24 priority update: focus on MVP launch gates rather than finishing the whole modernization roadmap. Canonical current plan: `MVP_LAUNCH_PLAN.md`. Core-only versus all-features launch scope still awaits owner choice; no features removed. Fixed documented API environment variable support, removed dormant build-import hook, and added secret-safe configuration preflight. 109 frontend/113 backend tests pass. Hosted acceptance remains unverified; historical progress is not being rebased to create an artificial percentage increase.

## Current overall estimate: 60 / 100

Latest staging-readiness continuation: password-reset SMTP uses a 10-second socket timeout and verified STARTTLS; 117 backend tests pass. Vercel connected discovery returned no accessible teams, so no staging project was identified. Real provider/browser acceptance remains pending; no readiness increment. See `MVP_STAGING_VERIFICATION.md` for confirmed database fallback risks requiring staged correction and the remaining acceptance checklist.

Latest video validation: real ffprobe metadata inspection now precedes storage/quota on the enabled proxy path; 109 backend tests pass, including actual short/overlong MP4 API checks. Local user tools installed and preview restarted. Awarded one media implementation point, no hosted/browser acceptance credit. Backend runtime must provide ffprobe before deployment; absent tool safely rejects video uploads. Full decoding/moderation remain incomplete. See `VIDEO_UPLOAD_VALIDATION.md`.

Latest active upload fix: partial batch failures no longer discard successful files/asset IDs, overlapping batches are blocked, and primary-image capacity is enforced. 106 frontend tests plus types/lint/build pass. No provider rollout or browser acceptance credit; backend unchanged. `UPLOAD_BATCH_RELIABILITY.md` records remaining proxy-video duration validation and provider-reconciliation blockers.

Latest editor integration: upload recovery discovery, verified preview and explicit gallery addition now implemented with media limits and stale-session guards. 101 frontend/102 backend tests, lint/types/build pass. Direct mode remains OFF; provider-safe settlement and browser/provider acceptance are unresolved, so no readiness increment. See `UPLOAD_RECOVERY_PROGRESS.md` for current UI behavior and manual QA.

Latest accounting correction: signed completion no longer releases replay-related allowance; owner-only paginated recovery API implemented. 102 backend tests pass. Recovery UI and verified settlement remain unfinished; retained holds intentionally over-count usage and are not a complete replay/billing solution. Direct mode stays disabled, no additional launch credit. Details: `UPLOAD_RECOVERY_PROGRESS.md`.

September 23: bounded, scoped provider observation implemented with image/video/raw detection and conservative unknown handling; 99 backend tests pass and CI includes them. No actual provider acceptance or mutation performed, direct uploads still disabled. Previews restarted, six cars retained, interactive browser unavailable. No readiness increment for diagnostics alone; replay-safe quota accounting/recovery and hosted acceptance remain unfinished. See `UPLOAD_RECONCILIATION.md`.

Latest continuation: read-only upload inventory detects pending/expired/active-completed signatures and accounting mismatches without changing data. 91 backend tests pass. CI now includes the 94 frontend and 91 backend regression tests plus test-only dependencies; hosted execution/enforcement remains unverified. No additional readiness credit for unrun hosted gates. See `UPLOAD_RECONCILIATION.md` and `CI_REGRESSION_GATES.md`. Direct upload/provider acceptance and cleanup remain incomplete.

Latest signed-adapter integration: prepare/provider/completion is wired through the listing API client, with owned verified metadata and conservative retry handling; 94 frontend and 85 backend tests, lint, TypeScript and network-enabled build pass. Direct mode remains OFF because provider preset enforcement and unsigned-resource-type replay accounting are not accepted. No extra readiness credit; browser unavailable. Both previews respond and six cars remain. See `SIGNED_UPLOADS.md` for exact remaining gates, migration and rollback.

Latest quota batch: account reservations/source-byte limits integrated and locally enabled after backup, including concurrency and conservative failure handling; 80 backend tests pass. One additional media implementation point, no hosted/provider acceptance credit. Pending reservations require reconciliation; signed uploads remain unfinished and local Cloudinary is unconfigured. Details: UPLOAD_QUOTAS.md.

Latest September 22 integration: editor IDs and owner-checked listing writes complete; 73 backend and 85 frontend tests, lint/types/build pass. Additive local migration applied after backup and local enforcement enabled, preserving six cars. Awarded one marketplace and one media implementation point. Browser and hosted acceptance still pending; signed uploads/quotas/cleanup incomplete. See MEDIA_ASSET_LEDGER.md.

September 22 ledger foundation: explicit migration/backup tool, authenticated upload provenance and owner-scoped lookup implemented behind a disabled flag; 70 backend tests pass. No live schema/hosted rollout performed. No additional readiness credit until association and the complete upload flow are verified. See MEDIA_ASSET_LEDGER.md. Previous frontend checks were not rerun for this backend-only batch.

This is an engineering estimate of weighted launch deliverables, not a measured probability of safety, a calendar forecast, or permission to deploy. Unverified hosted behavior receives limited credit. Scores may fall if testing finds defects; small test additions do not automatically raise the estimate. The user requested this overall estimate alongside next steps in future reports.

| Launch area | Credit / weight | Evidence and remaining gate |
| --- | --- | --- |
| Public frontend and shared UI | 18 / 20 | Route/shell migrations and automated checks implemented; actual mobile/RTL/browser acceptance pending. |
| Core marketplace flows | 11 / 15 | Upload-to-listing ownership/save/reload/removal API flow and editor payload tested; isolated listing/favorites/messaging journey passes; browser acceptance pending. |
| Authentication and security | 15 / 20 | Access control, password/session hashing, gated cookies/CSRF, baseline headers, optional atomic shared quotas and explicit trusted-proxy handling implemented/tested; real Redis/proxy acceptance, cookie rollout and strict script CSP incomplete. |
| Production data and recovery | 2 / 10 | Local data path and isolated tests work; production-compatible migrations, staging and restore verification pending. |
| Durable media and upload safety | 9 / 10 | Image checks, video metadata/duration checks with real-file API tests, ledger/editor ownership and account budgets integrated locally; complete decode/moderation, signed replay safety, storage reconciliation, cleanup and real cloud acceptance pending. |
| Email, AI and operational services | 2 / 10 | Reset URL/error handling improved; real delivery/provider controls and operational acceptance unverified. |
| Release QA, deployment and monitoring | 3 / 15 | Build and automated baseline pass; browser/staging acceptance, operational monitoring and approved deployment still pending. |
| **Total** | **60 / 100** | **Release blockers remain regardless of score.** |

Latest September 22 follow-up: listing media limits/types/URLs and partial-edit checks now enforced; removed cover/video values no longer survive editor saves; query-string URLs preserved. 63 backend and 83 frontend tests pass, lint/types/compilation pass, production build passes with font network access. One additional implementation point only: no asset-ownership, hosted persistence or storage-quota credit. Browser unavailable; Phase 4 remains incomplete. Details: UPLOAD_SAFETY_PROGRESS.md.

September 22 upload batch: 57 backend tests pass, Python compilation and dependency checks pass. Implemented size/dimension/frame limits and non-development fail-closed persistence; added three media implementation points, not hosted acceptance credit. Live frontend 200/backend six cars. No browser connected. Exact compatibility changes, manual QA, remaining Phase 4 work and rollback: UPLOAD_SAFETY_PROGRESS.md. Frontend validation below is historical, not rerun for this backend-only batch.

Latest shared-limiter batch: optional Redis sliding windows with bounded client timeouts/fail-closed 503 behavior, and peer-allowlisted forwarded IP/scheme trust. 51 backend tests pass using local Lua emulation and Flask fixtures. Added three implementation points, no hosted acceptance credit. No service provisioned or hosted setting changed; live preview still uses local limits and trusts no proxies. See SHARED_LIMITER_PROXY_SETUP.md for the required real-service acceptance and rollout plan.

Latest security batch: baseline frontend/API CSP, HTTPS HSTS behavior and corrected bounded/thread-safe endpoint budgets with broader costly-route coverage. 80 frontend entries and 44 backend tests pass; live headers verified. Added three security implementation points, not hosted acceptance credit. Shared multi-worker limits and trusted proxy topology are mandatory outstanding release gates. See SECURITY_HEADERS_RATE_LIMITS.md; no paid service or deployment change.

September 19 password follow-up: new password writes use Werkzeug's maintained default, and successful logins upgrade the confirmed legacy hash format transactionally. 36 backend tests pass. This earns one implementation point; no production rollout is claimed. Staging/capacity limitations and rollback: PASSWORD_HASH_MIGRATION.md.

Latest session milestone: 13 mounted AuthProvider scenarios cover startup, logout/races, focus/storage rechecks, password rotation/reset and verification timeout. They run real provider/API code with simulated DOM and mocked fetch, not real cookies. Both cookie rollout gates remain disabled. Canonical reset-origin separation is complete; SMTP delivery is not verified. The previous production build passed with network access for existing fonts. See SESSION_SECURITY_PROGRESS.md for current validation and scope.

Priority next steps: complete browser/cookie and staging acceptance with a safe legacy-session cutover; finish remaining security work; validate persistent media and production database/backup behavior; then complete operational configuration and end-to-end release QA. Production deployment/DNS/destructive data changes remain approval-only.

## Historical checkpoints (counts and unfinished lists below describe earlier patches)

Validation for this patch: 38 frontend test entries, isolated API journey, TypeScript, project ESLint, production build and Git whitespace check pass. Final live checks: frontend HTTP 200; backend six cars. Existing Browserslist-age and Git line-ending notices remain.

## Confirmed working in isolated API smoke test

`backend/test_public_journey.py` creates a disposable SQLite database, registers seller/buyer/outsider fixtures, and exercises public search/detail, listing create/edit/delete, favorites, message delivery, conversation privacy, owner-only mutations, and logout invalidation. All assertions pass. It does not touch the live preview database, send email, call AI, upload to cloud services, or prove PostgreSQL compatibility/browser behavior.

Run `.venv/Scripts/python.exe backend/test_public_journey.py -v` separately from broad unittest discovery because importing the app package initializes its database. The script sets isolated configuration before that import and suppresses legacy auth output containing sensitive response details.

## Fixed: newly uploaded local media URL

Flask's fallback upload response contains `/api/uploads/...`. On a separate frontend origin this previously pointed images/videos at Next.js rather than Flask. `resolveUploadUrl` now resolves this specific response path against the configured API origin before the editor previews or saves it. Absolute Cloudinary URLs and unrelated frontend paths stay unchanged. Three pure tests cover resolution; existing historical listing URLs are not migrated. No API/upload authorization changes were bundled into this frontend fix.

## Release blockers, in priority order

Canonical password-reset URL is now separated from the CORS list and targets `/account`. Optional backend PASSWORD_RESET_ORIGIN overrides the first-configured-origin fallback; invalid destinations fail startup validation. 32 backend tests pass. No hosted settings or email delivery were changed/verified. Cookie cutover and browser/staging verification remain outstanding.

September 18 continuation: gated frontend cookie transport and session lifecycle are implemented and covered by 47 frontend test entries plus 29 backend tests. Final lint, TypeScript and production build pass. Both cookie gates remain disabled pending canonical reset-origin separation, mounted/browser acceptance and staged-origin verification. The live preview remains on its previous transport; do not mistake passing helper tests for completed browser migration. See `SESSION_COOKIE_MANUAL_QA.md` and `SESSION_SECURITY_PROGRESS.md`.

Cookie/CSRF foundation now exists behind `COOKIE_AUTH_ENABLED=False`, tested in isolation only. The live app has NOT switched from bearer storage. Do not enable before the remaining coordinated frontend/lifecycle/browser work in `SESSION_SECURITY_PROGRESS.md`. This is partial implementation, not release completion.

Session follow-up: returning Google-user SQLite compatibility fixed; newly issued signup/login/Google sessions store versioned hashes, with replay-rejection tests. Legacy raw sessions and browser bearer storage remain temporarily. Cookie/CSRF migration is not enabled. See `SESSION_SECURITY_PROGRESS.md` for remaining work and rollback constraints; this does not make deployment ready.

AI disclosure follow-up: provider exception messages and malformed vision output are no longer logged or interpolated into failure responses; search query logging removed. Models, successful outputs and fallback logic are preserved. Seventeen journey/security tests plus four import tests pass using mocked AI only. Live Gemini functionality/cost controls and infrastructure telemetry remain unverified; no credentials were added. See roadmap for files and rollback.

Non-AI error disclosure follow-up: request-wide unexpected failures use safe JSON 500 responses; intentional HTTP errors remain intact. Non-AI route logs omit dynamic private data/tracebacks, and failure responses no longer return raw database exceptions. Health error strings are generic. Thirteen isolated journey/security tests and four import tests pass, with Python compilation and whitespace checks. AI-service caught-error output, infrastructure logs, startup/teardown exceptions and telemetry remain outside this completed slice. See roadmap for exact files, API error-message changes and rollback.

Logging follow-up: authentication route logs no longer print session prefixes, usernames, recipients or raw exceptions. Explicit database logs also omit raw exceptions. Nine isolated journey/security/logging tests and four import tests pass; Python compilation passes. This is not blanket log redaction: uncaught framework traces, other routes and infrastructure access logs remain to be audited. API contracts and session storage are unchanged. See the roadmap log for files and rollback.

1. **Anonymous writes — fixed:** `cars.py:create_car` and `system.py:upload_image/upload_video` require a valid existing session before processing input or storing files. Missing, invalid, expired and revoked sessions receive HTTP 401. Public reads and unauthenticated OPTIONS remain available. Session and upload-hardening work below is still required.
2. **Sessions:** browser-readable tokens remain; secure cookies, CSRF, token hashing/rotation, and comprehensive backend log redaction are still required by Phase 2.
3. **Persistent uploads:** production local-filesystem fallback and file validation/quota limitations remain. Correct URL resolution is not durable storage or upload security.
4. **Browser acceptance:** complete sign-in, listing/upload, favorites, messaging, language/theme/mobile and failure tests in a connected browser. API smoke testing cannot establish rendering or user interaction correctness.
5. **Production data:** PostgreSQL/CockroachDB schema and migration/restore compatibility require validation against a safe staging database.
6. **Operational configuration:** production secret, persistent storage, matching frontend/backend origins, email delivery, and feature-appropriate AI credentials/limits must be verified. No exposed chat credential has been used.

Public deployment, DNS, paid services and production data/environment changes remain approval-only. The approved frontend design and cache fix are retained.

## This continuation's files and rollback

Access-control follow-up: changed `backend/app/routes/cars.py`, `backend/app/routes/system.py`, `backend/test_public_journey.py` and the two release/roadmap documents. Five isolated journey/security tests, four import tests, Python compileall, 38 frontend test entries and Git whitespace checks pass. Upload fixtures validate storage/auth contracts, not media decoding. Frontend lint/typecheck/build last passed in the preceding frontend patch, not rerun for this Python-only change. Live frontend returns 200 and backend is healthy with six cars; browser acceptance remains pending.

API change: three POST endpoints now return 401 without a valid bearer session; authenticated response contracts and database schema are unchanged. Rollback only the auth guards/import and optional-owner-assignment change, together with corresponding test assertions. This would reopen anonymous writes and is unsafe for public deployment. Preserve prior dangerous-endpoint removal in `system.py`, all other completed changes and preview data.

`src/lib/uploadUrl.ts`, `src/lib/api.ts`, `tests/upload-url.test.mjs`, `tests/api-session.test.mjs`, `backend/test_public_journey.py`, `.gitignore`, and this document plus the roadmap log.

Rollback only the upload-response URL normalization and its helper/test import together. The smoke test and its narrow Git-ignore exception are independently removable. Preserve earlier code changes and all preview data. No commits, deployments or schema migrations were performed.
