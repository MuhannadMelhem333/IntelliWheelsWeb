# Preview data and shared interface repair — 2026-09-07

## Scope and current status

### Follow-up: user reports only the logo is visible

Subsequent screenshot showed reset styles but no new layout rules. Confirmed the server sent development CSS with `Cache-Control: public, max-age=31536000, immutable`, from the custom `/_next/static/:path*` override in `next.config.ts`. Removed that override so Next.js controls development and production caching, then restarted the frontend. Existing browser-cached responses need a one-time hard refresh; a normal reload may continue using the old immutable asset. This is the identified delivery defect, distinct from the earlier defensive logo patch. Focused config ESLint and TypeScript pass. User-side visual confirmation after hard refresh remains required.

The earlier handoff did not establish visual correctness. On investigation, localhost:3000 returned the home heading and a 200 stylesheet containing `.iw-logo` width/height/overflow rules. No browser connection was available, so the user's observed rendering has not been reproduced or explained. `PublicHeader` now caps the logo directly with inline containment and 220px image dimensions instead of relying entirely on CSS to shrink a 1563px image. Focused ESLint and TypeScript pass. This is defensive containment, **not a confirmed resolution** of the reported page failure. Exact user URL and screenshot requested; other roadmap work paused pending diagnosis.

User-prioritized repair: visible local car inventory, light/dark logos, readable dark controls, and a more restrained automotive interface. Frontend roadmap continuation stays within shared-shell work; production, authentication architecture, schema, and API routes were not changed.

Implementation is available in the live development preview. **Interactive and visual QA is pending; this is not a claim that the entire website redesign or modernization roadmap is complete.**

## Confirmed data cause and correction

`backend/app/routes/cars.py:get_cars` reads the SQLite/PostgreSQL cars table; it does not load `backend/data/cars.json`. The local backend had been started with a new, empty `backend/intelliwheels.db`.

The user identified `backend/data/cars.json` as the intended source. `backend/import_local_cars.py:main` explicitly imports that file into the existing local SQLite file. It never reads remote configuration, refuses a nonempty table, assigns the numeric IDs required by `/api/cars/<int:id>`, retains the original source slugs in `source_sheets`, copies galleries, and leaves the JSON untouched. All inserts share a transaction and the connection is explicitly closed.

- Imported 6 cars, assigned local IDs 1–6.
- `GET /api/cars`: success, total 6.
- `GET /api/cars?make=Toyota`: success, total 2.
- `GET /api/cars/1`: success.
- A repeated import refused to alter existing rows.
- No dealers, seller accounts, review authors, or messages are present in the source. Importing it does not fabricate these relationships.
- The data file's third-party image URLs are retained. Their ongoing availability is not guaranteed.

## Shared interface and architecture

- `PublicRouteShell` remains the shared controller and context provider. It does not mount `AppView`.
- `PublicHeader` now owns logo and desktop/mobile navigation presentation. It receives typed state, links, preference controls, and callbacks; it has no independent auth or preference state.
- `AppFooter` is now used by the active shell, rather than left as an unused extraction. It contains informational Next.js links and the existing support email, telephone, location, and Instagram link.
- `useStoredPreference` uses `useSyncExternalStore` with deterministic server defaults for theme, language, and service mode. This avoids differing server/client initial markup from local-storage lazy initializers. Browser preferences restore after hydration; native storage events synchronize tabs and a local event synchronizes subscribers. Invalid values fall back, and storage-denied operation uses in-memory state.
- Language applies to document `lang`/`dir` and shell direction. Theme applies to document `data-theme`/`color-scheme` and shell tokens. Currency continues using `AuthContext`; its persistence architecture was not changed.
- A brief default light/English paint before preference restoration remains possible. No hydration suppression or font configuration workaround was added.
- `globals.css` introduces neutral light surfaces, charcoal dark surfaces, teal accents, explicit native input/select/textarea foreground/background pairs, visible keyboard focus, responsive navigation, and narrowly scoped compatibility rules for older slate/gray utility surfaces.
- Existing square logo assets are clipped with CSS to remove their transparent margins in the header. Light and dark variants are selected by theme; the source PNGs are unchanged.
- Home now has a search-led editorial layout, quieter vehicle cards, service links, and a selling CTA. Search submits to the existing listings URL contract. The homepage no longer couples car rendering to a statistics request; unavailable statistics cannot hide returned cars. Error, loading, and empty states are distinct. Promotional emoji tiles and gradient panels were removed.

