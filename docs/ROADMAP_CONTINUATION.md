# Roadmap continuation — 2026-09-07

## MVP staging discovery and SMTP reliability — September 24

Added socket timeout and verified STARTTLS before SMTP credentials/reset links; four regression tests cover verification, certificate rejection, timeout privacy and absent configuration. All 117 backend tests pass; compilation/whitespace checks pass. Frontend unchanged, prior checks remain the latest. Connected Vercel lookup returned zero accessible teams; no local project link. Local frontend/backend respond with six cars, backend restarted. No provider calls for email, hosted settings, deployment or data changes. Files, rollback and exact remaining acceptance: `MVP_STAGING_VERIFICATION.md`. Overall remains 60/100; next obtain the isolated staging target/access and complete the core marketplace journey. Confirmed database TLS downgrade/driver fallback risks remain unchanged pending staged compatibility validation.

## MVP priority / configuration launch-blocker batch — September 24

Owner requested faster minimum-viable launch delivery. Do not resume optional automatic-cleanup/signed-upload work before core staged acceptance. Feature deferral choice remains pending; no feature removed. Fixed ignored NEXT_PUBLIC_API_URL (documented/CI variable), removed dormant build-time SQL import hook whose script is absent, added standalone secret-safe release configuration preflight plus tests and CI inclusion. 109 frontend/113 backend tests, types/lint/compilation/YAML/whitespace pass. Full batch details/rollback and staged acceptance gates: `MVP_LAUNCH_PLAN.md`. Historical overall estimate remains 60/100; MVP scope is not yet rebased. Next: obtain/inspect isolated staging service readiness and run the core user journey, not more optional architecture work. No hosted settings/deployment/data mutations performed.

## Active video upload validation — September 23

Implemented bounded ffprobe metadata validation before quota/storage, rejecting non-video/missing or overlong duration/invalid dimensions and failing 503 when validator unavailable. Installed user-scoped FFmpeg via WinGet, ran real generated short/overlong videos through disposable API fixtures, and restarted preview with trusted binary path. 109 backend tests PASS; CI now installs/requires video tools. Initial sandbox execution denied; approved execution passed. No frontend, hosted or data migration changes. Files/QA/limitations/rollback: `VIDEO_UPLOAD_VALIDATION.md`. Readiness 60/100 (+1 active media implementation point), no hosted acceptance credit. Next: media reference accounting before safe cleanup; signed replay settlement remains gated. Runtime ffprobe provisioning is required before deployment.

## Enabled upload-flow partial failure fixed — September 23

Rather than enabling unaccepted signed settlement, fixed a confirmed active-path bug: one failed file discarded successful siblings from the draft. All-settled uploads now retain successful URLs/IDs, give localized partial-failure feedback, block overlapping batches, count the primary image in the cap, and discard stale session/listing responses. 106 frontend tests, TypeScript, lint and build pass. Backend/provider/schema unchanged; no quota refunds/deletion. Files/rollback/manual QA: `UPLOAD_BATCH_RELIABILITY.md`. Next: proxy-video playback/duration validation gap; provider replay acceptance remains external and direct uploads stay disabled. Readiness remains 59/100.

## Listing editor upload recovery integrated — September 23

Typed discovery/completion API calls, explicit recovery/preview/add panel, English/Arabic/RTL/theme support and pure bounded gallery merge now wired into the editor. No request on mount or automatic attachment; functional updates preserve owned IDs and media caps. Session-keyed panel and revision guards discard stale results. 101 frontend/102 backend tests, TypeScript, project lint and production build pass; mounted JSDOM tests are not visual/provider acceptance. Signed mode remains OFF. Both previews respond with six cars; backend refreshed for current code. Files/rollback/manual QA: `UPLOAD_RECOVERY_PROGRESS.md`. Next: audited replay accounting/settlement and provider acceptance. Readiness stays 59/100; no hosted acceptance credit.

## Retained signed-upload allowance and private recovery discovery — September 23

Fixed premature reservation release at completion: full owner/kind/cap hold remains alongside ledger usage until verified reconciliation, including after expiry. Added gated owner-only paginated GET recovery endpoint with no-store, safe errors and no provider activity. Inventory updated for retained completed holds. 102 backend tests pass; no frontend/schema/provider/production changes. This is conservative over-counting, not complete cross-resource replay protection. Recovery UI remains unfinished. Exact files, limitations and rollback: `UPLOAD_RECOVERY_PROGRESS.md`. Next: explicit editor recovery/preview integration, then audited settlement; keep direct uploads off. Readiness remains 59/100.

## Bounded provider observations — September 23

