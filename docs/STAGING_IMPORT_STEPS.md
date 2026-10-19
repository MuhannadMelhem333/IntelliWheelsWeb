# First staging import — September 24, 2026

## October 19 checkpoint

- Confirmed workspace: IntelliWheels (`tea-darr4l7avr4c73frn89g`). User authorized backing up and replacing the newly created service, not purchasing resources or deploying production.
- Existing service `srv-dbaubalg1s2s73dim6n0` uses the old `MuhannadMelhem333/IntelliWheels` repository, `main`, root directory, `pip install -r requirements.txt`, and `python app.py`. Latest deployment failed. Auto-deploy is enabled. Intended repository is `MuhannadMelhem333/IntelliWheelsWeb`.
- No Render Postgres or Key Value instances were found; external database configuration remains unverified. An isolated staging database must be identified before startup, which can initialize schema. Do not use disposable SQLite storage as a launch database.
- Backups verified locally in ignored `.cache/backup-20261019`: old repository mirror, current committed-history bundle, and 267-file working-source archive. See its `RECOVERY.md`; ignored secrets/databases/uploads are not included, and no commit is asserted to be a verified working deployment.
- Created local `dev` tracking `origin/dev`, preserving all changes. Remote `dev`, `stg`, and `production` were verified at `82de0bc6988f07e68b0fc6cd35529fb23ca00cb3` before preparation. Production remains unchanged.
- Fresh validation: ESLint, TypeScript, production build (24 generated pages), 109 frontend tests, 118 isolated backend tests with real video tooling, Python compilation, and diff whitespace checks passed. Build required network access for configured fonts. Existing Browserslist age warning remains.
- Publication screening covered 219 text files with credential patterns and checked tracked/untracked filenames for local secrets/data. Matches were test fixtures and a documentation example, not a complete secret audit. No backups or environment files are in the publication set.
- Remaining: checkpoint/publish reviewed code through `dev` and hosted CI, arrange reviewed `stg` promotion, confirm isolated database and supporting services, change the existing service settings through a supported Dashboard/API path (the current connector cannot update repository/build settings), then deploy and verify. Do not apply the three-service Blueprint.

The historical instructions below describe the initial preparation; the checkpoint above supersedes their account-discovery status.

Status: prepared locally, **not imported, pushed or deployed**. No paid resource, hosted setting or DNS change made. This guide supersedes the older three-service setup for the first staging exercise.

## What was checked

- Current checkout: `production`, latest commit `82de0bc`, with substantial tracked and untracked work. Only `production` exists as a local branch. Importing the existing remote repository will not include these local improvements.
- Existing `render.yaml` defines three Starter services (paid compute), including production. Do not apply that Blueprint for this staging exercise.
- `recovery-codes.txt` was untracked. Added its name to `.gitignore` without opening, copying or deleting it. Ignoring a file is not a full secret audit and does not remove anything previously published elsewhere.
- `.env`, SQLite databases, local uploads and virtual environments are already ignored. Never use `git add .` as a substitute for reviewing the upload set.

## Do this now

1. Open GitHub and copy the IntelliWheels repository **web URL**. Confirm whether this repository is already connected to deployments in the old Vercel account or Render. Do not push to `production`.
2. Open Render and look for an existing IntelliWheels backend. If present, copy its service dashboard URL and public `https://…onrender.com` URL, and identify its branch and whether it contains real customer data. Do not paste environment values.
3. Send those URLs to Codex. If no backend exists, say “No Render backend.” Do not purchase a plan or create three services from the Blueprint yet.

These facts determine whether we reuse an isolated staging service or create one, and whether pushing a branch will trigger an existing deployment. Production data must not be reused for write tests.

## Git preparation after deployment links are known

Create or check out `dev` without discarding the current work (inspect remote branches first; do not reset an existing branch). Review all intended source/test/docs additions and deletions; scan for secrets and private datasets before staging. Commit the reviewed work on `dev`, then push only after confirming its deployment targets. Run hosted CI and promote the tested commit to `stg` via the established review flow. This guide deliberately provides no blind add/commit/push command for the large dirty worktree.

## Render staging settings, once service creation/cost is agreed

