# MVP staging verification — September 24, 2026

## Completed in this continuation

Authorized scope: MVP operational readiness and existing password-reset email transport. No deployment, hosted settings, DNS, data migration or provider purchase.

`backend/app/routes/auth.py:send_auth_email` previously used SMTP without a socket timeout and without an explicitly verified TLS context. It now uses a 10-second socket timeout and `ssl.create_default_context()` for STARTTLS before authentication. Invalid certificates fail closed; no plaintext fallback or automatic retry. Existing SMTP credentials, port, templates and generic forgot-password response are preserved. This is a per-socket-operation timeout, **not** a total request deadline; DNS and a slow multi-step exchange can still take longer. SMTP delivery remains synchronous, and SMTP acceptance does not establish inbox delivery.

Four tests added in `backend/test_public_journey.py` cover TLS verification and call order, certificate failure without credential transmission/retry, timeout with indistinguishable known/unknown-account JSON responses, and missing configuration without connection. Existing sensitive-error-log tests remain passing. No email was actually sent. Timing-based account enumeration is not solved by equal JSON responses.

Validation: all **117 backend tests PASS**, including installed real video tools; Python compilation and `git diff --check` PASS. Failure-injection log events in the suite are expected. No frontend code changed; frontend tests/lint/types/build were not rerun for this backend-only patch (previous batch: 109 frontend tests and lint/types/build PASS). Local `/listings` returned HTTP 200 and `/api/cars` returned six cars. Backend restarted for the fix. No browser acceptance claimed.

## Hosting discovery and remaining blockers

Used the Vercel skill and connected read-only tool. Authentication completed, but `vercel_list_teams` returned an empty teams list. There is no `.vercel/project.json` in this workspace. This connection therefore did not identify an accessible staging project; it does **not** prove that no project or deployed services exist. No project/env/log values were retrieved, and no Vercel settings were changed.

To continue actual hosted acceptance, provide the existing isolated staging frontend/backend URLs and access through the appropriate connected account. If staging does not exist, choose/approve its creation before provisioning. Configure secrets only in provider settings, never in chat. The previous browser session had no available browser; interactive checks remain pending.

Required staging acceptance:

1. Confirm selected database engine/version, schema compatibility and isolated backup/restore. Never test writes against production.
2. Run the configuration preflight in the target environment; retain only its redacted report.
3. Verify Cloudinary image upload → save listing → reload after backend restart using a disposable staging account; keep signed direct uploads disabled until their separate acceptance gates pass.
4. Verify reset-email inbox delivery and link origin, expiry, single use, session revocation and login with the changed password. An SMTP outage must leave generic responses and redacted errors; no delivery credit from mocks.
5. Browser-test register/login, listing CRUD, search, favorites, seller contact, ownership rejection, Arabic/RTL/themes and mobile navigation.
6. Verify shared limiter/proxy/CORS/cookie rollout configuration, hosted CI, monitoring and rollback before deployment approval.

## Database risks observed, not changed

`backend/app/db.py:_create_postgres_connection` retries certificate/root-certificate errors using `_force_sslmode_require`, removing `sslrootcert` and weakening requested TLS verification. `is_postgres` also treats missing psycopg2 as SQLite despite a configured PostgreSQL URL. These are confirmed code risks, not verified incidents. Before a hosted rollout, establish the actual target trust chain and driver availability, then validate fail-closed corrections in isolated staging. Removing compatibility fallbacks without knowing the deployed certificate requirements could cause a service outage; no database behavior changed here.

## Files and rollback

This continuation changed `backend/app/routes/auth.py`, `backend/test_public_journey.py`, this document, `MVP_LAUNCH_PLAN.md`, `PUBLIC_RELEASE_READINESS.md`, and `ROADMAP_CONTINUATION.md` only. Existing dirty worktree remains uncommitted and intact.

Rollback only the SMTP timeout/context import and call changes, the four new test methods, and this continuation's documentation. Do not reset the entire dirty files. No schema rollback needed. Prefer correcting the SMTP server certificate to disabling peer verification.

Historical overall estimate remains **60/100**. No additional hosted/browser acceptance credit; none of the six MVP gates has full acceptance evidence yet. Next: connect the existing isolated staging target and run the core marketplace acceptance journey.