Implemented standalone read-only provider observer for recorded signed intents, cloud/environment-scoped and namespace-validated. Bounded pagination across image/video/raw detects unexpected types/ID variants and completed immutable-identity mismatches; errors and incomplete scans remain unknown. No live provider calls, refunds, deletion, schema application or signed-mode enablement. Eight added tests; 99 backend tests pass after fixing test fixture uniqueness/Windows connection cleanup. Compilation/YAML/whitespace checks pass; CI includes this suite. Exact files, bounds, limitations and rollback: `UPLOAD_RECONCILIATION.md`. Both preview servers restarted and respond, with six cars retained; browser unavailable. Readiness remains 59/100. Next: replay-safe quota reservation/settlement and durable recovery; the observer does not itself prevent replay.

## Read-only upload inventory and CI regression wiring — September 22

Added standalone read-only SQLite upload inventory with consistent snapshots, aggregate-only output, pending/expired/active-completed intent counts and ledger/reservation mismatch detection. No provider lookup, automatic refund, schema change or deletion. Six new tests; 91 backend tests pass. Live database has zero ledger assets/reservations and no signed schema; historical six listings remain. Details/files/rollback: `UPLOAD_RECONCILIATION.md`.

Then wired the existing frontend/backend regression suites into GitHub CI, with backend test dependencies and explicit isolated modules. No deployment commands/settings or branch triggers changed. Local frontend 94 and backend 91 tests pass; hosted CI not yet run. Details/files/rollback: `CI_REGRESSION_GATES.md`. Readiness stays 59/100 pending provider, browser and hosted acceptance. Resume with bounded provider reconciliation/replay accounting; direct mode remains disabled.

## Signed upload adapter/client integration — September 22

Implemented gated prepare and owner-scoped completion, explicit signed-intent migration, full-cap reservations, provider-observed metadata validation and atomic settlement. Listing API now negotiates proxy/direct and uses credential-free provider POST with completion-only retry after ambiguous outcomes. 94 frontend and 85 backend tests pass; lint/TypeScript/compilation/whitespace and network-enabled build pass. Initial restricted build failed only Google Fonts. Frontend and backend previews respond, six cars retained; browser unavailable. Signed mode remains off, schema not applied live, provider calls mocked. Cross-resource replay and preset enforcement remain release gates, not solved by completion validation. Full files, limitations and rollback: `SIGNED_UPLOADS.md`. Readiness stays 59/100. Resume with read-only reconciliation inventory/replay accounting, then recovery and safe cleanup; no production/provider changes or deletion performed.

## Account quota integration — September 22

Existing image/video uploads now reserve account count/source bytes before storage, including in-flight/previous-ledger usage, and consume reservations in the ledger transaction. Shared owner locking protects concurrent requests; failed/ambiguous uploads keep allowance reserved and cannot trigger local fallback. Seven new tests plus migration coverage; 80 backend tests/compilation/dependencies/whitespace pass. Additive quota migration locally applied after backup; preview process has both flags true, hosted/source defaults unchanged. Six cars preserved, both previews respond. Frontend unchanged, browser unavailable. Readiness 59/100 (+1 media implementation point). Exact files/config/API/recovery/rollback: UPLOAD_QUOTAS.md. Signed adapter remains unfinished: provider docs show one-hour signatures and unsigned resource-type selection; local Cloudinary is unconfigured. Continue constrained signed-parameter/completion implementation and provider-reconciliation workflow without claiming direct uploads or billing quotas complete.

## Asset integration and local enablement — September 22

Completed editor upload ID capture/reload/save/removal and owner/type/URL validation in listing writes. IDs persist in the same gallery JSON transaction; existing same-listing URLs remain compatible, new unknown/foreign URLs are rejected when enabled. Seventy-three backend and 85 frontend tests plus lint/types/build/compilation/dependency/whitespace checks pass. Applied additive local ledger migration only after backup (`backend/intelliwheels-before-ledger-20260922-1610.db`) and enabled the owned preview process; six cars retained. Source/hosted flag remains false. Browser unavailable, so no interactive acceptance claim. Full changed files, behavior, manual QA and rollback in MEDIA_ASSET_LEDGER.md. Estimate 58/100 (+2 for verified integration/local enablement, no hosted acceptance credit). Next: signed-upload reservations/completion and per-user quotas; no physical media cleanup yet.

## Gated asset ledger foundation — September 22

Added explicit additive media schema and backup-first SQLite migration command (not run on live data), server-derived owner/provider/byte recording, and private owner-scoped lookup. Default flag false preserves existing uploads and makes no table changes. Missing migration fails before storage; registration failures expose no URL and cannot trigger fallback. Seventy backend tests, compilation/dependency checks pass. Fixed a Windows migration connection leak revealed by testing. Frontend unchanged; previous 83 tests/lint/types/build remain baseline. Both previews respond with six existing cars. New files/config/API/rollout and rollback: MEDIA_ASSET_LEDGER.md. Readiness stays 56/100: no credit for unrolled-out foundation alone. Resume with atomic listing-asset association/editor IDs, then reservation/signature/completion; quotas, duration, cleanup and hosted acceptance remain. Do not infer owned assets from historical URLs or automatically enable the flag.