Create **one** isolated Web Service, not the whole Blueprint:

| Field | Value |
| --- | --- |
| Repository | confirmed IntelliWheels repository |
| Branch | tested `stg` commit |
| Root directory | `backend` |
| Runtime | Python |
| Build command | `bash render-build.sh` |
| Start command | `gunicorn run:app --bind 0.0.0.0:$PORT --timeout 120 --workers 2` |
| Health check | `/api/health` |
| Auto-deploy | disable initially; explicitly deploy the reviewed commit |

Securely configure `FLASK_ENV=staging`, an independently generated `SECRET_KEY`, isolated `DATABASE_URL`, `FRONTEND_ORIGIN`, `PASSWORD_RESET_ORIGIN`, `BACKEND_URL`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `RATE_LIMIT_REDIS_URL` and a staging-specific `RATE_LIMIT_NAMESPACE`. Use the actual selected HTTPS frontend/backend origins; do not use guessed URLs, `localhost`, wildcard CORS, production credentials or a production database. Keep credentials out of Vercel public variables. AI remains unverified unless separately configured and tested; no feature has been removed.

Database startup currently performs schema initialization: inspect compatibility and backups **before first start**, not afterward. Database TLS fallback, schema migrations and feature-enforcement configuration still need staged validation; see `MVP_STAGING_VERIFICATION.md`. Cookie auth and direct signed uploads stay gated; their configuration is not enabled simply by adding arbitrary environment flags. Runtime `ffprobe` must be available for videos; current build script does not install it. Missing tooling rejects videos safely but is not full feature acceptance.

Run `python check_release_config.py --component backend` inside the securely configured service environment. A pass proves configuration shape only, not functioning services or launch readiness.

Render Free is distinct from Starter and has operational limits. Verify current cost and SMTP network availability before selecting a plan; the existing application uses SMTP, not an email HTTP API. No paid plan is authorized by this document.

## Vercel import, after Git and backend are ready

1. In the intended Vercel account, choose **Add New → Project**, then import the confirmed repository. Select **Next.js** and the repository root (`./`), not `backend`.
2. Use `npm ci` for install and `npm run build` for build; leave Next.js output settings at their defaults.
3. Set `NEXT_PUBLIC_API_URL=https://<actual-staging-backend-host>/api`. Remove conflicting public API aliases. Public values are baked into the build: changing them requires rebuilding.
4. Use an isolated staging project if needed for the first import, with staging credentials only and no custom domain. Confirm the selected deployment branch is the reviewed staging commit **before starting**. If the import UI cannot select it, stop and arrange the project/branch through supported settings or a preview workflow; do not deploy the old `production` commit by accident.
5. Initial Git imports can create a Vercel **Production-target** deployment even when the project is named “staging.” The name is not isolation or access protection. Check deployment protection availability and verify logged-out access; do not assume the generated URL is private. Proceed only with approved staging-only data and deployment visibility.
6. Vercel's default environments are Production, Preview and Development. A Git branch named `stg` is not automatically a separate environment; non-production branch builds normally use **Preview** variables, with a branch override where configured. **Development** variables are for local tooling, not a hosted `dev` branch. Set the variable in the environment actually being built.
7. Once Vercel supplies the real stable staging frontend URL, set that exact origin in the Render CORS/reset settings, redeploy the backend as needed, then test `/api/health`, `/listings`, direct car routes and the complete account-to-listing journey. No customer launch until acceptance passes.

## Sources and remaining work

- [Vercel Git deployments and branch selection](https://vercel.com/docs/git)
- [Vercel deployment environments](https://vercel.com/docs/deployments/overview)
- [Render pricing](https://render.com/pricing)
- [Render Free service limitations](https://render.com/docs/free)

No application behavior changed in this preparation. Validation: Git ignore rule and diff whitespace checks only; previous 117 backend tests and 109 frontend tests remain the latest test results. Overall historical estimate remains 60/100, not launch approval. Next: identify the repository and existing backend, then prepare a reviewed staging commit and environment.

Rollback: remove only the new `.gitignore` line and these documentation additions if necessary. Prefer retaining the recovery-code exclusion. Nothing external needs rollback.
