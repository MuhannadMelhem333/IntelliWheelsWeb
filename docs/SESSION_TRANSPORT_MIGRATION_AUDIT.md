# Session transport migration audit

Status: audit and baseline characterization complete; cookie migration NOT implemented.

Follow-up: proceeding with recommended same-site custom-domain design; no DNS/hosting changes. Returning Google-user row compatibility and hashing for newly issued sessions are now implemented. The table below records the pre-migration audit; see `SESSION_SECURITY_PROGRESS.md` for current status and legacy-session limitations.

## Confirmed repository behavior

| Area | Evidence | Migration consequence |
| --- | --- | --- |
| Session storage | `backend/app/db.py` PostgreSQL/SQLite `user_sessions` definitions; `auth.py` signup/login/google_auth | Raw bearer token is the primary key. Store a versioned hash instead; do not silently reinterpret old rows or delete production sessions. |
| Frontend storage | `src/context/AuthContext.tsx`: persistAuth, initial effects, login/signup/Google handlers | Token and profile persisted in localStorage. Replace token identity with a non-secret session generation; remove stale-response races without exposing cookie values. |
| Requests | `src/lib/api.ts`: apiRequest, verifySession, logoutUser | Reads several legacy storage keys and sets Authorization; no credentials include. Verification/logout short-circuit without token. All must change together. |
| Authorization | `backend/app/security.py`: require_auth/token_required; direct header readers in auth/favorites/listings | A central cookie/session resolver must replace every header reader, not only decorators. |
| Cookie configuration | `backend/app/__init__.py`: SESSION_COOKIE_* and CORS | Cookie flags exist but custom sessions never set cookies. CORS has credentials disabled; staging is treated as non-production for origin restrictions and Secure flag. |
| UI gates/cache | CarDetailView, MessagesView, PublicRouteShell; apiRequest | Many actions gate on token presence. Browser requests carrying invisible cookies cannot use token presence to decide public-cache eligibility. |
| Rotation | auth.py login, update_profile, reset_password, logout | Login creates a fresh token but preserves other sessions; logout deletes one. Reset revokes all; profile password change does not rotate/revoke sessions. |
| Google | auth.py google_auth | Existing-user code uses `user.get`, incompatible with native sqlite3.Row; needs dedicated mocked-provider regression coverage before migration. Live Google verification untested. |
| Reset | auth.py forgot_password, AccountView | Link is built from FRONTEND_ORIGIN (can be comma-separated). Canonical reset URL must be separated from CORS origin list. |
| Rate limits | security.py rate_limit | Shared process-local IP bucket across endpoints. Baseline reset test initially hit 429 after login/verify; reset uses a separate fixture IP to test reset semantics. This is existing limiter behavior, not a session regression. |

## Deployment design decision

Current browser API requests go directly to the configured backend (`src/lib/config.ts`); `next.config.ts` has no API proxy. `render.yaml` names custom production frontend origins but does not establish deployed API/custom staging domains. Hosting configuration and actual DNS have not been verified or changed.

SameSite=Lax cookies do not accompany cross-site fetches, even with credentials include. Cross-origin credentialed fetches also require an explicit allowed origin and credential support. See [MDN cookie reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie) and [Fetch credentials](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch#including_credentials).

Recommended minimum architecture: direct API requests between same-site HTTPS custom domains (www/api and stg/api-stg under intelliwheels.co); local development uses localhost consistently. Host-only HttpOnly Secure SameSite=Lax Path=/ cookies, no broad Domain attribute. Stable staging handles signed-in acceptance; arbitrary Vercel preview domains need either same-site domains or a separately designed same-origin gateway.

Alternative: same-origin Next.js gateway for authenticated traffic. This adds cookie/header forwarding, request allowlisting, private-cache rules, timeouts and upload-size/streaming constraints. Do not casually proxy existing large uploads through hosting request limits.

User decision required before switching transport: do signed-in previews need to work on raw Vercel/Render hostnames, or can authenticated acceptance use stable custom staging domains? No DNS/deployment action is authorized by this design choice itself.

## Coordinated implementation sequence

1. Confirm origin model; characterize Google returning-user and password-change flows. Separate canonical frontend origin from CORS allowlist.
2. Central session module: opaque random cookies, versioned token hashes, expiry enforcement, issue/revoke/rotate operations. Document existing-session cutover and rollback before production changes.
3. CSRF protection for unsafe methods, including login/signup/Google/logout; exact Origin validation plus session-bound CSRF token/header, public OPTIONS, fail closed. Do not adopt cookie auth before this is implemented.
4. Update all backend readers/issuers and frontend requests/context/UI gates in one coordinated feature. Remove browser bearer fallback and localStorage secrets, keep non-secret preferences. Use session generations for stale 401 handling and private request no-store.
5. Rotate on login and password change; revoke on logout/reset. Clear cookie even if session expired. Explicitly report logout/network failures.
6. Run backend tests, frontend auth/API tests, lint/typecheck/build, browser cookie/CSRF/CORS tests, Google login, reload/multi-tab/logout/reset and mutation coverage. Verify local and staging separately. Production rollout remains approval-only.

## Validation and rollback

18 isolated backend journey/security tests pass. Added login/new-token, verify, current-session logout, reset revocation, reset reuse rejection, old-password rejection and new-password login coverage. No external email/provider calls or preview DB writes. Preview frontend HTTP 200 and backend six cars confirmed.

This audit changes only documentation and the new baseline test. Remove that test and documents to roll back; no runtime/auth configuration changed. Frontend checks were not rerun. Cookie migration, browser acceptance and hosted-origin validation remain pending.
