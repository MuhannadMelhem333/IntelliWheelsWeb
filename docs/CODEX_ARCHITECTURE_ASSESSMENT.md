# IntelliWheels Architecture Assessment (Phase 0)

Assessment date: 2026-07-20  
Scope: read-only repository assessment. No application code, deployment configuration, environment variables, or data were changed.

> Implementation status (2026-07-20): the Phase 2A issue recommended by this assessment has been completed. The debug and temporary admin-setup routes documented below were removed from `backend/app/routes/system.py`. Findings in this report describe the repository state at assessment time.

## Executive summary

IntelliWheels is a Next.js App Router frontend backed by a Flask API. The repository confirms the intended major technologies, including React 19, Flask 3, direct SQLite/PostgreSQL/CockroachDB support, Gemini, Cloudinary, Render service definitions, and GitHub Actions CI.

The most urgent confirmed risks are exposed diagnostic/admin-setup API routes, browser-accessible bearer session tokens, and unauthenticated upload endpoints. The frontend is also predominantly a client-rendered SPA shell: `AppView.tsx` is 5,369 lines and the root page is explicitly a Client Component. Database schema management is performed during application startup and differs materially by database engine.

**Recommended first atomic issue:** remove or safely replace the dangerous debug and temporary admin-setup endpoints in `backend/app/routes/system.py` (Phase 2A). This narrowly scoped security issue should precede frontend work because the exposed endpoints can disclose session/user data and allow privileged changes when their weak shared-secret check is satisfied.

## Confirmed technology stack

| Area | Confirmed implementation |
| --- | --- |
| Frontend | Next `^16.0.7`, React/React DOM `19.2.0`, TypeScript, Tailwind 3, ESLint 9 (`package.json:5-30`) |
| Frontend architecture | Next App Router under `src/app`; root page renders `AuthProvider` and `AppView` (`src/app/page.tsx:1-12`) |
| Backend | Flask app factory with nine registered blueprints (`backend/app/__init__.py:12-116`) |
| Data | SQLite default; PostgreSQL/CockroachDB via `psycopg2` when `DATABASE_URL` is set (`backend/app/db.py:57-60`, `247-287`) |
| AI | `google-generativeai` integration and local price-model artifact; Gemini model candidates are in source (`backend/app/services/ai_service.py:14-24`) |
| Media | Cloudinary SDK is a backend dependency; API falls back to local storage (`backend/requirements.txt:15`, `backend/app/routes/system.py:403-445`) |
| Observability | Sentry Next.js wrapper and client/edge/server config files; GA4 is embedded in the root layout (`next.config.ts:52-73`, `src/app/layout.tsx:190-204`) |
| Hosting/CI | Three Render backend services and GitHub Actions frontend lint/typecheck/build plus limited Python compilation (`render.yaml:6-80`, `.github/workflows/ci.yml:3-57`) |

## System flow

```text
Browser
  -> Next.js App Router (root Client Component -> AuthProvider -> AppView)
  -> fetch with Authorization: Bearer <localStorage token>
  -> Flask /api blueprints
  -> SQLite locally OR direct/pool-backed PostgreSQL/CockroachDB
  -> Gemini API / Cloudinary (when configured)

Git push (dev, stg, production)
  -> GitHub Actions checks
  -> Render backend service selected by branch
```

## Critical production blockers

1. **Public debug routes expose sensitive session diagnostics.** `debug_verify` accepts a token in the URL and returns it plus session data (`backend/app/routes/system.py:93-153`). `debug-sessions` is unauthenticated and returns token prefixes, user IDs, and timestamps (`189-215`). `debug-tables` exposes database table inventory/counts (`155-187`). URLs can also be retained in logs, history, and proxies. Recommended correction: remove these routes or replace them with properly authorized, non-sensitive operational diagnostics.

2. **Temporary admin-setup routes use only the first 16 characters of `SECRET_KEY` as a request-supplied secret.** The routes list users (including password-hash previews), reset passwords, make users admins, and inspect sessions (`backend/app/routes/system.py:223-318`). Recommended correction: remove them from deployed code and use a controlled, audited bootstrap process.

3. **Upload endpoints are unauthenticated and accept files based on filename extensions.** Neither `upload_image` nor `upload_video` calls an authentication helper (`backend/app/routes/system.py:385-516`); validation is extension-only (`17-45`, `400-401`, `462-463`). Recommended correction: defer to the authorized upload workstream; require auth/ownership and validate MIME/content and quotas.

