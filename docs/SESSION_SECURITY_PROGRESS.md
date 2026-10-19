# Session security progress

Status: IN PROGRESS. Cookie/CSRF migration is not complete or enabled.

## Password lifecycle and timeout acceptance — September 19

Added three mounted-provider regressions to `tests/auth-provider.test.mjs`: successful password rotation adopts the new non-secret session version/profile without credential storage; successful reset clears local authentication and broadcasts change; the existing 15-second verification timeout aborts fetch and settles as an unverified guest. All 13 mounted scenarios pass. No runtime code, rollout gates, dependencies or configuration changed in this slice.

Overall launch-readiness baseline is now documented as an estimated 45/100 in PUBLIC_RELEASE_READINESS.md, weighted across seven deliverable areas. This is not a claim that remaining risk is 55% or that public deployment is safe. Future reports should include next steps plus this overall estimate, updating it only when justified by delivered/verified work.

Validation: 78 frontend test entries, 28 backend journey/security tests and four import tests pass; project ESLint and TypeScript pass. Preview frontend returns HTTP 200 and backend serves six cars. No real-browser checks performed. Files changed: provider test, release-readiness report, session progress/QA and roadmap log.

Rollback: remove only the three additional test cases and this continuation's documentation. Preserve prior mounted tests, jsdom dependency and all implementation. Actual browser cookies, concurrent Set-Cookie ordering, real cross-tab behavior, staging and legacy cutover remain pending. Build is not rerun for these test/documentation-only edits; preceding build remains the latest passing build.

## Mounted AuthProvider coverage — September 19

Added `tests/auth-provider.test.mjs`, mounting the real React AuthProvider, API client and session helpers with ReactDOM and the existing Node test runner. Only fetch responses and the DOM environment are simulated; cookie mode is enabled in the in-memory test compilation, not in source configuration. Ten scenarios cover startup identity restoration and credential cleanup/preferences, guest StrictMode settling, login/logout, failed logout preserving verified UI, focus re-verification, storage-event re-verification with stale responses, offline startup, delayed logout success/failure after a newer login, and logout during pending startup. These are mounted React checks, unlike the earlier helper-only tests.

Added development-only jsdom 26.1.0 (package/lockfile) for DOM support, retaining compatibility with Node 20 CI. No new test runner, production dependency, runtime code or rollout change. jsdom emulates DOM APIs, not a real browser's cookie/CORS policy: https://github.com/jsdom/jsdom . No scripts or external resources are enabled in the test DOM. Fixtures unmount roots and restore globals.

Validation: all 75 frontend test entries pass; project ESLint, TypeScript, production build (24 pages, network access for existing fonts) and whitespace checks pass. Existing Browserslist-age warning remains. Installation reported deprecated transitive whatwg-encoding; no unrelated dependency updates were attempted. Backend unchanged and its tests not rerun in this slice. Preview processes had stopped; restarted frontend/backend and confirmed HTTP 200 and six cars. No browser available after supported discovery/troubleshooting, so no visual checks are claimed.

Remaining: actual browser cookie response ordering for simultaneous login/logout, cross-tab cookie/storage coordination, OAuth provider acceptance, timeout/unmount/password-rotation lifecycle coverage, same-site HTTPS staging and PostgreSQL, and legacy-session cutover. The tests do not model Set-Cookie, and their delayed-logout assertions prove local state protection only. Both cookie gates remain false; migration remains IN PROGRESS.

Changed this slice: `tests/auth-provider.test.mjs`, `package.json`, `package-lock.json`, session progress/QA and roadmap log. Rollback: remove only this test file and jsdom dependency/associated lock entries, preserving the existing test command and all prior tests and implementation. No database or backend rollback required.

## Logout completion guard — September 18

Code inspection found that AuthContext skipped server logout when its token/version was null, even though cookie mode can have an HttpOnly cookie before verification finishes. It also unconditionally cleared local authentication after a delayed logout, potentially clearing a replacement login. Added typed `src/lib/logoutSession.ts` orchestration and wired it into AuthContext. Cookie mode always requests revocation; failed revocation keeps local auth and shows retry. Stale handlers do not issue requests; stale completions/errors do not update local auth. Guards use cookie revision plus identity, or current persisted bearer identity, and are checked again before the UI change. Legacy offline sign-out behavior is retained.

