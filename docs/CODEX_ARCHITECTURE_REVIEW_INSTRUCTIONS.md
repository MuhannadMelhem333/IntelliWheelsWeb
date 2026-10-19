# IntelliWheels Codex Assessment and Modernization Instructions

## Purpose

Use these instructions to assess and improve the IntelliWheels repository safely, incrementally, and without attempting a full-system rewrite in one run.

The repository currently uses:

- Next.js 16 and React 19.2 for the frontend

- Flask 3 for the backend

- PostgreSQL/CockroachDB for production data

- SQLite in local development

- Gemini for AI features

- Cloudinary for production media storage

- Vercel for the frontend

- Render for the backend

- GoDaddy for the `intelliwheels.co` domain

The objective is to move the application from a working prototype toward a secure, maintainable, production-ready system while preserving existing user-facing behavior.

The execution model is continuous: after the initial read-only assessment, Codex should work through the roadmap incrementally and keep going until all non-blocked tasks are complete rather than stopping after a small number of tasks.

---

# 1. Mandatory Operating Rules

## 1.1 Execute the roadmap continuously, one coherent issue at a time

A Codex run should work through the authorized roadmap continuously until all applicable tasks are complete, rather than stopping after only one or a few issues.

Work must still be performed one coherent issue or workstream at a time so changes remain reviewable, testable, and reversible.

Do not mix unrelated changes inside the same patch, such as:

- Frontend refactoring

- Authentication redesign

- Database migration

- Upload redesign

- AI rate limiting

- Deployment changes

Finish and validate the current issue, record its completion, then automatically continue to the next roadmap issue.

Cross-workstream changes are allowed only when they are strictly required to complete the current issue safely and must be documented.

## 1.2 Continue automatically after each completed issue

After completing each issue:

1. Run the relevant checks.

2. Summarize what changed in the running work log or final report.

3. List files changed.

4. Record test/build results.

5. Document remaining risks.

6. Continue automatically to the next applicable issue in the roadmap.

Do not stop merely because one issue, route group, phase subsection, or safe patch has been completed.

Continue until all tasks covered by these instructions are complete, blocked by a genuine technical limitation, or require an action that is explicitly reserved for user approval, such as production deployment, DNS changes, destructive migrations, production data deletion, production environment-variable changes, or adding paid services.

When blocked by one of those approval-only actions, continue with every other independent task that can be completed safely before stopping.

## 1.3 No opportunistic rewrites

Do not modify unrelated code merely because it could be cleaner.

Do not:

- Rename large parts of the repository without necessity

- Replace frameworks

- Replace working dependencies casually

- Reformat the entire codebase

- Rewrite modules outside the authorized scope

- Change API contracts without documenting and coordinating them

- Delete apparently unused code without proving it is unused

- Introduce new infrastructure without explaining the operational cost

## 1.4 Preserve behavior

Before changing a feature, identify its current behavior and preserve it unless the authorized issue explicitly requires a behavior change.

Important behavior to preserve includes:

- English and Arabic support

- Light and dark themes

- Currency selection

- Marketplace, dealer, and insights modes

- Authentication flows

- Car listings

- Dealer profiles

- Favorites

- Reviews

- Messaging

- AI chatbot

- Vision helper

- Listing assistant

- Admin functionality

- Responsive mobile behavior

- Existing public URLs

## 1.5 Never expose secrets

Never print, commit, or copy:

- API keys

- Database URLs

- Session tokens

- Password-reset tokens

- Cloudinary secrets

- OAuth client secrets

- SMTP credentials

- Render or Vercel credentials

- Production environment values

Use environment-variable names and safe placeholders in reports.

## 1.6 Make reversible changes

Prefer:

- Small patches

- Focused commits

- Feature flags where useful

- Compatibility layers during migrations

- Clear rollback instructions

Avoid destructive schema changes or broad rewrites without a migration and rollback strategy.

---

# 2. Required First Run: Repository Assessment Only

The first Codex run must be **read-only assessment work**.

Do not modify application code during the first run.

## 2.1 Inspect

Inspect at least:

### Repository and tooling

- `package.json`

- Lockfiles

- `next.config.*`

- `tsconfig.json`