The React review skill guided the typed presentation boundary and state review; the Next.js guidance informed keeping navigation route-based. Other route-specific designs and English-only legacy labels still need review; shared token changes are not a full per-page redesign.

## Files changed in this repair

- `src/app/globals.css`
- `src/components/public/PublicRouteShell.tsx`
- `src/components/public/PublicHeader.tsx`
- `src/components/public/useStoredPreference.ts`
- `src/components/layout/AppFooter.tsx`
- `src/components/home/PublicHomeView.tsx`
- `backend/import_local_cars.py`
- `backend/test_import_local_cars.py`
- This document, `docs/LOCAL_PREVIEW_STATUS.md`, `docs/PHASE_1C_APP_SHELL_EXTRACTION.md`, and `docs/FRONTEND_MODERNIZATION_REPORT.md`.
- Runtime-only local SQLite rows; source JSON unchanged. Existing unrelated Git changes preserved.

## Validation

- TypeScript: PASS after header extraction.
- Changed-component ESLint: PASS, zero warnings.
- Project ESLint: PASS after final header extraction, zero warnings.
- Production build: initially failed with `Failed to fetch Geist from Google Fonts` and `Failed to fetch Geist Mono from Google Fonts`. Retrying with approved network access passed, including static generation for 24 pages. The final build after header extraction also passed. Font configuration unchanged. Browserslist reports an old compatibility dataset; no dependency upgrade performed.
- `.venv/Scripts/python.exe backend/test_import_local_cars.py -v`: 4 PASS (source/gallery/ID preservation, duplicate refusal, rollback on malformed record, missing database refusal).
- Initial broad unittest discovery incorrectly imported Flask's app package, causing its existing Windows console encoding error. The focused test entrypoint avoids app initialization. Tests also found a new SQLite connection-lifetime issue on Windows; explicit connection closure fixed it before the passing rerun.
- HTTP 200: `/`, `/listings`, `/cars/1`, `/dealers`, `/account`, and both logo assets.
- Browser connection discovery returned no available browsers. HTTP responses and compilation do not prove hydration, fetched UI contents, appearance, or interactive behavior.
- `git diff --check`: PASS, with Git line-ending conversion notices. Worktree remains dirty with the prior migration and unrelated changes; no commit, reset, or revert was performed. Many Phase 1 files are still untracked and must be included deliberately when committing.

## Manual QA — all pending

| Check | Expected result |
| --- | --- |
| Home and listings | Home displays up to four imported cars; unfiltered listings displays six, not a zero/error state. |
| Car navigation | A card opens its numeric `/cars/[id]`; refresh and Back work. |
| Search | Submit Toyota on home; listings URL contains `search=Toyota` and shows the two Toyota records. |
| Light logo | Teal/dark wordmark is visible, correctly sized and not cropped at its edges. |
| Dark logo | Theme switch selects teal/white wordmark, with no duplicate header. |
| Dark inputs | Search, account forms, listing editor, review/contact fields and dropdown options have legible text, placeholder, focus and disabled states. |
| Theme persistence | Change theme, refresh and navigate between routes; the preference restores without hydration errors. |
| Arabic | Switch language; shared copy and home change language, document and layout become RTL without overflow. |
| Currency | Change currency; car prices and header selection stay consistent after navigation and refresh. |
| Desktop navigation | Active route indicator, sign-in/account, seller CTA and service-mode links work by keyboard and pointer. |
| Mobile navigation | At 375px and 768px, open/close menu; links and all preference controls remain reachable, without horizontal overflow. |
| Authenticated navigation | Favorites, messages/unread count, my listings and existing gated actions remain available after login. |
| Footer | Information links, support email/phone and Instagram work; Arabic labels are readable. |
| Data failure | Stop API temporarily: error is distinct from empty inventory; restart and reload restores cars. |
| Console/network | No hydration errors or repeated requests/navigation caused by preference synchronization. |
| Image availability | Imported third-party photographs load; report broken remote images separately from missing database records. |

## Rollback and next work

Undo only the repair hunks/files listed above, preserving all pre-existing route migrations and unrelated worktree changes. Restore the previous footer contract together with its shell call site. Do not use a repository-wide reset or checkout. The import script is not automatic; removing it does not delete imported records. Keep the local database or back it up before any requested data rollback; never delete a database that has acquired new user work.

Next coherent work: browser-led review of shared controls and listings/detail surfaces, followed by correcting remaining page-specific contrast, localization, and navigation regressions. Do not classify Phase 1 as fully verified before this comparison.