Eight new dependency-free tests cover these outcomes, including delayed success/failure in both transports. All 64 frontend test entries, project ESLint, focused changed-file ESLint and TypeScript pass. HTTP preview checks returned frontend 200/backend six cars. No backend or database changes; backend tests were not rerun for this frontend-only slice. Build initially failed only on Geist/Geist Mono fetching; network-enabled retry result is recorded below.

This is a local UI race fix, not proof of complete browser lifecycle safety. HTTP Set-Cookie response ordering across overlapping login/logout requests remains a separate acceptance concern; mounted provider, multi-tab and staging tests remain pending. Both cookie gates stay disabled. No visual design, preferences, routes, hosted configuration or dependencies changed.

Final build: PASS with network access, 24 pages generated. Restricted attempt reported only `Failed to fetch Geist` and `Failed to fetch Geist Mono` from Google Fonts; no font configuration changed. Existing nine-month-old Browserslist-data warning remains. Whitespace validation passes. Browser checks were not performed in this continuation.

Files: `src/context/AuthContext.tsx`, new `src/lib/logoutSession.ts`, new `tests/logout-session.test.mjs`, session QA/progress and roadmap log. Rollback only the new helper/import/handleLogout changes and tests together; preserve all earlier auth, hash, CSRF and public-route work. No data migration or destructive operation.

## Transport failure acceptance coverage — September 18

Added nine focused cases to `tests/cookie-api.test.mjs`, using the existing Node test runner and mocked fetch: malformed CSRF payloads with recovery, shared bootstrap failure/recovery, already-aborted requests, independent cancellation of concurrent callers, session revision changes even when the identity returns to its earlier value, no automatic mutation retries, verification without a stale version header, no browser bearer-storage reads, and protected 401 notifications versus failed-login credentials. Test fixtures restore their temporary globals and event subscriptions. No runtime implementation, dependencies, database, settings or rollout gates changed.

Validation: all 56 frontend test entries and 32 backend tests (28 journey/security plus four import tests), project ESLint and TypeScript pass. Browser discovery returned no connected browsers; no mounted React, visual, cookie-policy or multi-tab checks were performed. HTTP checks confirmed frontend 200 and six backend cars. Production build was not rerun for this tests/documentation-only change; the previous passing build is not a new validation result.

Remaining: mounted/browser AuthProvider lifecycle checks, same-site HTTPS staging cookie/CORS and PostgreSQL acceptance, and a reviewed legacy-session cutover. Keep both gates false. The mocked EventTarget tests validate API notifications only, not provider rendering or real browser storage. Follow `SESSION_COOKIE_MANUAL_QA.md`; browser access is needed to complete its interactive portion.

Rollback: remove only this continuation's nine test cases, helper/import and documentation entries. Preserve the earlier eight cookie transport tests and all existing implementation. No runtime rollback or database operation is required.

## Canonical reset origin — September 18

Completed: new `backend/app/frontend_origin.py` separates account-email destinations from CORS. Optional backend `PASSWORD_RESET_ORIGIN` is one validated origin; if absent, the first nonempty configured FRONTEND_ORIGIN entry is used for compatibility. App startup rejects malformed URLs, origin lists, userinfo, paths, query/fragment, wildcard origins and insecure non-loopback URLs. HTTP loopback is development-only. Errors do not echo configuration values. No .env, hosted settings or DNS changed.

Reset links now target `/account?reset_token=...`, matching AccountView, with URL-encoded tokens. Request Host/Origin cannot influence links. CORS continues to use its complete original list. Explicit canonical-origin overrides are independent of list order. Teams should set the intended HTTPS canonical origin per hosted environment before deployment; malformed existing origin configuration may now block startup rather than produce unsafe reset emails.

