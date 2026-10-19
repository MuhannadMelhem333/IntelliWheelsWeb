# Frontend Modernization Report

> September 7 correction: the completion wording below records the earlier implementation report, not release acceptance. Runtime information-route, local-data setup, logo and theme regressions were subsequently found. See [UI_PREVIEW_REPAIR.md](UI_PREVIEW_REPAIR.md) and [LOCAL_PREVIEW_STATUS.md](LOCAL_PREVIEW_STATUS.md). Production compilation now passes with permitted font access, but interactive parity and the complete visual redesign remain unverified. Do not treat Phase 1 as 100% validated.

## Final status

Phase 1 frontend architecture is implementation-complete. Every active screen has a real Next.js App Router boundary, shared public preferences and navigation are supplied by `PublicRouteShell`, and no source file imports the former 5,369-line `AppView` SPA. The unreachable compatibility component was removed after legacy page-key links were mapped to route paths.

## Route architecture

- `/` — public home
- `/listings` — URL-driven filters and pagination
- `/cars/[id]` — car detail
- `/dealers` and `/dealers/[id]` — dealer directory and detail
- `/about`, `/how-it-works`, `/pricing`, `/faq`, `/contact`, `/cookie-policy`, `/disclaimer` — information routes
- `/account`, `/favorites`, `/messages` — account and private user workflows
- `/my-listings`, `/my-listings/new`, `/my-listings/[id]/edit` — listing management
- `/assistant` — persistent, user-scoped AI assistant
- `/analytics` — authenticated market analytics
- `/admin` — verified-admin dealer application workflow

All data/auth route groups have loading and error boundaries. Internal navigation uses Next.js paths. `src/lib/publicRoutes.ts` supplies the temporary page-key-to-path compatibility map for detail return links and informational-page CTAs.

## Completed Phase 1 work

- Phase 1A: frontend baseline characterization.
- Phase 1B: all planned public, authenticated, listing-management, AI, analytics, and admin screens migrated to App Router routes.
- Phase 1C: shared shell responsibilities extracted; active routes use `PublicRouteShell`; the monolithic SPA was removed.
- Phase 1D: anonymous public caching is distinct from private `no-store` requests.
- Phase 1E: cached profiles are not trusted as verified sessions; private actions require server-validated auth.
- Phase 1F: persisted language/RTL, theme, currency, service mode, accessible mobile navigation, unread messages, metadata, sitemap, typed errors, and Next Image handling are implemented.

## Listings URL state

`src/lib/listingsSearchParams.ts` validates and serializes make, search, sort, category, condition, transmission, fuel type, and page. Default/empty values are removed, unrelated parameters are preserved, keys are sorted stably, filter changes clear pagination, and page-only changes do not refetch the listing dataset.

## Validation

- `npx tsc --noEmit`: PASS
- `npm run lint`: PASS with zero warnings
- `npm run build`: `BLOCKED BY ENVIRONMENT — not a confirmed code regression`. Turbopack reaches production compilation, then `next/font` cannot fetch Geist and Geist Mono from Google Fonts.
- `npm run dev`: PASS; Next.js reported ready on `http://localhost:3000`.
- Interactive browser automation: PENDING. The documented `agent-browser` executable is not installed in this environment.
- Automated unit tests: none added because this repository has no test framework. Pure URL-state behavior and route flows have documented manual checks.

## Known limitations

- Browser QA with a running backend and authenticated user/admin accounts remains required.
- The build environment must permit `fonts.googleapis.com`, or have fonts available through its build cache.
- Authentication still uses browser-accessible bearer-token storage. That is Phase 2B work.

## Rollback

Revert the Phase 1 route/component changes together, restore `src/components/AppView.tsx` and its former root entry, then revert navigation, preference, API typing/cache, and auth-startup changes. Do not selectively restore the old root without its page-key contracts.

STATUS: IMPLEMENTATION COMPLETE — MANUAL QA PENDING
