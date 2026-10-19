# Deployment Setup Guide

> September 24 staging preparation: follow `STAGING_IMPORT_STEPS.md` before importing. The local working branch is currently `production` with substantial uncommitted work. Do not push it or apply the three-service Blueprint blindly. Example service URLs below are placeholders, not verified deployments. Starter is paid; no hosting plan or database provider has been selected in this preparation.

## Password-reset destination

Backend `PASSWORD_RESET_ORIGIN` is an optional single canonical frontend origin (for example, `https://www.intelliwheels.co` in production). It is separate from `FRONTEND_ORIGIN`, which remains the comma-separated CORS allowlist. If unset, reset links use the first nonempty configured allowlist origin. Links target `/account?reset_token=...`. Use an environment-matched HTTPS origin with no path, query, fragment or credentials; HTTP loopback is allowed only in development. Invalid configuration now fails startup instead of sending malformed reset links. No hosted values have been changed automatically.

Cookie authentication remains gated off. Raw Vercel/Render cross-site preview URLs shown in older setup examples are not acceptance evidence for SameSite=Lax cookie authentication; use the same-site design and checks in `SESSION_COOKIE_MANUAL_QA.md` before coordinated cutover.

## Git flow

```
dev ──► stg ──► production
```

All changes go to `dev` first. Muhannad Melhem tests on `stg`. Once approved, merge to `production`.

## Repo changes already applied

| File | Change |
|------|--------|
| `.github/workflows/ci.yml` | Branches updated to `production`/`stg`/`dev` |
| `render.yaml` | 3 services — `intelliwheels-backend-{prod,stg,dev}` — each deploys from its branch |
| `AGENTS.md` | Documents branching workflow, Vercel/Render setup, and CI pipeline |

## Vercel (frontend) — one project, 3 environments

### Step 1: Import and configure
1. Go to [vercel.com](https://vercel.com) → **Add New Project** → Import your GitHub repo
2. **Project Settings → Git → Production Branch**: set to `production`
3. Vercel auto-deploys `production` and creates preview deployments for every push to any branch

### Step 2: Set environment variables

| Environment | `NEXT_PUBLIC_API_URL` |
|-------------|----------------------|
| **Production** | `https://intelliwheels-backend-prod.onrender.com/api` |
| **Staging** | `https://intelliwheels-backend-stg.onrender.com/api` |
| **Development** | `https://intelliwheels-backend-dev.onrender.com/api` |

1. Go to **Project Settings → Environment Variables**
2. Add `NEXT_PUBLIC_API_URL` with the corresponding value for each environment
3. Ensure each environment (Production, Preview) has the correct value

### Step 3: Note the URLs
After first deployment, you'll get URLs like:
- **Production**: `https://www.intelliwheels.co` (your custom domain)
- **Staging**: `https://intelliwheels-git-stg-xxxxx.vercel.app`
- **Development**: `https://intelliwheels-git-dev-xxxxx.vercel.app`

Copy these — you'll need them for the Render backend's `FRONTEND_ORIGIN`.

---

## Render (backend) — 3 services per `render.yaml`

### Option A: Use the updated `render.yaml` (IaaC)
1. Go to [render.com](https://render.com) → **Dashboard → New + → Infrastructure as Code (IaaC)**
2. Paste the contents of `render.yaml` from this repo
3. This creates 3 services:

| Service | Branch | `FLASK_ENV` |
|---------|--------|-------------|
| `intelliwheels-backend-prod` | `production` | `production` |
| `intelliwheels-backend-stg` | `stg` | `staging` |
| `intelliwheels-backend-dev` | `dev` | `development` |

### Option B: Create services manually
Create 3 Web Services, each pointing to a different branch. For each:
- **Root Directory**: `backend`
- **Build Command**: `bash render-build.sh`
- **Start Command**: `gunicorn run:app --bind 0.0.0.0:$PORT --timeout 120 --workers 2`
- **Python Version**: 3.11.9
- **Plan**: choose explicitly after checking current pricing; Starter is paid, not the Free instance type.

---

## Environment variables per service

These must be set in the Render dashboard for each service. Secrets (`sync: false`) are not stored in `render.yaml`.

### `intelliwheels-backend-prod`

| Variable | Value |
|----------|-------|
| `FLASK_ENV` | `production` |
| `DATABASE_URL` | Production CockroachDB connection string |
| `GEMINI_API_KEY` | Your Gemini API key |
| `SECRET_KEY` | Random 32+ character string |
| `FRONTEND_ORIGIN` | `https://www.intelliwheels.co,https://intelliwheels.co` |
| `BACKEND_URL` | `https://intelliwheels-backend-prod.onrender.com` |
| `CLOUDINARY_CLOUD_NAME` | Your Cloudinary cloud name (recommended) |
| `CLOUDINARY_API_KEY` | Your Cloudinary API key (recommended) |
| `CLOUDINARY_API_SECRET` | Your Cloudinary API secret (recommended) |

### `intelliwheels-backend-stg`

| Variable | Value |
|----------|-------|
| `FLASK_ENV` | `staging` |
| `DATABASE_URL` | Staging CockroachDB connection string |
| `GEMINI_API_KEY` | Your Gemini API key |
| `SECRET_KEY` | Random 32+ character string |
| `FRONTEND_ORIGIN` | `https://intelliwheels-git-stg-xxxxx.vercel.app` |
| `BACKEND_URL` | `https://intelliwheels-backend-stg.onrender.com` |

### `intelliwheels-backend-dev`

| Variable | Value |
|----------|-------|
| `FLASK_ENV` | `development` |
| `DATABASE_URL` | Dev CockroachDB connection string |
| `GEMINI_API_KEY` | Your Gemini API key |
| `SECRET_KEY` | Random 32+ character string |
| `FRONTEND_ORIGIN` | `https://intelliwheels-git-dev-xxxxx.vercel.app` |
| `BACKEND_URL` | `https://intelliwheels-backend-dev.onrender.com` |

---

## Database

**CockroachDB Serverless** (free 10 GiB tier) — create one database per environment:
1. Go to [cockroachlabs.cloud](https://cockroachlabs.cloud) → **Create Cluster** → **Serverless**
2. Create 3 clusters (or 1 cluster with 3 databases): `intelliwheels-prod`, `intelliwheels-stg`, `intelliwheels-dev`
3. Copy each connection string into the corresponding Render service's `DATABASE_URL`

---

## CI pipeline

The workflow in `.github/workflows/ci.yml` runs automatically on:
- **Push** to `production`, `stg`, or `dev`
- **PRs** targeting `production` or `stg`

It runs: `npm ci` → `npm run lint` → `npx tsc --noEmit` → `npm run build` (frontend) + `pip install` → `py_compile` (backend)

CI now runs frontend regression tests and isolated backend tests, including real FFmpeg validation. See `.github/workflows/ci.yml` for the current commands; hosted execution and branch enforcement still require verification.

---

## Workflow summary

1. Developers push to `dev` → Vercel preview + Render dev build automatically
2. Merge `dev` into `stg` → Muhannad tests on staging environment
3. Merge `stg` into `production` → live on intelliwheels.co