Validation: 28 journey/security tests plus four import tests pass; Python compilation and whitespace checks pass. Added origin validation, two-origin app-factory configuration and intercepted reset-email assertions (no real email). Live frontend HTTP 200 and six backend cars confirmed. Frontend unchanged; prior lint/typecheck/build results retained, not rerun here.

Files: new `backend/app/frontend_origin.py`, app factory, auth route, journey tests, session QA/progress, deployment notes and roadmap. Rollback only resolver/config/reset-URL hunks and related tests together; preserve cookie/hash work. Old already-issued links are not rewritten.

Remaining: mounted/browser lifecycle acceptance, actual same-site staging cookie/CORS and PostgreSQL verification, and legacy-session cutover. Both transport gates remain false. Canonical reset-origin separation is no longer a code blocker; SMTP delivery/operational configuration is still unverified.

## Frontend integration and lifecycle continuation — September 18

Both rollout gates remain false: `src/lib/config.ts:COOKIE_AUTH_ENABLED` and the backend app-factory `COOKIE_AUTH_ENABLED` default. Cookie mode has not been activated on the live preview. Earlier sections below describe earlier checkpoints, not the latest test counts.

Implemented and tested API transport in `src/lib/cookieSession.ts` and `src/lib/api.ts`: credentials include, no Authorization header or localStorage lookup in cookie mode, no-store requests, coalesced CSRF bootstrap, no mutation retries, session-version headers, and cancellation/session-change checks. The existing `token` argument/context property temporarily carries a non-authenticating sessionVersion in cookie mode. It is never used as a bearer credential. This preserves existing page props without rewriting UI.

AuthContext cookie path removes old browser token/profile keys, verifies the server session on startup, persists no credentials/profile, guards stale validation/profile updates, and rechecks on focus or a non-secret cross-tab storage notification. Failed logout is shown as an error instead of falsely clearing the UI. These context behaviors have static/type/lint validation but still require mounted/browser acceptance; API helper tests do not establish React lifecycle correctness.

Backend adds sessionVersion to successful verification, rejects mismatched version headers, revokes the presented cookie on successful sign-in, and revokes all user sessions/rotates the current cookie on password change. Logout database failures now return 500 in cookie mode without clearing cookies. The legacy conversation GET marks messages read, so cookie mode now requires Origin/CSRF for that GET as temporary compatibility; frontend thread requests supply it. Bearer-mode behavior is retained.

Validation: 47 frontend test entries pass; 25 isolated journey/security tests and four import tests pass; TypeScript, project ESLint and Python compilation pass. Production build passed with network access after the restricted run failed to fetch Geist/Geist Mono. The final thread-GET CSRF adjustment passed tests/typecheck; final build/lint rerun recorded in roadmap. Existing Browserslist-age warning remains. No connected browser was available after discovery/troubleshooting, so no visual or interactive checks are claimed.

Remaining before activation: canonical reset-link origin separation, mounted/browser lifecycle and cross-tab acceptance, real same-site staging CORS/cookies, safe legacy-session cutover and PostgreSQL verification. Both gates must switch together only after these checks; do not silently accept raw Vercel/Render cross-site previews as equivalent. Follow `SESSION_COOKIE_MANUAL_QA.md`.

Files this continuation: frontend config/API/AuthContext, new cookieSession helper, API test loader and new cookie API tests; backend cookie_auth/app factory/auth route and journey tests; session QA/progress and roadmap documents. Rollback this slice by keeping both gates false; revert its gated branches/tests together if needed, preserving hash-aware sessions and all earlier security/UI work.

## Gated backend cookie/CSRF contract

Implemented `backend/app/cookie_auth.py`, integrated into the app factory and all request-token readers in auth/security/favorites/listings. `COOKIE_AUTH_ENABLED` defaults to false and has no new environment-variable toggle. The live frontend/backend still use the verified bearer path; do not enable the gate before the coordinated frontend conversion.