## Security findings

### Confirmed

- **Bearer tokens are stored in `localStorage` and supplied through the Authorization header.** `persistAuth` stores the token (`src/context/AuthContext.tsx:169-181`); API requests recover it automatically from browser storage and attach it as Bearer authentication (`src/lib/api.ts:44-78`). The backend stores the raw token as the primary key of `user_sessions` and queries it directly (`backend/app/db.py:337-344`, `backend/app/routes/auth.py:64-91`). This increases impact of XSS or client-device compromise. Recommended correction: Phase 2B secure HttpOnly-cookie sessions, hashed server-side session tokens, rotation/revocation, and CSRF protection.

- **The client logs token previews and local-storage keys.** Examples include `AuthContext` initial load and persistence logs (`src/context/AuthContext.tsx:80-81`, `169-180`) and API 401 diagnostics (`src/lib/api.ts:123-127`). Recommended correction: remove/redact authentication diagnostics in the security logging issue.

- **Session state can be treated as valid during a failed background validation.** A stored user causes `sessionValidated` to be set true before verification; a network failure retains that state (`src/context/AuthContext.tsx:121-159`). Recommended correction: Phase 1E must represent this as an explicitly limited offline/read-only state, not verified authentication.

- **Rate limiting is in-process and IP-header based.** `_rate_limit_store` is a Python `defaultdict`, and the limiter trusts `X-Forwarded-For` (`backend/app/security.py:130-172`). Render starts two Gunicorn workers (`render.yaml:15`), so limits are per process and reset on restart. Recommended correction: Phase 2E shared rate limiting with trusted proxy configuration.

- **Security headers are incomplete.** Flask adds frame, MIME, legacy XSS, and referrer headers but no CSP/HSTS/Permissions-Policy (`backend/app/security.py:222-232`). Next adds some headers (`next.config.ts:20-40`), but frontend headers cannot protect direct Flask API responses. Recommended correction: Phase 2D, after endpoint removal.

### Probable / requires deployment confirmation

- The actual reachable public API may expose the listed routes if the production service runs this revision. Repository inspection cannot determine deployed commit, route firewalling, or external access controls.

## Frontend findings

### Confirmed

- **The primary application remains a monolithic client-side shell.** `src/app/page.tsx:1-12` is a Client Component and mounts `AppView`; `AppView.tsx` has 5,369 lines. Only dynamic car and dealer detail pages exist as additional App Router pages (`src/app/cars/[id]/page.tsx:1-16`, `src/app/dealers/[id]/page.tsx:1-15`); most UI page state is persisted in `sessionStorage` (`src/components/AppView.tsx:772-782`). This limits route-level loading/error boundaries, server rendering, URL ownership, and isolated testing. Recommended correction: Phase 1A characterization first, then one route group per Phase 1B issue.

- **All API requests use `cache: 'no-store'`.** The shared API helper sets it for every request (`src/lib/api.ts:84-99`). Recommended correction: Phase 1D endpoint-specific public/private caching policies.

- **Client/server boundaries are broad.** `AuthContext` is explicitly client-side (`src/context/AuthContext.tsx:1`) and is mounted separately by every current page. Detail views should be examined during their authorized route migration; no refactor was performed.

- **SEO foundations exist but are global.** The root layout defines metadata, JSON-LD, GA4, robots, sitemap, and manifest support (`src/app/layout.tsx:23-172`, `src/app/robots.ts`, `src/app/sitemap.ts`, `src/app/manifest.ts`). Dynamic page-specific metadata was not found in the two current detail routes. Recommended correction: address during route-based public-page work.

- **Bilingual/RTL behavior is client controlled rather than document-level by default.** The root document is fixed at `lang="en"` (`src/app/layout.tsx:180`). RTL behavior needs a focused behavior characterization before refactoring.

### Unverified

- Bundle size/composition was not measured because no build/analyzer run was authorized or necessary for this read-only assessment.
- Keyboard, screen-reader, visual RTL, and responsive behavior require browser-based/manual validation.

## Backend findings

### Confirmed

- The app factory creates upload directories and initializes the complete database schema at startup (`backend/app/__init__.py:57-81`, `backend/app/db.py:303-310`). This couples service startup to schema mutation.