- ESLint configuration

- Tailwind configuration

- `.github/workflows/`

- `render.yaml`

- `AGENTS.md`

- Environment example files

- Git status and branch structure

### Frontend

- `src/app/`

- `src/components/AppView.tsx`

- `src/components/CarDetailView.tsx`

- `src/components/DealerDetailView.tsx`

- `src/context/AuthContext.tsx`

- `src/lib/api.ts`

- `src/lib/config.ts`

- Client/server component boundaries

- Routing

- State management

- Authentication storage

- Error handling

- Caching

- Accessibility

- SEO

- Bundle risks

### Backend

- Flask app factory

- Database connection and schema initialization

- Authentication routes

- Session handling

- Security decorators

- Debug and admin bootstrap routes

- File upload routes

- Gemini integration

- Rate limiting

- Email/password reset

- Health endpoint

- Error handling

- Logging

### Database

- PostgreSQL/CockroachDB code paths

- SQLite code paths

- Schema differences

- Runtime table creation

- Runtime `ALTER TABLE` statements

- Migration tooling

- Transaction handling

- Indexes

- Constraints

- Connection pooling

### Deployment

- Vercel assumptions

- Render services

- Branch-to-environment mapping

- Environment variables

- Custom-domain assumptions

- Health checks

- CI gates

- Rollback readiness

## 2.2 Validate facts from code

Do not trust architecture documents blindly.

For every important conclusion, cite:

- File path

- Function or component name

- Relevant line range when practical

- Why it is a risk

- Recommended correction

Clearly separate:

- Confirmed findings

- Probable findings

- Unverified assumptions

## 2.3 Produce an assessment report

Create:

```text

docs/CODEX_ARCHITECTURE_ASSESSMENT.md

```

The report must contain:

1. Executive summary

2. Confirmed technology stack

3. Architecture diagram or textual system flow

4. Critical production blockers

5. Security findings

6. Frontend findings

7. Backend findings

8. Database findings

9. AI and cost-control findings

10. Deployment findings

11. Test coverage findings

12. Prioritized remediation roadmap

13. Recommended first atomic issue

14. Files inspected

15. Commands run

16. Uncertainties requiring user input

## 2.4 Assessment continuation condition

After creating the assessment report:

- Present or update the report summary.

- Identify the highest-priority first implementation issue.

- Automatically begin implementation using the prioritized remediation roadmap.

- Continue through subsequent issues and phases without waiting for additional authorization between ordinary development tasks.

The assessment remains read-only until the report is created. After that point, implementation may begin automatically under the safety and approval rules in this document.

---

# 3. Issue Execution Protocol

After assessment, every implementation run must follow this protocol.

## Step 1: Confirm the authorized issue

At the top of the response, state:

```text

Authorized issue: [exact issue]

Out of scope: [related areas that will not be modified]

```

Do not ask for confirmation if the user already explicitly authorized the issue.

## Step 2: Inspect only the relevant code

Read the affected files and their immediate dependencies.

Do not scan and modify the entire repository again unless necessary.

## Step 3: Create an issue plan

Before editing, define:

- Current behavior

- Target behavior

- Files expected to change

- API or schema impact

- Risks

- Test plan

- Rollback approach

## Step 4: Implement incrementally

Use small, understandable changes.

If the issue is larger than one safe patch:

1. Complete the safest coherent portion.

2. Leave the application working.

3. Validate the completed portion.

4. Document what remains.

5. Continue with the next coherent portion.

Do not leave half-migrated behavior across unrelated modules.

## Step 5: Validate

Run the checks relevant to the issue.

### Frontend baseline

```bash

npm ci

npm run lint

npx tsc --noEmit

npm run build

```

Run available frontend tests.

### Backend baseline

```bash

python -m pip install -r backend/requirements.txt

python -m compileall backend

```

Run available backend tests.

### Full-stack issues

Run both sets plus focused smoke tests.

## Step 6: Report progress and continue

Report:

- Summary

- Files changed

- Important implementation decisions

- Validation results

- Known limitations

- Rollback instructions

- Recommended next issue

Then continue automatically with the recommended next issue unless a user-approval-only action is required.

---

# 4. Modernization Roadmap

