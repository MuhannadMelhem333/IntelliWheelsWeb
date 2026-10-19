# MVP launch plan — September 24, 2026

Priority change requested by the owner: deliver a functioning minimum viable marketplace, then improve minor features after launch. Do not make completion of every modernization phase a prerequisite for MVP.

## Proposed launch scope — awaiting feature choice

Browse/search/filter cars, view car details, accounts, create/edit/remove listings with images, favorites, and seller contact. Retain English/Arabic, RTL, themes and mobile support. Proposed deferrals: AI tools, videos, advanced dealer/analytics flows. The user has been asked to choose core-only versus all-current-features; **no feature has been removed or disabled on that assumption**.

## Necessary launch gates

September 24 continuation: SMTP now has a socket timeout and verified STARTTLS; 117 backend tests pass. Vercel read-only discovery returned no accessible teams and no local project link exists, so isolated staging is still unidentified, not proven absent. See `MVP_STAGING_VERIFICATION.md` for exact evidence, remaining database TLS risks, acceptance steps and rollback.

| Gate | Current evidence | Required acceptance |
| --- | --- | --- |
| Core journey | Disposable API tests and frontend helper/mounted tests pass | Real browser register/login, image upload, save/reload, search, favorite, seller contact, ownership rejection |
| Persistent data | Local SQLite works | Selected hosted database schema compatibility, backup and restore on isolated staging; no destructive production migration |
| Persistent images | Validated server-upload path, ownership ledger and quotas implemented locally | Actual Cloudinary credentials/persistence, reload after restart, target-schema migration and enforcement settings verified |
| Accounts/security | Access controls, hashing, reset/session machinery tested; cookie rollout gated | Login/logout/reset email delivery, session threat review, real proxy/shared limiter validation; secure deployment configuration |
| Build and routing | Automated checks pass; public API alias defect fixed | Matching deployed frontend/backend origins, HTTPS/CORS, navigation and mobile/RTL acceptance |
| Operations | CI test execution configured | Hosted CI run/enforcement, monitoring, owner/support contact, rollback drill and explicit deployment approval |

A working existing server-upload path can satisfy MVP media needs. Direct browser uploads, automatic media deletion, a full ORM rewrite, expanded analytics and additional refactoring are **not** inherently launch gates. Keep unverified features gated. Do not relax authorization, persistent storage or recovery requirements merely to improve a percentage.

## Execution batches

### September 26: reviewed simplification integrated

Graphify follow-up: generated a local, code-only frontend dependency map with `graphify extract src --code-only --no-cluster --out .cache/frontend-map --max-workers 2`. Output: `.cache/frontend-map/graphify-out/graph.json`, 400 nodes / 1,014 relationships from 90 code files; `globals.css` was skipped as unsupported. No provider/LLM calls or semantic tokens (0 input / 0 output); clustering, community scores and HTML were deliberately not generated. `explain PublicRouteShell` identifies route imports and its auth/preferences/unread-count dependencies; `explain API_BASE_URL` identifies the API and cookie-session clients. Diagnostic reports one dangling edge, 60 external references and seven potential same-endpoint edge collapses. Treat this as a navigation aid, not complete proof of absence or runtime correctness. Cross-check source before changing dependencies. Regenerate after source changes; the ignored cache is disposable and never a deployment prerequisite. No application code changed in this follow-up, so previous test results remain the latest. Staging still needs the owner's existing Render service URL or confirmation that none exists.

Use Ponytail review to identify unnecessary code, Agent Skills simplification/TDD to verify removal, and deployment checks for launch gates. Do not create extra frameworks, graphs or architecture projects merely because a skill is installed. Cleanup is a bounded preparation step, not a replacement for staging acceptance.

Completed: removed eight unreferenced frontend files: `src/lib/{vehicleDatabase,catalog,mockData}.ts` and `src/components/layout/{AppHeader,AppShell,DesktopNavigation,MobileNavigation,SettingsControls}.tsx`. References existed only inside this unused group (plus historical comments/docs). Active `PublicRouteShell`, `PublicHeader`, `AppFooter`, stored preferences and API-backed listing reference data remain unchanged. Exact deleted contents are backed up locally in ignored `.cache/cleanup-20260926/` using their unique basenames; restore each to its original path if needed. This includes untracked shell files that Git alone cannot restore.