- Flask CORS allows all origins outside `FLASK_ENV=production`; production origins come from `FRONTEND_ORIGIN` (`backend/app/__init__.py:69-76`). Cookies are not presently used for API auth (`supports_credentials=False`), consistent with bearer tokens.

- Password hashes are created with explicit PBKDF2-SHA256 iterations (`backend/app/routes/auth.py:171`, `362`, `505`). This is not reported as a current plaintext-password defect; hash migration policy remains unverified.

- Password-reset tokens are stored raw and embedded in a query parameter in the reset URL (`backend/app/routes/auth.py:411-455`). They are deleted and sessions invalidated when reset succeeds (`504-514`). Recommended correction: include token hashing/redaction in the authorized authentication workstream.

- Operational logging is implemented with `print` across authentication, database, and AI paths (for example `backend/app/routes/auth.py:293-299`, `backend/app/db.py:174-180`, `backend/app/services/ai_service.py:371-375`), rather than structured logging and systematic redaction.

## Database findings

### Confirmed

- **No migration framework or migration directory is present.** Schema creation and incremental alterations are code paths in `backend/app/db.py`; PostgreSQL runs `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` at startup (`471-479`) and SQLite attempts ALTER statements, suppressing errors (`653-665`). Recommended correction: Phase 3 migration tooling with a baselined schema and rollback plan.

- **SQLite and PostgreSQL schemas/query contracts differ.** `messages.py` explicitly documents PostgreSQL `buyer_id`/`seller_id`/`car_id` versus SQLite `user1_id`/`user2_id`/`listing_id` (`backend/app/routes/messages.py:13-76`, `91-126`). The database wrapper translates placeholders and selected SQLite constructs (`backend/app/db.py:78-157`). Recommended correction: standardize supported schema and test it before schema changes.

- **PostgreSQL has a 1–10 direct driver connection pool.** It is created in-process (`backend/app/db.py:229-245`) and checked out per Flask request (`247-287`). SQLite opens a per-context local file connection. Environment-specific behavior must be tested against each supported production engine.

- **Indexes and constraints are only partially demonstrated by the runtime DDL.** The SQLite schema has several primary/unique/foreign-key constraints (`backend/app/db.py:502-650`), but no explicit non-primary `CREATE INDEX` statements were found in the inspected database module. Query-plan and production index adequacy are unverified without data/workload access.

## AI and cost-control findings

### Confirmed

- Gemini model fallback names are embedded in source, although an optional text-model environment variable exists (`backend/app/services/ai_service.py:17-24`, `62-67`).
- Guest callers can invoke `/chatbot`; it has input/history/image-size caps but no rate-limit decorator or usage budget (`backend/app/routes/ai.py:8-44`). `/price-estimate` and `/semantic-search` likewise have no rate-limit decorator (`56-99`). Recommended correction: Phase 5 per-feature user/IP limits, budgets, timeouts, and usage telemetry.
- The endpoint named semantic search fetches every car row and scores it in application memory (`backend/app/services/ai_service.py:382-394`). This is a scalability risk and does not establish embedding/vector search. Recommended correction: Phase 6, beginning with database filtering/full-text search; retain or rename behavior based on an honest product definition.

### Unverified

- Actual Gemini model availability, provider costs, API quotas, latency, and production usage cannot be determined from repository source.

## Deployment findings

### Confirmed

- `render.yaml` defines `production`, `stg`, and `dev` backend services and maps each to the matching branch (`render.yaml:6-80`). It requires `DATABASE_URL`, `GEMINI_API_KEY`, and `SECRET_KEY` as dashboard-managed values.
- CI runs on the same three branches and pull requests to `production`/`stg` (`.github/workflows/ci.yml:3-8`). It runs `npm ci`, lint, TypeScript, and build; backend coverage is limited to installing requirements and compiling three files (`24-57`).
- Render invokes Gunicorn with two workers and a 120-second timeout (`render.yaml:15`, `40`, `65`). No Render health-check field is defined in the inspected manifest, although `/api/health` exists (`backend/app/routes/system.py:51-91`).
- Frontend API-base normalization recognizes several environment variable names but **not** `NEXT_PUBLIC_API_URL` (`src/lib/config.ts:1-15`), while CI supplies `NEXT_PUBLIC_API_URL` (`.github/workflows/ci.yml:35-36`). The production build can therefore fall back to `http://localhost:5000/api` unless another supported variable is configured. Recommended correction: investigate and correct only in a later, explicitly authorized deployment/frontend configuration issue.