This is the recommended order. Once the run begins under these instructions, proceed through the phases automatically in this order unless code findings justify a safer sequence.

---

## Phase 0: Assessment

**Scope:** Read-only repository assessment and remediation plan.

**No application-code changes.**

**Stop after report.**

---

## Phase 1: Frontend Architecture

Frontend work must be completed before moving to backend, database, AI, or deployment work unless an immediate security blocker requires otherwise.

However, frontend work must still be divided into atomic issues. Do not refactor the entire frontend in a single patch.

### Phase 1A: Frontend baseline and characterization

Goals:

- Confirm Next.js and React versions

- Confirm App Router usage

- Record existing routes and SPA page keys

- Measure or inspect bundle composition

- Identify client/server boundaries

- Establish tests or smoke checks for current behavior

- Document all frontend environment variables

- Confirm whether the frontend compiles without the backend being online

Do not refactor yet.

After producing the frontend baseline report, continue to the next frontend modernization issue.

### Phase 1B: Introduce route-based page boundaries

The current application reportedly places most UI in `AppView.tsx`.

Refactor one page group at a time.

Recommended order:

1. Static information pages

2. Public listings page

3. Car detail page

4. Dealer list and detail pages

5. Authentication/profile pages

6. Favorites

7. Messages

8. Listing creation and management

9. AI pages

10. Admin pages

For each route migration:

- Preserve the existing UI

- Preserve language and theme behavior

- Preserve mobile behavior

- Use real Next.js routes

- Add route-level loading and error states where appropriate

- Avoid making the whole route a Client Component

- Use small Client Components for interactive behavior

- Maintain redirects or compatibility for old navigation state

- Update internal links to use Next.js navigation

Do not migrate all routes in one patch. Migrate and validate route groups incrementally, then continue automatically to the next group.

### Phase 1C: Break up `AppView.tsx`

After routes are established:

- Extract shared layout components

- Extract header and navigation

- Extract page-specific components

- Extract translation data

- Extract theme and currency logic

- Extract service-mode logic

- Extract upload UI logic

- Extract chatbot state

- Extract admin UI

- Reduce global state

Do not introduce a state-management library unless the code demonstrates a real need.

Prefer React context, URL state, local state, and server data before adding Redux, Zustand, or another global store.

### Phase 1D: Frontend data fetching and caching

Replace blanket `cache: 'no-store'` behavior with endpoint-specific policies.

Suggested policy:

- Static content: static generation

- Makes/models/reference data: long cache

- Public listings: short revalidation

- Dealer public data: short revalidation

- User profile: no-store

- Favorites: no-store

- Messages: no-store

- Admin data: no-store

- Mutations: no-store with explicit refresh/invalidation

Do not cache private user data publicly.

### Phase 1E: Frontend error, loading, and offline behavior

Correct the current optimistic session behavior.

Requirements:

- A network timeout must not be treated as a valid authenticated session.

- An explicit 401 must clear authentication.

- Cached user information may be shown only as clearly limited offline/read-only state.

- Sensitive actions must require a verified session.

- Every major route must have a useful loading state.

- Every major route must have a useful failure state.

### Phase 1F: Frontend quality

Address:

- Accessibility

- Keyboard navigation

- Form labels

- Error messages

- Mobile navigation

- Arabic RTL correctness

- Persisted language selection

- Metadata

- Sitemap

- Robots configuration

- Canonical URLs

- Structured data

- Image optimization

### Phase 1 completion gate

Frontend phase is complete only when:

- The main application no longer depends on one giant SPA shell for all pages.

- Public pages have real URLs.

- Shared behavior remains functional.

- Builds and checks pass.

- Critical flows have automated or documented smoke coverage.

- The frontend work is summarized in `docs/FRONTEND_MODERNIZATION_REPORT.md`.

After frontend completion:

**Proceed automatically to the next roadmap phase after recording frontend completion and passing the relevant checks.**

---

## Phase 2: Authentication and Backend Security

Proceed when reached in the roadmap, subject to the approval-only safety actions defined in this document.

Atomic issues should include:

### Phase 2A: Remove dangerous endpoints

Remove or safely replace:

- Unauthenticated debug endpoints

- Session-token inspection endpoints