## Listing media contract and removal — September 22

Added server-side media shape/URL/count checks matching the editor's 12-image/two-video limit, including merged saved fields on partial updates. Retained known label/thumbnail metadata and non-media edits of legacy records. Fixed query-string URL escaping and editor omission of empty primary URLs, which previously retained removed images/videos. 63 backend and 83 frontend tests pass; lint, changed-file lint, TypeScript, compilation, dependencies and whitespace pass. Production build succeeds with network access (restricted attempt failed only fetching Google Fonts). Both previews available, six cars intact, browser discovery empty. All scope/files/API changes/manual QA/rollback are in UPLOAD_SAFETY_PROGRESS.md. Estimate 56/100, one implementation point; do not force the requested 3–5% pace by inventing credit. No schema, cloud or hosted changes. Resume at persistent asset identity/ownership and reservation design for signed upload; quotas/duration/cleanup and cloud acceptance remain.

## Upload validation and persistence safeguards — September 22

Implemented bounded content validation before storage, image decoding/dimension/frame limits, basic video-container screening, one-file request enforcement, and fail-closed cloud behavior outside development. Fixed development fallback stream rewinding. Exact API compatibility changes, changed files, validation, manual QA and rollback: UPLOAD_SAFETY_PROGRESS.md. 45 journey/security + eight limiter + four import tests pass (57 total); compilation/dependency checks pass. Previews restarted: frontend 200/backend six existing cars. Browser discovery empty. No frontend, schema, hosted settings or deployment changes. Readiness estimate 55/100 (+3 media implementation points), not launch-ready. Next upload work: asset ownership/count/quota contract and signed-flow integration; duration, cleanup and hosted acceptance remain. Preserve all existing work; Phase 4 is not complete.

## Shared limiter and trusted proxy batch — September 19

Added optional Redis atomic sliding-window quotas, bounded one-second connection/read timeouts with no retries, safe fail-closed 503 without local fallback, and explicit environment namespaces. Added forwarded IP/scheme trust only for configured immediate peer networks/counts; forwarded host stays untrusted. Defaults preserve local limiter/no proxy trust. No external service, hosted config, credentials or deployment touched. 39 journey/security, eight limiter and four import tests pass (51 backend total); compilation, pip check and whitespace pass. Live frontend 200/backend six cars. Frontend unchanged; previous validation not rerun. Readiness estimate 52/100 (+3 implementation points), with real Redis/proxy/cookie staging still outstanding. Details/files/rollback: SHARED_LIMITER_PROXY_SETUP.md. Next independent deliverable: upload validation and production persistence safeguards; no claims that infrastructure gates are complete.

## Security headers and limiter batch — September 19

Implemented Phase 2D compatibility headers plus Phase 2E local limiter correction and endpoint coverage together. Removed blind XFF trust, separated endpoint budgets, added bounded/thread-safe monotonic windows and standard retry headers; guarded AI/search/uploads/admin application paths. Added frontend baseline CSP/HSTS and backend JSON-specific CSP/HTTPS headers without altering UI caching. 80 frontend entries, lint/types, 44 backend tests and Python compilation pass. Both previews return 200 with new CSP; six cars preserved. Scope, exact limits, source references, limitations and rollback in SECURITY_HEADERS_RATE_LIMITS.md. Overall launch readiness estimated 49/100 (+3 implementation points). This does not complete shared rate storage, strict script CSP, proxy topology, cookie rollout or browser/staging verification. No deployment, infrastructure service, schema or hosted settings changed.

## Password hashing modernization — September 19

Continued independent Phase 2C work while real-browser/staging cookie acceptance remains unavailable. Signup/change/reset now use Werkzeug's maintained default. Successful login upgrades only the confirmed historical PBKDF2 format, with compare-and-swap and session-transaction rollback. Four new tests; 32 journey/security plus four import tests and Python compilation/whitespace pass. Frontend unchanged, prior frontend validation not rerun. Both previews respond with six backend cars. No forced resets, bulk migration, schema change or deployment. Files: auth route, journey tests, new PASSWORD_HASH_MIGRATION.md, readiness and this log. Rollback/limitations in that document. Overall launch-readiness estimate 46/100 (+1 authentication implementation point); cookie rollout stays disabled. Next independent security work: inspect and test headers/rate-limit gaps, while browser/staging acceptance remains a release blocker.

## Password lifecycle coverage and readiness baseline — September 19