When explicitly enabled in isolated tests: login/signup/Google responses set host-only HttpOnly SameSite=Lax cookies and omit the raw token from JSON. Secure mode uses `__Host-` names. An HMAC-derived `sessionVersion` is a non-authenticating identifier. CSRF bootstrap uses an HttpOnly anonymous seed or the existing session cookie; unsafe API methods require an exact trusted Origin plus the HMAC CSRF header. Cookie mode never falls back to bearer headers. CORS enables credentials only for explicit origins; authenticated/auth responses are no-store. Successful logout expires both cookies. Hosted cookie mode requires a valid secret and forces Secure, including staging.

24 isolated journey/security tests pass: original bearer flows plus cookie signup/verify/listing/logout, old-CSRF invalidation after login, different-client CSRF rejection, hostile/null/missing origins, bearer rejection, credentialed preflight, cookie attributes and unauthenticated uploads. This is test-client coverage, not browser acceptance. No frontend code or live transport changed.

Known gated-contract gaps before activation: frontend sessionVersion bootstrap/verification, password-change/login rotation policy, logout failure semantics, stale/multi-tab responses, canonical origins, cookies across real staging hosts and browser CSRF/CORS verification. Existing GET message-read side effects must be reviewed against CSRF method assumptions. None of these are marked complete.

Rollback for this slice: keep COOKIE_AUTH_ENABLED false; remove cookie_auth hooks and restore direct bearer readers/session response wrappers together if necessary. Preserve hash-aware verification/logout and prior fixes. No session/database migration is needed for this disabled foundation.

## Design direction

Proceeding with the recommended same-site custom-domain direct API design after the user's continuation. No domains, DNS, deployment or hosted environment settings changed. Raw cross-site hosting preview URLs will not be assumed compatible with SameSite=Lax cookies. Verify staged custom origins before rollout.

## Completed compatibility baseline

`backend/app/routes/auth.py:google_auth` converts the existing database row to a dictionary before using `.get`. The new regression test reproduced returning-user HTTP 500 on SQLite before the fix, then passed. Both native SQLite rows and the repository PostgreSQL row wrapper support dictionary conversion. Live PostgreSQL and Google-provider flows remain unverified.

## Completed session hashing bridge

- `backend/app/session_tokens.py` hashes high-entropy random session tokens with SHA-256 and a `sha256:` version marker. This is not password hashing.
- Signup, login and Google sign-in store the digest in the existing TEXT token column; the client still receives the opaque random token under the existing API contract.
- Verification and logout use parameterized digest/legacy lookups. Supplied digest-prefixed credentials are rejected so database hashes cannot be replayed via legacy fallback. Blank/non-string/overlong credentials fail closed instead of being truncated into valid credentials.
- Existing raw sessions remain readable and revocable temporarily. No live rows, schema or token column names were migrated. Raw legacy rows remain a security limitation until a separately planned expiry/cutover; no claim that all stored sessions are hashed.
- Logout and password-reset revocation still work. Password-change rotation and browser localStorage removal are still pending.

## Validation

21 isolated journey/security tests pass, including signup/login/Google digest storage, digest replay rejection for verification and logout, legacy compatibility, expiry/revocation, login/reset behavior and protected listing/upload flows. No real OAuth credentials/provider calls, email, or preview-data mutations.

## Exact remaining work

1. Separate canonical reset-link origin from CORS allowlist and verify environment policies (hosted staging must not inherit insecure development defaults).
2. Add cookie issuance/clearing and session-bound CSRF protection together, including login/signup/Google and all unsafe authenticated methods.
3. Coordinate frontend credentials, startup verification, session-generation stale-request protection, cache policy and removal of all localStorage bearer keys; replace token-based UI gates.
4. Rotate sessions on password changes and login as specified, decide legacy-session cutoff, and document recovery. Do not silently delete production sessions.
5. Backend/API/frontend tests plus lint/typecheck/build; browser cookie/CORS/CSRF, Google, mobile/RTL, reload/multi-tab and account/listing workflows. PostgreSQL staging verification before production.

## Rollback

Keep the hash-aware reader/logout when rolling back any newer code. Old auth code cannot recognize hashed rows, so a full rollback signs out users with newly issued sessions; hashes cannot be converted back to credentials. No destructive database operation is needed. The Google dictionary-conversion fix is independent. Preserve all earlier logging and access-control changes. No commit or deployment performed.