- Database-table inspection endpoints

- Weak admin-setup endpoints

- Production-sensitive debug logging

Do not merely hide these routes from Swagger.

### Phase 2B: Secure session transport

Replace browser-accessible bearer tokens in local storage with secure session cookies.

Target cookie properties:

```text

HttpOnly

Secure

SameSite=Lax

Path=/

```

Additional requirements:

- Store only a hash of session tokens in the database

- Rotate sessions after login and password changes

- Revoke sessions on logout and reset

- Add CSRF protection for unsafe methods

- Preserve Google OAuth

- Provide a migration path for existing users

Coordinate the frontend and backend changes within this one authentication issue only.

### Phase 2C: Password hashing

- Confirm current hashing method from code

- Upgrade new passwords to Werkzeug's maintained secure default

- Rehash old hashes after successful login

- Avoid forcing all users to reset passwords unless necessary

### Phase 2D: Security headers and logging

Add and validate:

- Content-Security-Policy

- Strict-Transport-Security

- Permissions-Policy

- Referrer-Policy

- X-Content-Type-Options

- Frame restrictions

Redact secrets, tokens, authorization headers, and password-reset values from logs.

### Phase 2E: Centralized rate limiting

Replace process-local rate limiting with a shared store such as Redis when production scaling requires it.

Define separate limits for:

- Login

- Signup

- Forgot password

- Reset password

- AI endpoints

- Upload-signature endpoints

- Search

- Messaging

- Admin actions

After Phase 2 is complete, record results and continue to Phase 3.

---

## Phase 3: Database Standardization and Migrations

Proceed when reached in the roadmap, subject to the approval-only safety actions defined in this document.

### Preferred target

Use PostgreSQL consistently across:

- Production

- Staging

- Development

- Automated tests

A local PostgreSQL Docker configuration is preferred for development.

### Required work

- Remove schema-name differences between SQLite and PostgreSQL

- Remove manual SQL placeholder translation

- Remove request-time table creation

- Remove request-time schema alteration

- Introduce SQLAlchemy if appropriate

- Introduce Alembic migrations

- Define initial schema migration

- Add indexes and constraints

- Validate transaction behavior

- Add migration tests

- Add a backup and restore procedure

If CockroachDB is retained:

- Use the supported CockroachDB SQLAlchemy dialect

- Review transaction retry behavior

- Test all migrations against CockroachDB

- Do not assume complete PostgreSQL equivalence

Do not perform destructive migrations without:

- Backup

- Data migration script

- Rollback plan

- Explicit user authorization

After Phase 3 is complete, record results and continue to Phase 4.

---

## Phase 4: File Upload Architecture

Proceed when reached in the roadmap, subject to the approval-only safety actions defined in this document.

Target design:

1. Authenticated user requests short-lived signed upload parameters.

2. Browser uploads directly to Cloudinary.

3. Backend stores validated Cloudinary asset metadata.

4. Listing ownership controls asset association.

5. Deleted listings clean up associated assets.

Requirements:

- No production local-filesystem fallback

- Authentication required

- File-count limits

- File-size limits

- MIME and signature validation

- Image dimension limits

- Video duration limits

- Environment-specific Cloudinary folders

- Per-user quotas

- Deletion workflow

- Moderation plan

- Error and retry handling

Suggested limits:

- Images: 10–15 MB each

- Avatars: 5 MB

- Videos: 50–100 MB

- Listing images: 10–20 maximum

After Phase 4 is complete, record results and continue to Phase 5.

---

## Phase 5: AI Reliability, Abuse Prevention, and Cost Control

Proceed when reached in the roadmap, subject to the approval-only safety actions defined in this document.

Required work:

- Move model names to environment variables

- Add per-user and per-IP limits

- Add daily token budgets

- Limit input length and output tokens

- Limit image size

- Add timeouts

- Add safe retry rules

- Log usage without logging sensitive content unnecessarily

- Add graceful provider-failure responses

- Track cost by feature

- Separate chatbot, vision, pricing, and listing-assistant limits

- Test Arabic and English output

- Validate structured JSON output

- Add prompt-injection defenses where tools or private data are involved

Do not change production models only because a newer model exists.