Three additional mounted-provider scenarios cover password rotation/reset and verification timeout; 78 frontend entries and 32 backend tests pass, as do lint and TypeScript. No runtime changes; previous build remains latest, not rerun for tests/docs. Both previews respond, backend six cars. Overall public-launch readiness estimated at 45/100 with explicit weighted rubric in PUBLIC_RELEASE_READINESS.md; include percentage plus next steps in future reports as requested. This is not deployment approval. Cookie rollout/browser/staging and other release blockers remain. Exact scope and rollback: SESSION_SECURITY_PROGRESS.md.

## Mounted authentication tests — September 19

Added ten mounted AuthProvider scenarios with the existing Node runner, ReactDOM and development-only jsdom 26.1.0 (Node 20 CI compatible). The real API/provider code runs against mocked fetch; no runtime implementation or rollout gates changed. All 75 frontend entries, lint, TypeScript, build (24 pages with font network access) and whitespace checks pass. Restarted previews: frontend HTTP 200, backend six cars. Browser discovery remains empty. See SESSION_SECURITY_PROGRESS.md for files, rollback and exact remaining cookie/browser/staging acceptance; do not treat DOM tests as browser cookie-policy verification.

## Logout lifecycle guard — September 18

Fixed local auth being cleared by stale logout completion and cookie-mode server revocation being skipped without a JS identity. Added a narrow typed helper and eight tests; 64 frontend test entries, lint and TypeScript pass. Preview remains available with six cars; both cookie gates remain disabled. Actual cookie response ordering and mounted/browser acceptance remain pending. See SESSION_SECURITY_PROGRESS.md for exact files, validation and rollback. No backend, schema, deployment or visual changes.

## Cookie transport regression coverage — September 18

Expanded existing mocked-network coverage by nine cases without changing application behavior or dependencies. All 56 frontend entries and 32 backend tests pass. Browser discovery still reports no connected browser; real lifecycle/staging acceptance is pending and both cookie gates remain disabled. Live frontend returns 200 and backend still serves six cars. Changed this continuation: `tests/cookie-api.test.mjs`, session progress/QA and this log. Build not rerun for test/docs-only edits. Resume from browser/provider lifecycle acceptance, not from reimplementing the completed transport. Detailed scope and rollback: `SESSION_SECURITY_PROGRESS.md`.

## Canonical reset-link origin — September 18

Separated password-reset email URL construction from the comma-separated CORS allowlist. Added validated PASSWORD_RESET_ORIGIN configuration with first-allowed-origin compatibility fallback; link directly to `/account`. Confirmed arbitrary request Host/Origin cannot affect destination. No hosting configuration, credentials, DNS, UI or database changes.

28 isolated journey/security tests and four import tests pass; compileall/whitespace pass. Frontend HTTP 200 and backend six cars verified. Prior frontend lint/typecheck/build pass remains unchanged. Cookie rollout gates stay disabled pending mounted/browser/staging validation and legacy-session cutover. Exact files, configuration behavior and rollback are in SESSION_SECURITY_PROGRESS.md.

## Frontend cookie transport and lifecycle — September 18

Continued the existing gated implementation, preserving the bearer-mode preview. Added cookie request/CSRF/session-version transport and AuthContext integration, cross-tab/focus revalidation, server verification versions, login/password-change rotation and truthful logout failures. Protected the existing message-read GET side effect with CSRF in cookie mode. No UI, database schema or deployment changes. Both gates remain false; migration is IN PROGRESS, not complete.

47 frontend test entries, 25 journey/security tests, four import tests and TypeScript pass. Final project lint, TypeScript, production build (24 pages) and whitespace checks pass after the thread-CSRF patch; build required network access for existing Google Fonts. Browser unavailable after supported discovery/troubleshooting; no interactive QA claimed. Servers were stopped between runs and have been restarted on :3000/:5000; final frontend HTTP 200 and six backend cars confirmed.

Exact files/remaining tasks/rollback: `SESSION_SECURITY_PROGRESS.md`. Added `SESSION_COOKIE_MANUAL_QA.md`. Next: canonical reset origin, mounted/browser acceptance and coordinated activation after remaining checks; do not reimplement completed hashing/cookie foundation.

## Cookie/CSRF foundation — September 16

Added a disabled-by-default cookie transport foundation and integrated token resolution across backend readers. Existing bearer live behavior remains unchanged; cookie mode is exercised only in isolated tests. No frontend conversion or live cutover claimed. See `SESSION_SECURITY_PROGRESS.md` for contract, exact outstanding activation requirements and rollback.

Files this slice: `backend/app/cookie_auth.py`, `backend/app/__init__.py`, `backend/app/security.py`, `backend/app/routes/auth.py`, `backend/app/routes/favorites.py`, `backend/app/routes/listings.py`, `backend/test_public_journey.py`, session-progress/release documentation and this log. 24 isolated tests pass before final checks. Next execution must resume frontend cookie/CSRF integration plus lifecycle tests, not reimplement this foundation or enable it prematurely.

