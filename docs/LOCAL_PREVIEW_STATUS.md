# Local preview — 2026-09-07

## Latest update

The user identified `backend/data/cars.json` as the intended local inventory. Six cars have now been imported into the preview SQLite database; the source JSON is unchanged. The API returns six cars, two for the Toyota filter, and a valid detail for ID 1. This supersedes the empty-database notes below, which describe initial startup.

Shared navigation, theme-aware logos, native field contrast, and the home design have been updated. See [UI_PREVIEW_REPAIR.md](UI_PREVIEW_REPAIR.md) for changed files, tests, pending visual QA and rollback. Production build passed after an approved network-enabled retry; no font configuration changes were required. No secret supplied in chat was saved or used.

## Initial startup record

Frontend: http://localhost:3000
Backend: http://localhost:5000/api/health

Both development servers were started and left running with automatic reload. The frontend uses `NEXT_PUBLIC_API_BASE_URL=http://localhost:5000/api` for this process. The backend uses local `backend/intelliwheels.db`, with remote database configuration overridden only in the launched process. The newly created SQLite database is empty. Register a local account and add listings to exercise authenticated flows. No demo records or accounts were inserted.

Python dependencies are installed from `backend/requirements.txt` in the ignored root `.venv`. The backend reports no valid Gemini API key, so AI provider calls remain unavailable until local configuration supplies one.

## Validation and corrections

- Home, listings, dealers, account, assistant, and all seven information routes returned HTTP 200.
- Backend health, cars, and dealers endpoints responded; cars/dealers reported success and the local listing count was zero.
- Fixed the information routes' HTTP 500 by moving their slug constants out of a Client Component into `src/lib/infoPages.ts`.
- Added a narrow Git ignore exception for `src/lib/` so the URL-state and navigation helpers are visible to Git.
- Excluded `**/.venv/**` from ESLint after the new Python environment caused it to scan bundled dependency JavaScript.
- TypeScript and project ESLint passed after these corrections.
- HTTP checks do not verify client hydration or interactions. Browser discovery returned no connected browsers; interactive QA remains pending.
- Development uses Next's font fallback when Google Fonts is unreachable. Font configuration was not changed.

The earlier completion report described implementation progress too broadly: the runtime fault above passed TypeScript and ESLint. Complete the manual behavior comparison before treating the frontend as release-ready.

Rollback of this session's code correction: move the slug constants back into `InfoPageRoute.tsx` and restore its route import (this restores the observed fault). Keep the Git exception if the new helpers are to be committed. Stopping the servers does not remove the local SQLite data or virtual environment.