Benchmark candidate models in staging before promotion.

After Phase 5 is complete, record results and continue to Phase 6.

---

## Phase 6: Search and Pricing

Proceed when reached in the roadmap, subject to the approval-only safety actions defined in this document.

### Search

The current “semantic search” must be assessed honestly.

Recommended progression:

1. Database-side filtering

2. PostgreSQL full-text search

3. Trigram similarity for misspellings

4. Optional embeddings for natural-language intent

Do not fetch every car row for every search request at production scale.

Rename the endpoint if it is not genuinely semantic.

### Pricing

Choose one clear product direction:

- Transparent rules-based market estimate, or

- Evaluated machine-learning estimate

For rules-based estimates, return:

- Low

- Expected

- High

- Confidence

- Factors

- Disclaimer

For ML:

- Document dataset

- Use time-aware validation

- Report MAE/MAPE or suitable metrics

- Prevent leakage

- Version the model

- Define fallback behavior

After Phase 6 is complete, record results and continue to Phase 7.

---

## Phase 7: Email and Operational Services

Proceed when reached in the roadmap, subject to the approval-only safety actions defined in this document.

Implement:

- Transactional email provider

- `no-reply@intelliwheels.co`

- `support@intelliwheels.co`

- SPF

- DKIM

- DMARC

- Password reset templates

- Single-use reset tokens

- Expiry and rate limiting

- Delivery failure handling

Preserve existing GoDaddy DNS records when adding Vercel, Render, and email records.

After Phase 7 is complete, record results and continue to Phase 8.

---

## Phase 8: Testing and Observability

Proceed when reached in the roadmap, subject to the approval-only safety actions defined in this document.

### Backend tests

At minimum:

- Signup/login/logout

- Session verification

- Authorization

- Ownership

- Admin permissions

- Password reset

- Upload authorization

- Listing CRUD

- Favorites

- Reviews

- Messaging privacy

- AI error handling

- Migration tests

### Frontend tests

At minimum:

- Authentication states

- Listings and filtering

- Create/edit/delete listing

- Favorites

- Messaging

- Language and RTL

- Theme

- Mobile navigation

- Admin protection

### End-to-end tests

Use Playwright or an equivalent tool for:

- Register/login

- Create listing

- Upload image

- Search

- Favorite

- Message seller

- Dealer application/admin review

### Observability

Add:

- Structured application logs

- Sentry or equivalent error tracking

- Request correlation IDs

- Health checks

- Readiness checks

- Uptime monitoring

- AI usage metrics

- Database-pool metrics

- Alerting thresholds

After Phase 8 is complete, record results and continue to Phase 9.

---

## Phase 9: Deployment and Domain Configuration

Proceed when reached in the roadmap, subject to the approval-only safety actions defined in this document.

The domain is already owned through GoDaddy:

```text

intelliwheels.co

```

Recommended production mapping:

```text

intelliwheels.co       → redirect to www.intelliwheels.co

www.intelliwheels.co   → Vercel production frontend

api.intelliwheels.co   → Render production backend

stg.intelliwheels.co   → Vercel staging branch

api-stg.intelliwheels.co → Render staging backend

```

Recommended environment model:

- Production: hosted frontend, backend, database, and Cloudinary

- Staging: hosted frontend, backend, and isolated non-production data

- Development: local frontend, backend, and PostgreSQL by default

Deployment work must include:

- Exact environment-variable inventory

- CI checks before auto-deploy

- Protected branches

- Required reviews

- Render health checks

- Database pre-deploy migrations

- Rollback runbook

- Backup restore test

- DNS documentation

- TLS verification

- CORS verification

- Smoke tests

- Post-deploy verification

Do not alter GoDaddy nameservers unless required.

Preserve:

- MX

- SPF

- DKIM

- DMARC

- Existing TXT verification records

After Phase 9 is complete, perform a final end-to-end verification, update the completion documentation, and stop only when all remaining non-approval-blocked roadmap work is complete.

---

# 5. Current Priority Order

Unless later code findings justify a change, use this order:

1. Assessment

2. Frontend architecture

3. Remove critical debug/admin exposures

4. Authentication security

5. Database standardization and migrations

6. File uploads