## Session compatibility and hashing — September 16

Proceeding with the recommended same-site custom-domain design, without external configuration changes. Fixed returning Google-user SQLite failure (reproduced 500 then passing regression); added versioned SHA-256 storage for newly issued signup/login/Google sessions. Existing raw sessions temporarily retain read/revoke compatibility. Digest replay is explicitly rejected, and no data/schema migration was run.

Files: `backend/app/routes/auth.py`, new `backend/app/session_tokens.py`, `backend/test_public_journey.py`, `docs/SESSION_SECURITY_PROGRESS.md`, this log and release/audit documentation. 21 isolated tests pass. Session cookies/CSRF and coordinated frontend conversion are NOT complete. See progress document for exact remaining work and rollback caveat: old auth code cannot read hashed sessions.

## Session transport audit — September 16

Created `docs/SESSION_TRANSPORT_MIGRATION_AUDIT.md` with repository evidence, cookie/CORS/cache/UI dependencies, rollout sequence and topology decision. Added baseline login/logout/reset coverage in `backend/test_public_journey.py`; all 18 tests pass. No runtime changes. Existing shared per-IP rate-limit bucket initially caused 429 during the combined test; separate reset fixture IP isolates reset behavior without changing the limiter. Live frontend 200/backend six cars confirmed.

Migration requires deciding whether authenticated previews use stable same-site custom staging domains (recommended minimal direct-API design) or raw hosting domains requiring a gateway/alternative design. No deployed domains assumed or modified. Remaining confirmed compatibility concerns include Google sqlite3.Row access, profile password-change session revocation, reset URL/CORS-origin conflation, and endpoint-shared rate limits. See audit for rollback and required checks.

## AI error disclosure continuation — September 16

Completed: AI logs use fixed event messages, omit raw exceptions and malformed model output, and no longer print search queries/results. Initialization retains a fixed error rather than a provider exception. Chat, image analysis and listing-assistant generic failures return safe text. Existing classified safety/quota/authentication responses, successful response shapes, prompt logic, language detection, model order and fallback behavior are unchanged. No SDK/provider migration or network AI calls.

Files: `backend/app/services/ai_service.py`, `backend/app/routes/ai.py`, `backend/test_public_journey.py`, this log and release-readiness document.

Validation: 17 isolated journey/security tests and four import tests pass; Python compilation and whitespace checks pass. Mocked tests cover unknown/quota/safety/auth provider errors, image-only chat, absent models, malformed vision output, initialization failure and successful chat/vision output. Static logging checks cover AI route/service. Frontend HTTP 200 and six backend cars verified. Frontend files untouched; lint/build/typecheck not rerun.

Limitations: tests do not validate live Gemini availability, output quality or cost controls; local AI remains unconfigured. Successful model-generated text is intentionally still returned, not redacted. Infrastructure/SDK telemetry is not covered by application print checks. Rate limits, secure session transport, durable uploads and browser QA remain release blockers.

Rollback: undo only this continuation's logging/error-text hunks and four AI test methods. Preserve earlier route/auth hardening, models, schema and UI. Rollback would restore disclosure and is unsuitable for public deployment. Next: session-security transport design and compatibility audit before coordinated implementation.

## Non-AI error disclosure continuation — September 16

Completed: app-wide request exception handler returns fixed JSON 500 and logs only `request.unexpected_error`, without exception attachment. Intentional HTTPException responses retain status/headers. Non-AI route prints no longer include raw exceptions, email bodies, recipient details or review content; explicit traceback printing removed. Listing creation, favorites, messages, callbacks and review failure responses now use fixed messages. Health database/AI error fields retain their shape but no longer expose exception/provider text. Normal successful responses and SQL are unchanged.

Files: `backend/app/__init__.py`; `backend/app/routes/{cars,dealers,favorites,listings,messages,reviews,system}.py`; `backend/test_public_journey.py`; this log and release-readiness document. Existing dirty work and endpoint removals preserved.

Validation: 13 isolated journey/security tests plus four import tests pass; compileall and whitespace checks pass. Failure injection covers uncaught 500, 404/405/413 preservation, health, listing creation and favorite writes. Static checks prohibit dynamic print data/traceback output in the seven non-AI route modules. Fixed an initial test-only namespace-package path assumption, then reran successfully. Browser acceptance remains pending; no frontend files changed or lint/build rerun. Frontend HTTP 200 and backend six cars verified.

Limits: caught AI-service errors can still expose provider details; hosting/access/telemetry logs and startup/teardown failures are outside the request handler. Constant events reduce diagnostic detail; safe correlation/observability is still future work. Existing favorites read failure still returns an empty success result; not changed in this disclosure-only issue. Full PostgreSQL failure flows are not tested.