Separately removed the unused `joblib` runtime import, `price_model` field, loader and estimate-time call from `backend/app/services/ai_service.py`. Pricing remains the same rules-based JOD calculation. Training scripts, model artifacts, dependencies, Gemini behavior and APIs are unchanged. Added one regression in `backend/test_public_journey.py`: it failed before removal because model deserialization occurred, then passed while preserving the exact Toyota fixture estimate. Rollback only these loader hunks and the new test, not the existing dirty files in full.

Validation: 109 frontend tests, 118 backend tests (real video tools included), TypeScript, ESLint, Python compilation and production build (24 pages) PASS. Existing Browserslist dataset-age warning remains. No interactive or hosted acceptance credit. No commit, push, deployment, database or hosted configuration change. Overall estimate stays 60/100.

Repository remote identified locally as `https://github.com/MuhannadMelhem333/IntelliWheelsWeb`; remote-tracking refs include `dev`, `stg`, and `production` (not freshly fetched). Current checkout remains `production` with previous work preserved. Next launch task: confirm Render service/branch/data isolation, prepare reviewed work on `dev`, then deploy the tested `stg` commit. Do not blindly push production or assume old-account deployment links are absent. Follow `STAGING_IMPORT_STEPS.md`; the remaining owner input is the existing Render backend URL or confirmation that none exists.

1. **Launch configuration correctness**: fix API variable mismatch, prevent build-time data imports, add secret-safe preflight and regression tests (implemented in this batch).
2. **Core staged journey**: verify actual database/image/email services, migration/backup/restore, then browser account-to-listing-to-contact flow. Fix discovered blockers together. Needs an isolated staging target and a connected browser; never paste credentials into chat.
3. **Launch acceptance**: review unresolved security issues, mobile/RTL and failure cases, validate hosted CI/monitoring/rollback, then request approval for deployment/DNS only when ready.

No expectation of a fixed 3–5% per run: finish coherent batches, reuse validation, avoid more optional upload tooling while these acceptance gates remain open. The historical 60/100 estimate covers the broader website roadmap; it is not an MVP completion metric. Do not silently relabel it as a higher percentage after narrowing scope. Report completed/remaining MVP gates alongside it until the scope is agreed and measured.

## Configuration preflight

Run in each target's securely provisioned process environment:

```text
python backend/check_release_config.py --component frontend
python backend/check_release_config.py --component backend
```

This tool does not load .env, import Flask, connect to services, mutate data or print values. Exit 1 means configuration failures; exit 0 means only syntactic/presence checks passed, **never launch approval**. It checks public API aliases/conflicts, hosted mode, obvious secret weakness, PostgreSQL-family URL presence, HTTPS origins, durable image storage credentials, reset-email settings and shared limiter settings appropriate to the existing two-worker deployment. It does not prove credential validity, secret entropy, TLS/database security, runtime feature gates, working email, CORS, proxy trust or schema safety.

The local terminal run correctly reported missing hosted configuration. Hosted account state was not queried, so this is not evidence that those services are absent remotely.

## Changes in this batch

- `src/lib/config.ts`: supports documented `NEXT_PUBLIC_API_URL`; existing `NEXT_PUBLIC_API_BASE_URL` remains highest priority. Older aliases/local fallback retained. Avoid conflicting aliases. Public variables are build-time configuration: rebuild when changing them.
- `backend/render-build.sh`: removes dormant automatic SQL-import invocation. Its target script is absent, so current builds previously skipped it; removal prevents a future reintroduced script from mutating data as a build side effect. Runtime schema initialization still exists; this is not a completed database migration refactor.
- `backend/check_release_config.py`, `backend/test_release_config.py`, `tests/api-config.test.mjs`, `.gitignore`, `.github/workflows/ci.yml`: configuration validation/tests and CI test inclusion.
- This plan, roadmap and readiness logs document the priority change without assuming feature removal.

Validation: 109 frontend tests and 113 backend tests PASS; TypeScript, project ESLint, Python compilation, CI YAML/wiring and whitespace checks PASS. Backend suite includes real video tools. Production build PASS (24 pages; existing Browserslist age warning). No commits, push, deployment, database changes, hosted environment changes or DNS actions.

Rollback: remove only the new public alias and its tests, the standalone preflight/tests/CI entry, and these batch-specific documentation changes. Keep prior work. Reintroducing automatic build imports is not recommended; schema/data operations belong to explicit reviewed workflows.