### Unverified assumptions requiring deployment access

- Vercel project branch mapping, actual frontend environment-variable names, Render health-check settings, database isolation, custom-domain/DNS/TLS records, protected branches, backups, deploy hooks, and rollback procedures are not represented conclusively in the repository.

## Test coverage findings

No Jest, Vitest, Playwright, pytest configuration, test directory, or migration test suite was found by repository file inventory. `package.json` exposes only dev/build/start/lint scripts (`package.json:5-10`). CI includes lint/typecheck/build and limited backend syntax compilation, not behavioral tests (`.github/workflows/ci.yml:24-57`).

## Prioritized remediation roadmap

1. **Phase 2A — Remove dangerous debug and admin-setup endpoints** (recommended first atomic issue).
2. **Phase 1A — Frontend baseline and characterization**: document current routes/page keys, client boundaries, public URLs, and smoke coverage; do not refactor yet.
3. **Phase 1B/1C — Route and component decomposition**: migrate one public page group at a time, then reduce `AppView` deliberately.
4. **Phase 1D/1E/1F — Frontend data, session-state UX, and quality**: caching policy, verified/offline state semantics, accessibility/RTL/SEO detail work.
5. **Phase 2B–2E — Authentication/session transport, password transition, headers/logging, and shared limiting.**
6. **Phase 3 — Standardize database development/production path and introduce migrations.**
7. **Phase 4–9 — Upload design, AI limits, testing/observability, email, search/pricing, and deployment/domain work** in the authorized sequence.

## Recommended first atomic issue

**Authorized issue proposal:** Phase 2A only — remove or safely replace the unauthenticated debug endpoints and temporary admin-setup endpoints in `backend/app/routes/system.py`.

Target routes: `/api/debug-verify/<token>`, `/api/debug-tables`, `/api/debug-sessions`, and `/api/admin-setup/*` (`backend/app/routes/system.py:93-318`). Out of scope: session-cookie migration, general authentication redesign, database schema changes, uploads, AI controls, frontend refactoring, Render/Vercel/DNS changes, and all other roadmap issues.

## Files inspected

- Repository/tooling: `AGENTS.md`, `package.json`, `package-lock.json`, `next.config.ts`, `tsconfig.json`, `eslint.config.mjs`, `tailwind.config.ts`, `.gitignore`, `.github/workflows/ci.yml`, `render.yaml`.
- Frontend: all `src/app` route/config files, `src/components/AppView.tsx`, `CarDetailView.tsx`, `DealerDetailView.tsx`, `InfoPages.tsx`, `DealerMap.tsx`, `src/context/AuthContext.tsx`, `src/lib/api.ts`, `config.ts`, `types.ts`, and route/file inventory.
- Backend: `backend/run.py`, `backend/app/__init__.py`, `db.py`, `security.py`, all route modules, `services/ai_service.py`, `requirements.txt`, `render-build.sh`, and backend file inventory.
- Documentation: `docs/CODEX_ARCHITECTURE_REVIEW_INSTRUCTIONS.md`.

## Commands run

- `Get-Content -Raw docs\CODEX_ARCHITECTURE_REVIEW_INSTRUCTIONS.md`
- Read-only Git status/branch/file inventory commands.
- Read-only, line-numbered inspections of the configuration, frontend, backend, database, route, security, and AI files listed above.
- Read-only `rg` searches for source size, client storage/navigation, API calls, routes/decorators, schema DDL, test/migration configuration, and environment examples.

No build, lint, typecheck, database initialization, application server, upload, network, or deployment command was run. Therefore this report does not claim that checks pass.

## Uncertainties requiring user input

- Which commit is deployed to production/staging and whether any route-level protection exists outside this repository.
- Whether `NEXT_PUBLIC_API_URL` is the intended frontend environment variable in Vercel, or a supported alternative is configured.
- The production database engine/version, data volume, backup/restore posture, and whether CockroachDB remains a supported target.
- Cloudinary production configuration, account limits, desired retention/deletion policy, and whether local upload fallback is currently in use.
- Gemini quota/billing limits, production model selection, and acceptable guest AI usage policy.
- Required availability, recovery objectives, and ownership of Vercel, Render, DNS, and email-provider operations.

**STOP: Awaiting explicit authorization.**