Rollback: reverse only these logging/error-message hunks and the new handler/tests, preserving earlier auth guards and removed dangerous endpoints. Rollback reopens error disclosure. No schema/data changes. Next: redact AI-service error output without changing model selection or feature behavior, then continue session security.

## Authentication logging continuation — September 16

Removed token-prefix and username prints from session verification. Auth email, signup, login, logout, profile, reset and Google-verification logs now use constant event identifiers, without raw exceptions, recipients, credentials, or traceback attachments. Removed raw exception interpolation from explicit database logs beneath authentication. No API responses, queries, schema, session transport or UI changes.

Files: `backend/app/routes/auth.py`, `backend/app/db.py`, `backend/test_public_journey.py`, this log and `docs/PUBLIC_RELEASE_READINESS.md`.

Validation: nine isolated journey/security/logging tests and four import tests pass; Python compileall passes. Tests cover session verification output, injected SMTP/database exceptions, and a static constant-message rule. Live frontend HTTP 200 and backend six cars verified. Frontend lint/typecheck/build not rerun because frontend is unchanged. No preview-data mutations, external email, cloud uploads or production changes.

Limitations: this is not complete application-wide log redaction. Framework uncaught-exception traces, other route logs, infrastructure access logs (including reset URLs), and telemetry need separate review. Existing exception propagation is preserved. Cookie transport, CSRF, token hashing/rotation and browser acceptance remain outstanding.

Rollback: undo only this continuation's logging replacements and four added test methods; retain all earlier access-control and frontend work. Restoring sensitive logs is not suitable for public deployment. Next: audit uncaught errors and remaining backend logs before completing the broader session-security work.

## Access-control continuation — September 16

Completed the approved priority security exception: listing creation and image/video uploads require an existing valid session. OPTIONS/public browsing stay available; listing ownership comes from the session, never the submitted owner ID. No auth transport redesign, schema changes or production actions.

Changed: `backend/app/routes/cars.py`, `backend/app/routes/system.py`, `backend/test_public_journey.py`, `docs/PUBLIC_RELEASE_READINESS.md`, this log. Preserved all existing dirty-worktree changes.

Validation: five isolated journey/security tests, four import tests, Python compileall, 38 frontend test entries and whitespace checks pass. Both live previews respond; six cars remain. Frontend lint/typecheck/build previously passed and were not rerun for this Python-only patch. Interactive browser acceptance and production-database verification remain pending. Tests never use preview data or cloud storage.

Rollback only the new guards/import and owner assignment, preserving earlier system endpoint removals. Removing guards reopens a security vulnerability. Next: remove sensitive authentication logging, then continue session security and outstanding frontend acceptance; public release remains unsafe until documented blockers are resolved.

## Release-priority continuation — September 16

User requested core functionality/public-release blockers first. See `PUBLIC_RELEASE_READINESS.md` for verified flows, exact scope, blockers and rollback. Corrected newly uploaded local-media URLs without changing backend behavior. Added an isolated, passing seller/buyer API smoke journey (registration, CRUD, favorites, messaging privacy, ownership, logout). Frontend runner reports 38 passing entries; TypeScript and ESLint pass. Frontend on port 3000 and backend on port 5000 were confirmed live with six existing cars. Requested permission to move the narrow anonymous-write security correction ahead of remaining frontend work; no backend behavior change made while awaiting that decision.

## September 16: API-client session and cache integration tests

- Added `tests/api-session.test.mjs`, exercising the actual compiled API client with mocked network and browser storage/events. No backend writes, real tokens, dependencies, or application behavior changes.
- Nine request-level cases cover anonymous reference caching, authenticated `no-store`, explicit-token precedence, resolved stored-token rejection, 403 preservation, anonymous 401, non-JSON authenticated 401, network failures and abort propagation.
- Added `npm test`. Node reports 35 passing test entries (34 leaf cases plus the API parent group). TypeScript and project ESLint pass.
- Production build passes, including 24 generated pages. The existing outdated Browserslist-data warning remains; no dependency update performed.
- Restarted the local frontend and Flask backend, retaining the existing SQLite database. `/account` and its stylesheet return HTTP 200; CSS retains `no-store, must-revalidate`; API returns six cars. No record import was repeated.
- Browser setup/discovery reports no connected browser. Per the browser-verification skills, visual/interactive acceptance remains pending rather than being inferred from HTTP status.
- Local backend warns that its development secret is unsuitable for production and Gemini is unconfigured. No secrets were printed, configured or changed in this continuation.

Files: `package.json`, `tests/api-session.test.mjs`, and this log. Rollback: remove only the test script entry and new test file, preserving all existing tests and implementation. Git remains dirty/uncommitted with earlier work preserved.

