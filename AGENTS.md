# IntelliWheels — Agent Guide

## Monorepo structure
- **Root** = Next.js 16 frontend (App Router, React 19.2, Tailwind CSS 3.4, TypeScript 5)
- **`backend/`** = Flask 3.0 Python API (SQLite dev / PostgreSQL prod)
- Single-page app: `src/app/page.tsx` → `<AuthProvider><AppView /></AuthProvider>`
- `AppView.tsx` (~5300 lines) is the main shell handling all UI
- `@/*` path alias maps to `./src/*`

## Commands
```
npm run dev          # Frontend dev server on :3000
npm run build        # Production build
npm run lint         # ESLint (flat config in eslint.config.mjs)
npx tsc --noEmit     # Typecheck (not in package.json scripts, but CI requires it)

cd backend
python run.py        # Flask dev server on :5000 (debug mode, loads .env)
```

### CI pipeline (`ci.yml`) — run in this order before committing:
1. Frontend: `npm ci` → `npm run lint` → `npx tsc --noEmit` → `npm run build`
2. Backend: `pip install -r backend/requirements.txt` → `python -m py_compile backend/run.py backend/app/__init__.py backend/app/db.py`

**No test framework exists** (no Jest, pytest, or Vitest).

## Key env vars
| Var | Notes |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | Frontend → backend URL. Falls back through several names, ultimate default `http://localhost:5000/api` |
| `GEMINI_API_KEY` | Required for AI features (chatbot, vision, pricing) |
| `SECRET_KEY` | Must be 32+ chars in production; app crashes on startup if missing/invalid in prod |
| `DATABASE_URL` | PostgreSQL in prod; SQLite default for local dev |
| `FRONTEND_ORIGIN` | CORS allowlist (comma-separated). In dev, CORS is open. |
| `CLOUDINARY_*` | Optional; without it, uploads are ephemeral (lost on Render redeploy) |

Sentry DSN is hardcoded in `sentry.client.config.ts` — only enabled in production.

## Branching & deployment workflow

### Git flow
```
dev ──► stg ──► production
```
All changes go to `dev` first. Muhannad Melhem tests on `stg`. Once approved, merge to `production`.

### Vercel (frontend)
One Vercel project with 3 environments — set the Production branch to `production`, then add `stg` and `dev` as preview branches. Each gets its own URL and env vars. `NEXT_PUBLIC_API_URL` must point to the matching Render backend.

### Render (backend)
3 services defined in `render.yaml`, each deploys from a different branch (`production`, `stg`, `dev`). Set `DATABASE_URL`, `GEMINI_API_KEY`, `SECRET_KEY`, `FRONTEND_ORIGIN`, and `BACKEND_URL` per service in the Render dashboard.

### CI
Runs lint → typecheck → build on push to any of the 3 branches and on PRs targeting `production` or `stg`.

## Architecture notes
- **API base URL normalization** (`src/lib/config.ts`): strips trailing slash, appends `/api` if missing
- Backend uses Flask blueprints: 9 route modules in `backend/app/routes/`
- CORS restricted to `FRONTEND_ORIGIN` origins in production, fully open in dev
- React Compiler enabled (`reactCompiler: true` in `next.config.ts`)
- Bilingual (English/Arabic) with RTL support — check `dir` and `lang` on `<html>`
- Multi-currency rates defined in `src/lib/config.ts` (10 currencies, rates relative to JOD)
- GA4 tracking ID `G-T959BS302R` in root layout
- Images: Cloudinary remote hostname whitelisted in `next.config.ts`; local image fallback in `public/`
- Uploads: max 500MB via Flask (`MAX_CONTENT_LENGTH`)