7. AI limits and reliability

8. Tests and observability

9. Email

10. Search and pricing

11. Deployment and domain configuration

Critical security findings may be moved earlier, but Codex must explain why and wait for authorization before changing scope.

---

# 6. Definition of Done for Every Issue

An issue is complete only when:

- The intended change is implemented

- Existing relevant behavior is preserved

- Relevant checks pass

- Tests are added or updated where practical

- No secrets are exposed

- Documentation is updated

- A rollback method is documented

- Known limitations are reported

- No unrelated changes were mixed into the same patch

A successful build alone is not sufficient.

---

# 7. Required Completion Report Format

At the end of every implementation run, use this structure:

```markdown

# Completed Issue

## Authorized scope

[Exact issue completed]

## Summary

[What changed and why]

## Files changed

- `path/to/file`

- `path/to/file`

## Behavior preserved

- [Existing behavior verified]

## Validation

- `npm run lint`: PASS/FAIL

- `npx tsc --noEmit`: PASS/FAIL

- `npm run build`: PASS/FAIL

- Backend checks: PASS/FAIL

- Tests: PASS/FAIL

## Security impact

[Security improvement or remaining concerns]

## Database/API impact

[None, or exact changes]

## Rollback

[How to revert safely]

## Remaining work in this phase

[Items not yet completed]

## Recommended next issue

[One issue only]

STATUS: Continue automatically to the next applicable roadmap issue unless blocked by an approval-only action.

```

---

# 8. Prohibited Behavior

Codex must not:

- Combine all roadmap items into one giant unvalidated patch

- Stop unnecessarily after completing an ordinary issue when more roadmap work remains

- Deploy to production without explicit permission

- Modify GoDaddy DNS without explicit permission

- Change production environment variables without explicit permission

- Delete production data

- Run destructive migrations without explicit permission

- Expose secret values in output

- Change API contracts silently

- Replace PostgreSQL/CockroachDB based only on preference

- Upgrade Gemini models without staging benchmarks

- Add paid services without identifying expected cost

- Claim tests passed without running them

- claim an issue is fixed when only documentation changed

- Ignore failing checks

- Hide incomplete work behind broad summaries

---

# 9. Initial Codex Command

Use the following instruction for the first run:

```text

Read CODEX_ARCHITECTURE_REVIEW_INSTRUCTIONS.md and follow it strictly.

Begin with Phase 0: perform a read-only assessment of the IntelliWheels repository.

Create docs/CODEX_ARCHITECTURE_ASSESSMENT.md.

Do not modify application code until the Phase 0 assessment report has been created.

Validate architecture claims directly against the repository.

Report confirmed findings with file references.

Identify the first atomic implementation issue, then automatically continue through the modernization roadmap one coherent issue at a time.

Run the relevant validation after each issue and phase.

Do not stop after only a few tasks. Continue until the roadmap is complete, a genuine technical blocker prevents further progress, or an approval-only action is required.

Do not perform production deployment, GoDaddy DNS changes, production environment-variable changes, destructive migrations, production data deletion, or paid-service adoption without explicit user permission. If one of these blocks a specific task, continue all other independent work first.

```

---

# 10. Example Command for Starting Frontend Work Later

If manually resuming or narrowing the work later, an instruction may be used such as:

```text

Continue under CODEX_ARCHITECTURE_REVIEW_INSTRUCTIONS.md.

Resume from Phase 1A: frontend baseline and characterization, then continue through subsequent roadmap work automatically.

Do not refactor routes yet.

Do not modify backend, database, authentication, uploads, AI, deployment, or DNS.

Create or update docs/FRONTEND_BASELINE.md.

Run the frontend checks.

Report findings, record validation, and continue.

```

For subsequent frontend work, still handle one route group or coherent frontend issue per patch, but continue automatically after validating each one.

Example:

```text

Begin with the migration of static information pages from AppView.tsx into Next.js App Router routes, validate it, then continue to the next frontend route group.

Preserve all current content, translations, styling, theme behavior, and navigation.

Do not migrate listings, authentication, messages, AI, admin, backend, or database code.

Run lint, typecheck, build, and relevant tests.

Report results and continue to the next applicable roadmap issue.

```