Next: add mounted-provider/session-transition coverage, then finish the remaining browser acceptance and localization work before marking Phase 1 complete.

The user approved the repaired preview appearance and requested resumption of the architecture instructions. Preserve the shared design and Next.js-managed development asset caching. No new backend/security phase has begun in this continuation.

## Completed: frontend URL regression coverage

- Added `tests/listings-search-params.test.mjs`, using Node's built-in test runner and the existing TypeScript compiler, with no dependency additions or generated source files.
- Tests cover defaults, every supported filter, invalid enum/page values, pagination reset, active-filter serialization, removal of defaults, unrelated-parameter preservation, Arabic encoding, stable serialization, and independent history-state restoration.
- Tests exposed unsafe integer pagination acceptance. `src/lib/listingsSearchParams.ts` now rejects unsafe/noninteger pagination for both parsing and serialization.
- Added a narrow `.gitignore` exception so the previously added `backend/test_import_local_cars.py` regression tests are not silently excluded from Git. No backend behavior was changed.

## Completed implementation: independent listing/reference loads

- `PublicListingsView` no longer uses `Promise.all` to couple inventory success to makes-reference success.
- Makes load independently on session/retry changes, not on every filter change.
- Makes available in returned cars and the current URL remain selectable if reference loading fails.
- Superseded listing requests are aborted and stale responses are ignored.
- Canonical request keys include only supported filters, preventing page-only, query-order, and unrelated query changes from restarting inventory requests.
- No layout, API contract, authentication architecture, database, or production configuration changes.

## Completed implementation: restore listing sorting

Repository evidence: `backend/app/routes/cars.py:get_cars` always orders by creation time and does not consume the supplied `sort` parameter. The former `AppView` applied client-side sorting, but that step was absent in the migrated listings view.

`src/lib/sortListings.ts` now sorts a copy of the returned inventory before pagination. The view supplies the existing `AuthContext.convertCurrency` conversion to JOD for price comparison, so AED/SAR/JOD nominal amounts are not compared directly. Default preserves API order; year/rating sorts are descending; missing/nonfinite values sort last; ties remain stable. `tests/listings-sort.test.mjs` covers all options, nonmutation, currency projection, missing values and pre-pagination ordering. Backend filtering/response limits remain unchanged; ordering applies to the fetched dataset, not records beyond the API's 1,000-row cap.

## Final checks and remaining acceptance work

- TypeScript and project ESLint passed after the implementation.
- Final production build after sorting passed (24 generated pages); the only warning was the old Browserslist dataset. `/listings` returned HTTP 200, development CSS retained `no-store, must-revalidate`, and the running backend returned six cars.
- 16 frontend tests pass: 12 URL-state/request-key cases and 4 ordering cases. The existing 4 local-import tests also pass.
- Browser interaction remains unverified. User approval establishes appearance acceptance, not full route parity.
- Manually fail `/api/makes` while `/api/cars` succeeds: inventory must stay visible. Change filters rapidly: only the latest result may apply. Change page or an unrelated tracking parameter: no inventory refetch should occur.
- Existing route QA documents remain applicable. Complete bilingual route labels, authenticated interactions, and browser Back/Forward still require an end-to-end comparison before declaring the frontend fully verified. Manually confirm each sort option reorders visible cards, including mixed-currency prices, and resets pagination.
- Dependency install was not repeated: existing locked dependencies are installed and both live servers were preserved.

## Rollback

Undo only the continuation changes in `PublicListingsView`, `listingsSearchParams`, `sortListings`, the two frontend test files, and the narrow Git exception. Preserve the approved UI, cache fix, local data, and all pre-existing migration changes. No commits or broad Git resets were performed.

## Next coherent issue

Continue checking private-route state transitions and remaining localization; browser verification of authenticated flows remains pending. Finish remaining frontend acceptance gaps before Phase 2 security work.

## Continuation: explicit 401 handling and stale verification protection

Phase 1E frontend correction; no backend/session-transport redesign.

- `apiRequest` now notifies the auth provider when an authenticated request receives an explicit 401. It uses the actual resolved token, including the legacy storage fallback. Non-401 responses and unauthenticated requests do not emit this signal.
- `AuthProvider` only clears auth when both current state and persisted token match the rejected request. A delayed old-session 401 cannot clear a replacement login. Clearing auth resets the fresh-login validation shortcut too.
- Session verification now has effect cleanup that aborts obsolete requests. Success/failure responses are ignored once unmounted or when the persisted session has changed.
- Removed debug `console.log` statements from `AuthContext`, including token-prefix and complete response/profile logs. No secret values were added to logs or documentation.
- Added `sessionEvents.ts` and three Node tests covering token identity, server-side no-op behavior, delivery, and unsubscribe. Total frontend tests: 25 passing; TypeScript and project ESLint pass.

