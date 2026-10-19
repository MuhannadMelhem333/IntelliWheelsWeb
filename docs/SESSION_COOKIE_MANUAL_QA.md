# Cookie session acceptance checklist

Status: NOT RUN. Both rollout gates remain disabled in the working preview.

Latest automated coverage: 13 mounted scenarios now include password rotation, password-reset local sign-out/broadcast and an aborted 15-second verification timeout. Mocked server responses verify UI behavior, not actual server revocation, browser cookie rotation or email delivery. Interactive rows remain pending.

September 19 automated update: ten real React-provider scenarios now pass in `tests/auth-provider.test.mjs` using ReactDOM/jsdom and mocked fetch. These cover restoration, credential cleanup with preferences preserved, guest StrictMode, login/logout, failed logout, focus/storage re-verification, stale verification, offline startup, delayed logout after login and pending-startup logout. Full frontend suite: 75 passing entries. This does not mark any real-browser row below as passed: no browser is connected, and cookie/CORS/Set-Cookie, actual tabs, layout and hosted OAuth remain unverified.

Use an isolated test database and the two coordinated cookie gates before testing. Do not switch one side independently. Do not use real passwords or copy cookie/CSRF values into reports. Test localhost consistently (do not mix localhost and 127.0.0.1), then configured HTTPS same-site staging origins. No production deployment/DNS change is authorized by this checklist.

| Check | Expected result |
| --- | --- |
| Guest startup | Verify returns unauthenticated; public browsing works; no cached profile enables actions. |
| Signup/login/Google | User appears; responses contain no bearer token; cookie is HttpOnly, host-only, Path=/, SameSite=Lax and Secure on HTTPS. |
| Returning Google user | Existing account reused without 500 or duplicate account. |
| Refresh/direct private route | Server verifies cookie; same user restored without localStorage credential. |
| Browser storage | Old token/profile keys removed; no new credentials stored; preference keys retained. |
| CSRF | Missing/wrong header, foreign/null Origin and another client's CSRF fail before mutation; preflight works. |
| Favorites/listings/uploads/reviews/callbacks | Intended actions work; denied requests produce no writes; multipart uploads retain content type boundary. |
| Messaging | Thread reads and sends work; message-read GET requires CSRF in cookie mode. |
| Password change | Old sessions revoked, current cookie rotated, UI retains verified current identity. |
| Password reset | Old sessions revoked, reset reuse rejected, login with old password fails. |
| Reset email destination | With two CORS origins, generated email points to the single configured PASSWORD_RESET_ORIGIN (first configured origin only if unset), on `/account`; Host/Origin request headers cannot redirect it. |
| Logout | Session revoked and cookies cleared; refresh stays logged out. Simulated DB/network failure shows retry error, not false success. |
| Logout before verification completes | If invoked without an in-memory identity, cookie mode still contacts the server to revoke any HttpOnly session; no false local-only success. |
| Delayed logout/account switch | Delay logout, sign in as another fixture account, then release success/failure. Old UI completion must not clear the newer identity or show its failure. Verify actual cookie response ordering too: the UI guard alone cannot prevent an older Set-Cookie response clearing a newer cookie. |
| Two tabs/account switch | Other tab removes old private UI and verifies new session; stale 401/response cannot overwrite a newer login. |
| Delayed CSRF/request | Session switch or abort prevents pending mutation; no automatic duplicate mutation. |
| Offline/timeouts | No unverified private actions; recovery/focus re-verifies; no infinite spinner or render loop. |
| Cache | Cookie-bearing/auth requests no-store; no cross-user cached data. |
| Legacy credentials | Cookie mode ignores Authorization bearer; database digest cannot authenticate; existing raw sessions follow documented cutover. |
| English/Arabic/RTL/mobile/themes | Current UI, preferences, navigation and layouts preserved. |
| Staging origins | Exact allowlist and credentials header; untrusted origins denied; no wildcard or insecure hosted cookie. |

Automated checks use mocked fetch and Flask clients. They do not prove browser cookie policy, hydration, Google-provider acceptance, multi-tab rendering or PostgreSQL behavior. Complete those checks before claiming transport migration done.

## Automated coverage checkpoint — September 18

`tests/cookie-api.test.mjs` now has 17 transport cases (18 Node test entries including the parent). Additional coverage checks malformed/bootstrap failures and recovery, cancellation isolation, revision changes, no automatic mutation retries, stale-version-free verification, absence of bearer-storage reads, and correct 401 notifications. All 56 frontend entries and 32 backend tests pass. These are not completed rows of the interactive checklist above.

Supported browser discovery returned an empty list. Connect a browser to run the pending interactive checks; do not enable cookie transport on the shared preview solely on the strength of mocked tests. Frontend and backend remain available at localhost ports 3000 and 5000 with the existing bearer transport.