Files: `src/lib/api.ts`, `src/context/AuthContext.tsx`, `src/lib/sessionEvents.ts`, `tests/session-events.test.mjs`, and this documentation. These files had prior changes; preserve them when reviewing or rolling back. Undo only this continuation's notification/cleanup/logging hunks and remove its helper/test together.

Manual checks pending: expire the current session and make a protected request (private UI must close); allow an old-session request to return 401 after a new login (new session must remain); navigate away during delayed verification (old result must not overwrite current state); verify logout, login, Google OAuth, timeout and 403 behavior. Tests here cover the event/identity logic, not a mounted auth-provider or full browser flow. Local-storage session transport remains a known Phase 2 concern.

## Continuation: account and conversation state corrections

Confirmed defects and fixes:

- `AccountView` initialized local mode to `reset` from a URL token. Removing the token could retain reset mode without a reset form, leaving the page with no form. Reset is now derived only from the URL; local mode starts at login.
- The authenticated account branch did not render `useAuth().error`, hiding profile-update failures. It now exposes the existing error in an alert. Backend validation and authentication transport are unchanged.
- `MessagesView` kept a single untagged message array when changing recipients. Messages now carry their conversation ID; `messagesForConversation` returns no loaded thread until the data matches the current selection. The existing effect cleanup ignores stale fetch responses.
- Retry now also reruns the active-thread request, not just the conversation list.
- The composer is keyed by conversation ID so unsent text is not silently carried to another recipient. Thread switching is disabled during sending; sending is disabled until that thread has loaded. This intentionally discards an unsent draft when switching threads; per-thread draft persistence is not introduced here.
- Added Arabic loading/retry labels for account/favorites/messages and composer accessible text. Server-provided errors and some existing account success notices remain untranslated.
- Favorites now uses the same image/gallery fallback sequence as listings, preserving API-provided images when `imageUrls` is absent.

Files: `src/components/account/AccountView.tsx`, `src/components/messages/MessagesView.tsx`, `src/components/favorites/FavoritesView.tsx`, `src/lib/messageThread.ts`, `tests/message-thread.test.mjs`, and this log plus the account/favorites/messages QA document.

Validation: 22 frontend tests pass, including three new conversation-selection cases. Final TypeScript, project ESLint and production build pass, including the final label/image fallback changes. `/account`, `/favorites`, and `/messages` return HTTP 200; the backend still returns six cars. Authenticated browser and failure-injection checks remain pending. No backend/database/authentication architecture or CSS changes. Existing dirty worktree preserved, no commits.

Rollback: undo only this continuation's account-mode/error-display, tagged-thread/retry/composer and localization/image-fallback hunks; remove the new helper and tests together. Keep all previous frontend, cache, and data repairs.

## Continuation: listings localization and shared-header keyboard behavior

- Added `src/lib/listingsCopy.ts`, with typed matching English/Arabic keys for all listing filters, options, pagination, empty/loading/error/retry messages and accessible labels. `PublicListingsView` now consumes this copy without changing option values, handlers, CSS classes, sorting, or URL semantics.
- Listing failures now show a localized, stable user-facing message instead of unlocalized exception text. Retry behavior is unchanged.
- Added `ListingsRouteFeedback` and reused it in `/listings` loading/error boundaries. Those boundaries sit outside the page provider, so they reuse `useStoredPreference` to restore language/theme without mounting a duplicate shell or depending on unavailable context. They supply their own language and direction attributes.
- `RouteErrorState` accepts an optional retry label with its existing English default, preserving all other callers.
- Localized public header logo/menu/navigation/theme/currency accessible labels. Escape closes an open mobile navigation and returns focus to its toggle; links and appearance are unchanged.
- Added `tests/listings-copy.test.mjs`. All 19 frontend tests pass; TypeScript and project ESLint pass. Translation-key and option-value tests are automated; they are not a substitute for browser rendering or screen-reader tests.
- Final production build passes (24 generated pages). Live `/listings` returns 200, CSS still uses `no-store, must-revalidate`, and the backend returns six cars. Only the pre-existing old Browserslist dataset warning remains.

Files in this continuation: `src/lib/listingsCopy.ts`, `src/components/listings/PublicListingsView.tsx`, `src/components/listings/ListingsRouteFeedback.tsx`, `src/components/RouteErrorState.tsx`, `src/app/listings/loading.tsx`, `src/app/listings/error.tsx`, `src/components/public/PublicHeader.tsx`, `src/components/public/PublicRouteShell.tsx`, `tests/listings-copy.test.mjs`, and the roadmap/manual-QA documentation.

No backend/API/database/authentication changes. Rollback only these localization/accessibility hunks and new files together; retain prior sorting, request cancellation, design and asset-cache changes. Worktree remains dirty and uncommitted; unrelated changes are preserved.
